#!/usr/bin/env python3

# Tool to translate "csv" files output by SW Maps (android gps mapping app) to a
# PNEZD-style lat/long format, which can be used by tools like Civil3D.

# input (sw maps point file) format:
# ID,Geometry,Remarks,
# 6,POINT Z (-119.83559303 52.37266082 1519.457),rebar cone top,
# 7,POINT Z (-119.83556155 52.37272424 1519.674),pt,

# 2023 Aug: Format has changed:
# 54,08/25/2023 12:43:39.500 PDT,pto,POINT Z (-112.83461149 39.57328935 1510.741),39.573289348,-119.834611492,1510.741,1534.672,2.050,4,0.001,0.0,0.010,0.010

# Geometry field looks like the 3-tuple E,N,Z(in meters),D

# output format: (ref: https://www.eyascopublic.com/mehelp/index.html#!Documents/surveypnezdfileformat.htm)
# P,N,E,Z,D,PROJECT1,2020-07-21 12:00
# 8,2871835.803,6235770.127,112.214,FND
# The single header line contains the column identifiers for the data as well as
# the project tag and event date. 
# 1)  P – Point indicator
# 2)  N – Northing / Latitude
# 3)  E – Easting / Lon.
# 4)  Z – Elevation
# 5)  D – Description
# 6)  PROJECT1 – this is the project name value for the entire file
# 7)  Date – this is the event date for the data in the file and should be in international format (yyyy-mm-dd hh:nn:ss)

import argparse
import datetime
import re
import sys
from typing import NamedTuple

METER_PER_US_SURVEY_FT = 0.30480061
METER_PER_FT = 0.3048

# Not official version, just increment when it changes
FORMAT_VER = 2

class PointPNEZD (NamedTuple):
    point: int
    northing: float
    easting: float
    elevation_m: float
    description: str

class PNEZDFile:
    @classmethod
    def print_header(cls, project_name: str) -> None:
        timestamp = datetime.datetime.now().isoformat()
        print(f"#P,N,E,Z,D,{project_name},{timestamp}")

    @classmethod
    def print_line(cls, p: PointPNEZD, convert_to_feet:bool=False) -> None:
        elevation = p.elevation_m
        if convert_to_feet:
            elevation = elevation / METER_PER_US_SURVEY_FT
        print(f"{p.point},{p.northing},{p.easting},{elevation},{p.description}")

    @classmethod
    def print_file(cls, points: list[PointPNEZD], project_name:str="PROJECT1") -> None:
        cls.print_header(project_name)
        for p in points:
            cls.print_line(p)

class SWMaps:
    def __init__(self):
        self.verbose = False
        self.header_re = re.compile("ID,Geometry,Remarks,")
        # matches are P,E,N,Z,D
        if FORMAT_VER == 1:
            cols_pattern = "(.*),POINT Z \\((.*) (.*) (.*)\\),(.*)[,]?"
        else :
            f = "[^,]*"
# 54,08/25/2023 12:43:39.500 PDT,pto,POINT Z (-112.83461149 39.57328935 1510.741),39.573289348,-119.834611492,1510.741,1534.672,2.050,4,0.001,0.0,0.010,0.010
            cols_pattern = f"([0-9]+),{f},({f}),POINT Z \\(({f}) ({f}) ({f})\\),{f},{f},{f},({f})" + f",{f}" * 5
        self.line_re = re.compile(cols_pattern)
    
    def vprint(self, *args:str, **kwargs:str):
        if self.verbose:
            print(*args, **kwargs, file=sys.stderr)
        
    def parse_points_csv(self, point_offset:int=0) -> list[PointPNEZD]:
        found_header = False
        points: list[PointPNEZD] = []
        for l in sys.stdin:
            if not found_header and self.header_re.match(l):
                found_header = True
                continue
            m = self.line_re.match(l)
            if not m:
                self.vprint("Ignoring unexpected line: " + l)
            else:
                point_id = int(m.group(1)) + point_offset
                if FORMAT_VER == 1:
                    # older format
                    easting = float(m.group(2))
                    northing = float(m.group(3))
                    z_m = float(m.group(4))
                    descr = m.group(5)
                else:
                    descr = m.group(2)
                    easting = float(m.group(3))
                    northing = float(m.group(4))
                    # this is ellipsoidal, we want orthometric: float(m.group(5))
                    z_m = float(m.group(6))

                points.append(PointPNEZD(point_id, northing, easting, z_m, descr))
        self.vprint(f"Parsed {len(points)} point records.")
        return points


def main():
    parser = argparse.ArgumentParser(
                    description = 'Convert SW Maps point files to PNEZD format',
                    epilog= 'Reads from stdin, writes to stdout.')
    parser.add_argument("--verbose", help="Print verbose output to stderr", action='store_true')
    parser.add_argument("--meter-to-ft", help="Translate elevations from meters to feet", action='store_true')
    parser.add_argument("--renumber", help="Add value to point numbers.", action='store', default=0)
    args = parser.parse_args()

    reader = SWMaps()
    if args.verbose:
        reader.verbose = True
    
    points = reader.parse_points_csv(int(args.renumber))
    PNEZDFile.print_header("PROJECT_NAME")
    for p in points:
        PNEZDFile.print_line(p, convert_to_feet=args.meter_to_ft)


if __name__ == "__main__":
    main()
