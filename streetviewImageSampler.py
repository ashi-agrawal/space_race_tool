# TODO: Finish header comment.
'''
Google Street View Image Sampler
November 2018
Ashi Agrawal
'''

import argparse
import json
import os
import random
import requests
import shapefile
import shutil

from shapely.geometry import shape, Point

# Google Street View Image API
# 25,000 image requests per 24 hours
# See https://developers.google.com/maps/documentation/streetview/
with open('keys.json') as json_data:
    data = json.load(json_data)
    API_KEY = data['api_key']
GOOGLE_URL = "http://maps.googleapis.com/maps/api/streetview?size=640x640&key=" + API_KEY

DIR_NAME = "StreetView_Images"
IMG_PREFIX = "IMG_"
IMG_SUFFIX = ".jpg"

'''
@fn: get_arguments()
@description: Prompts user for the following arguments: shapefile (file path to shapefile), number of images wanted (optional), seed for random function (optional), directory to store images in (optional).
@args: None
@return: Namespace of user-provided arguments.
'''
def get_arguments():
    # TODO (Stretch): Allow users to customize the size of their images. Use parameters dict instead of curr manual creation of url.
    # TODO (Stretch): Add more error checking of arguments.
    parser = argparse.ArgumentParser(
        description="Download random StreetView images within a given shape.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument(
        'shapefile', nargs=1, help="File path to shapefile.")
    parser.add_argument(
        '-n', type=int, default=10, help="Number of images wanted.")
    parser.add_argument(
        '-s', type=int, help="Initial seed for randomization of image location.")
    parser.add_argument(
        '-d', help="Directory to store the images in.")
    args = parser.parse_args()
    return args

# TODO: Comment.
# TODO: Add better error-checking here.
def parse_shapefile(file_path):
    sf = shapefile.Reader(file_path)
    shapes = sf.shapes()
    # TODO: Confirm expected functionality here.
    '''
    if len(shapes) != 1:
        raise RuntimeError("Expect one shape per file.")
    '''
    return shapes[0]

# TODO: Comment.
def print_log_file(points):
    with open(os.path.join(DIR_NAME, 'log_file.txt'), 'w') as f:
        for item in points:
            # TODO: Format this correctly.
            f.write("%s\n" % item)
    print("Log file written.")

if __name__ == '__main__':
    args = get_arguments()
    given_shape = parse_shapefile(args.shapefile[0])
    bounds = given_shape.bbox
    print(bounds)
    polygon = shape(given_shape)
    points = []
    random.seed(args.s)
    # TODO: What's a cleaner way to do this?
    if args.d:
        new_dir = os.path.join(args.d, DIR_NAME)
    else:
        new_dir = DIR_NAME
    if os.path.exists(new_dir):
        raise RuntimeError("Directory already exists. Please specify a new directory.")
    os.makedirs(new_dir)
    # TODO: Decompose.
    for i in range(args.n):
        point = Point(200, 200)
        while(not polygon.contains(point) or point in points):
            # TODO: Confirm that this ordering is correct.
            lon = random.uniform(bounds[0], bounds[2])
            lat = random.uniform(bounds[1], bounds[3])
            point = Point(lon, lat)
        # TODO: Figure out appropriate conversion from coords to lat/lon.
        points.append(point)
        url = GOOGLE_URL + "&location=" + str(point.x) + "," + str(point.y)
        r = requests.get(url, stream=True)
        # TODO: Fix syntax.
        '''
        if r.status_code not 200:
            raise RuntimeError("Failed to retrieve image " + str(i) + ".")
        '''
        save_location = os.path.join(new_dir, IMG_PREFIX + str(i) + IMG_SUFFIX)
        with open(save_location, 'wb') as f:
            r.raw.decode_content = True
            shutil.copyfileobj(r.raw, f)
        print("Image " + str(i) + " saved.")
    print_log_file(points)
