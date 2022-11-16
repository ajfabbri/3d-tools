#!/usr/bin/env python3

# Tool to translate "csv" files output by SW Maps (android gps mapping app) to a
# proper PNEZD format, which can be used by tools like Civil3D.

# input (sw maps point file) format:
# ID,Geometry,Remarks,
# 6,POINT Z (-129.83559303 52.37266082 1519.457),rebar cone top,
# 7,POINT Z (-129.83556155 52.37272424 1519.674),pt,
# Geometry field looks like the 3-tuple E,N,Z(in meters),D

# output format: (ref: https://www.eyascopublic.com/mehelp/index.html#!Documents/surveypnezdfileformat.htm)
# P,N,E,Z,D,PROJECT1,2020-07-21 12:00
# 8,2871835.803,6235770.127,112.214,FND
# 200,880332.631,6241504.876,314.337,MON

# The single header line contains the column identifiers for the data as well as
# the project tag and event date.  The PNEZD column indicators can be in any
# order but must reflect the order of the data in each line.  They must be
# followed by the project name and finally the event date of data.

# 1)  P – Point indicator
# 2)  N – Northing value
# 3)  E – Easting value
# 4)  Z – Elevation value
# 5)  D – Description value
# 6)  PROJECT1 – this is the project name value for the entire file
# 7)  Date – this is the event date for the data in the file and should be in international format (yyyy-mm-dd hh:nn:ss)

import argparse
import datetime
import re
import sys
from typing import NamedTuple


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
        print(f"P,N,E,Z,D,{project_name},{timestamp}")

    @classmethod
    def print_line(cls, p: PointPNEZD) -> None:
        print(f"{p.point},{p.northing},{p.easting},{p.elevation_m},{p.description}")

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
        cols_pattern = "(.*),POINT Z \\((.*) (.*) (.*)\\),(.*),"
        self.line_re = re.compile(cols_pattern)
    
    def vprint(self, *args:str, **kwargs:str):
        if self.verbose:
            print(*args, **kwargs, file=sys.stderr)
        
    def parse_points_csv(self) -> list[PointPNEZD]:
        found_header = False
        points: list[PointPNEZD] = []
        for l in sys.stdin:
            if not found_header and self.header_re.match(l):
                found_header = True
            if found_header:
                m = self.line_re.match(l)
                if not m:
                    self.vprint("Ignoring unexpected line: " + l)
                else:
                    point_id = int(m.group(1))
                    easting = float(m.group(2))
                    northing = float(m.group(3))
                    z_m = float(m.group(4))
                    descr = m.group(5)
                    points.append(PointPNEZD(point_id, northing, easting, z_m, descr))
        self.vprint(f"Parsed {len(points)} point records.")
        return points


def main():
    parser = argparse.ArgumentParser(
                    description = 'Convert SW Maps point files to PNEZD format',
                    epilog= 'Reads from stdin, writes to stdout.')
    parser.add_argument("--verbose", help="Print verbose output to stderr", action='store_true')
    args = parser.parse_args()

    reader = SWMaps()
    if args.verbose:
        reader.verbose = True
    
    points = reader.parse_points_csv()
    PNEZDFile.print_file(points)


if __name__ == "__main__":
    main()