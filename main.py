#!/usr/bin/python

import os
import sys
import argparse
import gpxpy
import gpxpy.gpx
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
import pytz
from pytz import timezone

TOOLS = 'mapillary_tools' #mapillary tools command (modify with path, version etc. if neeeded)

# Moves videos to folder structure such that they can be processed with mapillary_tools command. A subdirectory per camera (front, back etc.)
def move_to_camera_dir(basepath,camera):
  path = os.path.join(basepath,camera)
  if not os.path.isdir(path):
    os.mkdir(path)

  for filename in os.listdir(basepath):
    if filename.endswith(camera + ".mp4"):
      targetpath = os.path.join(basepath,camera,rchop(filename,"-" + camera + ".mp4"))
      if not os.path.isdir(targetpath):
        os.mkdir(targetpath)
        os.rename(os.path.join(basepath,filename), os.path.join(targetpath,filename))

# Processes videos in a particular directory
def process_camera_dir(basepath,camera,gpx_file,mapillary_username, localtz):
  angle = 0
  if camera == "back":
    angle = 180
  elif camera == "left_repeater":
    angle = -90
  elif camera == "right_repeater":
    angle = 90

  subfolders = [ f.path for f in os.scandir(os.path.join(basepath,camera)) if f.is_dir() ]

  for path in subfolders:
    for filename in os.listdir(path):
      if filename.endswith(camera + ".mp4"):
        tesla_datetime = datetime.strptime(filename[0:19], "%Y-%m-%d_%H-%M-%S") #Pattern: 2020-09-24_14-06-34-front.mp4
        tesla_datetime = localtz.localize(tesla_datetime).astimezone(pytz.utc)
        subprocess.run([TOOLS, "video_process", path, "--video_sample_interval", "0.5", "--video_start_time", tesla_datetime.strftime('%Y_%m_%d_%H_%M_%S_%f'), "--geotag_source", "gpx", "--geotag_source_path", gpx_file, "--overwrite_all_EXIF_tags", "--offset_angle", str(angle), "--device_make", "Tesla", "--video_sample_distance",  "-1"])
        

def rchop(s, suffix):
  if suffix and s.endswith(suffix):
    return s[:-len(suffix)]
  return s


if __name__ == "__main__":

  my_parser = argparse.ArgumentParser(description='Process Tesla dashcam videos with accompanying GPX file')
  my_parser.add_argument('videopath', metavar='videopath', type=str, help='The videopath to list')
  my_parser.add_argument('gpxfilepath',metavar='gpxpath', type=str, help='The gpx file')
  my_parser.add_argument('mapillary_user', metavar='mapillary_user', type=str, help='Mapillary username')
  my_parser.add_argument('timezone', metavar='timezone', type=str, default="Europe/Zurich", help='Timezone the Tesla ride was in. Default: Europe/Zurich')

  args = my_parser.parse_args()

  video_dir = args.videopath
  gpxpath = args.gpxfilepath
  mapillary_user = args.mapillary_user
  localtz = timezone(args.timezone)

  if not os.path.isdir(video_dir):
    print('The path specified does not exist')
    sys.exit()

  gpx_file = open(gpxpath, 'r')
  gpx = gpxpy.parse(gpx_file)

  cameras = ["front", "back", "left_repeater", "right_repeater"]

  for camera in cameras:
    print("Processing camera: **** " + camera + " ****")
    print("-- moving source files ---")
    move_to_camera_dir(video_dir,camera)
    print("-- Processing and uploading videos ---")
    process_camera_dir(video_dir,camera,gpxpath,mapillary_user, localtz)
