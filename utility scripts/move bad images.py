import os
import shutil

# list of ids to be moved
ids = input("Enter the ids of the images to be moved, separated by a space: ").split()

# move the images and the xml files. (some images may not have a xml file associated)
for id in ids:
    if os.path.exists("images/"+id+".png"):
        shutil.move("images/"+id+".png", "images to delete/"+id+".png")
    if os.path.exists("annotations/"+id+".xml"):
        shutil.move("annotations/"+id+".xml", "annotations to delete/"+id+".xml")

    print(id, "moved")

input("done")