import csv
import sys

FT_PER_METER = 3.2808399
reader = csv.reader(sys.stdin)
output = []
for row in reader:
    output.append([row[0], row[1], row[2], float(row[3])/FT_PER_METER, row[4]])

writer = csv.writer(sys.stdout)
writer.writerows(output)


