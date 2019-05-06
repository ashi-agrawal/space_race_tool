"""
Google Street View Image Sampler
November 2018
Ashi Agrawal

This tool allows a user to specify a shape and creates a folder with randomly selected Google Maps images from the given area.

Example Call:
python streetviewImageSampler.py shapefile -n 20 -s 5 -d directory
"""

import argparse
import datetime
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
with open("keys.json") as json_data:
    data = json.load(json_data)
    API_KEY = data["api_key"]

GOOGLE_METADATA_URL = (
    "https://maps.googleapis.com/maps/api/streetview/metadata?key=" + API_KEY
)
GOOGLE_URL = (
    "http://maps.googleapis.com/maps/api/streetview?size=640x400&key=" + API_KEY
)

DIR_NAME = "StreetView_Images_" + datetime.datetime.now().strftime("%m.%d.%Y%H%M%S")
IMG_PREFIX = "IMG_"
IMG_SUFFIX = ".jpg"

def get_arguments():
    """ Retrieve and parse user arguments.
    description: Prompts user for the following arguments: shapefile (file path to shapefile), number of images wanted (optional, assumed to be 10), seed for random function (optional), directory to store images in (optional).
    @return: Namespace of user-provided arguments.
    """
    # TODO (Stretch): Allow users to customize the size of their images. Use parameters dict instead of curr manual creation of url.
    parser = argparse.ArgumentParser(
        description="Download random StreetView images within a given shape.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("shapefile", nargs=1, help="File path to shapefile.")
    parser.add_argument("-n", type=int, default=10, help="Number of images wanted per shape.")
    parser.add_argument(
        "-s", type=int, help="Initial seed for randomization of image location."
    )
    parser.add_argument("-d", help="Directory to store the images in.")
    args = parser.parse_args()
    return args

def add_parameter(url, param_name, param_value):
    """ Add parameter to URL.
    description: Given a partially constructed URL in string format, adds a parameter to the end.
    @url: String representation of URL.
    @param_name: Name of parameter to add.
    @param_value: Value of parameter to add.
    @return: String URL with parameter.
    """
    if url[:-1] != "&":
        url += "&"
    url = url + param_name + "=" + param_value
    return url

def parse_shapefile(file_path):
    """ Return shape information from shapefile.
    description: Given a file path leading to a shapefile, opens the shapefile and returns information on all shapes in the file.
    @file_path: File path to shapefile containing shape.
    @return: Array of tuples of Shapely shape and bounding box.
    """
    sf = shapefile.Reader(file_path)
    shapes = sf.shapes()
    shapes_array = []
    for item in shapes:
        shapes_array.append((shape(item), item.bbox))
    return shapes_array

def check_image(point):
    """ Determine if there is an image at a given point.
    description: Query's Google Street View's Metadata endpoint to determine if there is an image at the given point. 
    @point: Shapely point consisting of an x, y coordinate pair.
    @return: Boolean.
    """
    metadata_url = add_parameter(
        GOOGLE_METADATA_URL, "location", str(point.y) + "," + str(point.x)
    )
    r = requests.get(metadata_url, stream=True)
    json = r.json()
    if json["status"] == "OK":
        return True
    elif json["status"] == "ZERO_RESULTS":
        return False
    else:
        raise RuntimeError("Failed to retrieve image metadata.")

def pick_points(polygon, bounds, number):
    """ Randomly pick points contained within polygon.
    description: Using a uniform distribution, randomly and evenly pick points from within the polygon. If the polygon is shaped oddly, it may take a while to run as the bounding box may be much larger than the polygon. For most shapes, however, this should be relatively quick.
    @polygon: Shapely shape object representing a shape.
    @bounds: Bounding box around polygon.
    @number: Number of coordinates to find.
    @return: Array of x,y coordinates.
    """
    points = []
    tried = []
    while len(points) < number:
        lon = random.uniform(bounds[0], bounds[2])
        lat = random.uniform(bounds[1], bounds[3])
        point = Point(lon, lat)
        valid = (
            polygon.contains(point) and point not in tried and check_image(point)
        )
        if valid:
            points.append(point)
        tried.append(point)
    return points

def print_log_file(dir_name, points):
    """ Write and format point information to log file.
    description: Given of array of points as input, writes to a text file in the same folder as images, detailing each image's latitude and longitude.
    @dir_name: Directory to store log file in.
    @points: Array of points (consisting of x and y coordinates), representing latitude/longitude, to log.
    @return: None.
    """
    with open(os.path.join(dir_name, "log_file.txt"), "w") as f:
        line_format = "{}, {}, {}\n"
        f.write(line_format.format("item", "latitude", "longitude"))
        for idx, item in enumerate(points):
            item_identifier = IMG_PREFIX + str(idx) + IMG_SUFFIX
            f.write(line_format.format(item_identifier, str(item.y), str(item.x)))
    print("Log file written.")


if __name__ == "__main__":
    args = get_arguments()
    random.seed(args.s)
    if args.d is None:
        args.d = ""
    shapes = parse_shapefile(args.shapefile[0])
    for shape_idx, item in enumerate(shapes):
        new_dir = os.path.join(args.d, DIR_NAME, str(shape_idx))
        os.makedirs(new_dir)
        polygon, bounds = item
        points = pick_points(polygon, bounds, args.n)
        for idx, point in enumerate(points):
            url = add_parameter(GOOGLE_URL, "location", str(point.y) + "," + str(point.x))
            r = requests.get(url, stream=True)
            if r.status_code != 200:
                raise RuntimeError("Failed to retrieve image " + str(idx) + ".")
            save_location = os.path.join(new_dir, IMG_PREFIX + str(idx) + "_" + str(shape_idx) + IMG_SUFFIX)
            with open(save_location, "wb") as f:
                r.raw.decode_content = True
                shutil.copyfileobj(r.raw, f)
            print("Image " + str(shape_idx) + "_" + str(idx) + " saved.")
        print_log_file(new_dir, points)
