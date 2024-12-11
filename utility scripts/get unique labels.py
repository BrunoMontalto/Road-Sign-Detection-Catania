import os
import xml.etree.ElementTree as ET

def get_labels(file_path):
    tree = ET.parse(file_path)
    root = tree.getroot()
    labels = []
    for obj in root.iter('object'):
        label = obj.find('name').text
        labels.append(label)
    return labels

def main():
    labels = []
    for file in os.listdir('annotations'):
        file_path = os.path.join('annotations', file)
        labels += get_labels(file_path)
    unique_labels = list(set(labels))
    
    for l in unique_labels:
        print(l)

if __name__ == '__main__':
    main()
