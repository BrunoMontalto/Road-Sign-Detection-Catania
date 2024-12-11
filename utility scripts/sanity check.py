# sanity check

import os
import xml.etree.ElementTree as ET

images = os.listdir("images")
annotations = os.listdir("annotations")

N = 3176 # greater id

tree = ET.parse("coordinates.xml")
root = tree.getroot()

print("looking for missing files")
for i in range(N + 1):
    # check if both images/i.png and annotations/i.xml exist

    png_missing = not str(i) + ".png" in images
    xml_missing = not str(i) + ".xml" in annotations

    if png_missing and not xml_missing:
        print("png missing:", i)
    
    if xml_missing and not png_missing:
        print("xml missing:", i)

    if not png_missing and not xml_missing:
        # check if tree.xml has an entry with id i
        entry_missing = True
        for entry in root.findall(".//entry"):
            if entry.get("id") == str(i):
                entry_missing = False
                break
        if entry_missing:
            print("coordinates missing for:", i)


input("done")

print("looking for xml files without annotations")
# look for xml file with no object nodes

for annotation in annotations:
    with open("annotations/" + annotation) as file:
        content = file.read()
        if "<object>" not in content:
            print("no object nodes:", annotation)


input("done")
quit()
