# delete coordinates of images that were deleted from coordinates.xml

import os
import shutil
import xml.etree.ElementTree as ET


images = os.listdir("images")

N = 3176 # greater id

tree = ET.parse("coordinates.xml")
root = tree.getroot()




# count duplicate ids
ids = []
duplicates = []
for entry in root.findall(".//entry"):
    id = entry.get("id")
    if id in ids:
        duplicates.append(id)
    ids.append(id)
print("duplicates({}):".format(len(duplicates)), duplicates)


# count number of entries in coordinates.xml
count = 0
for entry in root.findall(".//entry"):
    count += 1
print("number of entries in coordinates.xml:", count)