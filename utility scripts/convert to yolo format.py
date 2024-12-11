quit() # for safety
import os
import xml.etree.ElementTree as ET
import cv2
import numpy as np

def convert(size, box):
    dw = 1./size[0]
    dh = 1./size[1]
    x = (box[0] + box[1])/2.0
    y = (box[2] + box[3])/2.0
    w = box[1] - box[0]
    h = box[3] - box[2]
    x = x*dw
    w = w*dw
    y = y*dh
    h = h*dh
    return (x,y,w,h)

def convert_to_yolo_format(xml_file_path, img_file_path):
    tree = ET.parse(xml_file_path)
    root = tree.getroot()
    img = cv2.imread(img_file_path)
    size = img.shape
    for obj in root.iter('object'):
        difficult = obj.find('difficult').text
        cls = obj.find('name').text
        if cls not in classes:
            cls = "other"
        if cls not in classes or int(difficult)==1:
            print('skipping', cls)
            continue
        cls_id = classes.index(cls)
        xmlbox = obj.find('bndbox')
        b = (float(xmlbox.find('xmin').text), float(xmlbox.find('xmax').text), float(xmlbox.find('ymin').text), float(xmlbox.find('ymax').text))
        bb = convert(size, b)
        with open(xml_file_path.replace('xml', 'txt'), 'a') as f:
            f.write(f'{cls_id} {bb[0]} {bb[1]} {bb[2]} {bb[3]}\n')



classes = ['no parking', 'no entry', 'other', 'turn right', 'stop', 'parking place', 'pedestrian crossing', 'roundabout', 'give way', 'no stopping']


for folder in ["dataset"]:
    for label_file in os.listdir(os.path.join(folder, 'labels')):
        convert_to_yolo_format(os.path.join(folder, 'labels', label_file), os.path.join(folder, 'images', label_file.replace('xml', 'png')))




# delete all xml files from train/labels and test/labels folder
import os
import shutil

for folder in ['train', 'test']:
    for file in os.listdir(os.path.join(folder, 'labels')):
        if file.endswith('.xml'):
            os.remove(os.path.join(folder, 'labels', file))
print('Done')
