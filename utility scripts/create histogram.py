import os
import xml.etree.ElementTree as ET
import matplotlib.pyplot as plt

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
    frequency = [labels.count(l) for l in unique_labels]
    unique_labels = [l for _, l in sorted(zip(frequency, unique_labels))]
    frequency.sort()

    plt.barh(unique_labels, frequency)
    plt.xlabel('Frequency')
    plt.ylabel('Labels')
    plt.title('Labels Frequency')

    # add vertical grid lines
    plt.grid(axis='x')
    # grid goes behind the bars
    plt.gca().set_axisbelow(True)

    
    plt.gcf().set_size_inches(19.2, 10.8)
    # save the plot
    plt.savefig('labels_frequency.png')
    plt.show()



if __name__ == '__main__':
    main()
