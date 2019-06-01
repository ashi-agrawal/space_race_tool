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
import dbf
import json
import os
import pandas as pd
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
    parser.add_argument("-i", help="File path to .csv containing indices of shapes to use.")
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

def parse_shapefile(file_path, csv_file):
    """ Return shape information from shapefile.
    description: Given a file path leading to a shapefile, opens the shapefile and returns information on the shapes corresponding to the csv indices.
    @file_path: File path to shapefile containing shape.
    @csv_file: File path to a csv with two columns: index and include. This method will select only the indices where there is a 1 in the include column. If file path is None, will select all indices.
    @return: Array of tuples of index, Shapely shape, and bounding box.
    """
    sf = shapefile.Reader(file_path)
    shapes = sf.shapes()
    if csv_file is None:
        indices = list(range(len(shapes)))
    else:
        df = pd.read_csv(csv_file)
        indices = list(df.loc[(df['include'] == 1), 'index'])
    shapes_array = []
    for idx in indices:
        item = shapes[idx]
        shapes_array.append((idx, shape(item), item.bbox))
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
            item_identifier = IMG_PREFIX + str(idx)+ "_" + str(shape_idx) + IMG_SUFFIX
            f.write(line_format.format(item_identifier, str(item.y), str(item.x)))
    print("Log file written.")

def print_dbf_file(filename, results_dir):
    """ Write information from dbf file to .csv.
    description: Given a path from the user to a shapefile, reads the corresponding .dbf file and writes the information to a .csv.
    @filename: User-given shapefile given.
    @results_dir: High-level directory storing all results of run.
    @return: None.
    """
    dbf_file = os.path.splitext(filename)[0] + ".dbf"
    table = dbf.Table(dbf_file)
    table.open()
    output_file = os.path.join(results_dir, "dbf_info.csv")
    dbf.export(table, filename=output_file)
    print("DBF information written.")

if __name__ == "__main__":
    args = get_arguments()
    random.seed(args.s)
    if args.d is None:
        args.d = ""
    shapes = parse_shapefile(args.shapefile[0], args.i)
    results_dir = os.path.join(args.d, DIR_NAME)
    for shape_idx, polygon, bounds in shapes:
        new_dir = os.path.join(results_dir, str(shape_idx))
        os.makedirs(new_dir)
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
    print_dbf_file(args.shapefile[0], results_dir)
