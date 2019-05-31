# Google Maps Space Tool

## Motivation

The Mind, Culture, and Society Lab at Stanford is interested in exploring the link between space and race. To conduct this research, it is necessary to be able to generate images of particular areas or regions relatively quickly and programmatically. Therefore, this tool was created to query the Google Maps API for random images within a specified area.

## Usage

### Pre-Conditions

To use the tool, you will need a shapefile outlining the shape that you would like to select images from. This shapefile needs to fit a couple of requirements:

* (a) it should contain at least one shape to sample from
* (b) it should use EPSG 4326 (to work with the Google Maps database). You can use an online tool or the epsj-indent tool from the command-line to reproject the shapefile if necessary.
* (c) the shape should be of type POLYGON. POINT and POLYLINE objects cannot be queried for random images.

### Sample Usage

For this exercise, we will download a map from online, [Map of Stanford](https://earthworks.stanford.edu/catalog/stanford-xp345tc6626). Make sure to use "Export Formats" -> "EPSG:4326 Shapefile" on the right side for the right projection.

Navigate to the folder containing this tool. Make sure that you have a Google Street View API key and, using the format outlined in keys.sample.json, store this key in a file called keys.json. Then, to retrieve images using the tool, the command is python streetviewImageSampler.py path/to/stanford/xp345tc6626.prj. This should populate a folder with 10 images. There are also four different flags that you can use to change the behavior of the tool: "-n" to change the number of images from 10, "-s" to change the seed for random (if you want to replicate results across runs), "-d" to change the directory for storing images, and "-i" to specify which shape indices to include.. For instance, to pull 20 images with seed 5 in directory "directory" from shapes 0 and 2, this would be the appropriate command: python streetviewImageSampler.py path/to/stanford/xp345tc6626.prj -n 20 -s 5 -d "directory" -i sample.csv.
