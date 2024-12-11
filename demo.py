import os
import tkinter as tk
from tkinter import filedialog, ttk
from PIL import Image, ImageTk
import torch
from torchvision import transforms
import numpy as np
import cv2
from matplotlib import pyplot as plt

from ultralytics import YOLO
import torchvision
from torchvision.models.detection.faster_rcnn import FastRCNNPredictor
import xml.etree.ElementTree as ET

MODELS_DIR = "models"
SPLITS_DIR = "splits"
IMAGE_W, IMAGE_H = 500, 500

CATEGORY_MAP = {   # for faster rcnn
    1: "no parking",
    2: "no entry",
    3: "other",
    4: "turn right",
    5: "stop",
    6: "parking place",
    7: "pedestrian crossing",
    8: "roundabout",
    9: "give way",
    10: "no stopping"
}

def load_models():
    models = {}
    for filename in os.listdir(MODELS_DIR):
        model_path = os.path.join(MODELS_DIR, filename)
        model_name = filename.split(".")[0]
        if filename.endswith(".pt") and "YOLO" in filename:
            models[model_name] = YOLO(model_path)


        if filename.endswith(".pth") and "fasterrcnn" in filename:
            model = torchvision.models.detection.fasterrcnn_resnet50_fpn(pretrained=True)
            in_features = model.roi_heads.box_predictor.cls_score.in_features
            model.roi_heads.box_predictor = FastRCNNPredictor(in_features, len(CATEGORY_MAP.values()) + 1) #+ 1 because of the background class
            model.load_state_dict(torch.load(model_path))
            model.eval()
            models[model_name] = model
    return models

models = load_models()


def check_split(filename, model_name):
    #print("checksplit filename", filename)
    split_type = "random" if "random" in model_name else "cluster"
    split_folder = os.path.join(SPLITS_DIR, split_type)

    train_file = os.path.join(split_folder, "train.txt")
    test_file = os.path.join(split_folder, "test.txt")

    with open(train_file, "r") as f:
        train_files = [line.strip().split("\\")[-1] for line in f.readlines()]
    with open(test_file, "r") as f:
        test_files = [line.strip().split("\\")[-1] for line in f.readlines()]

    if filename in train_files:
        return "Train"
    elif filename in test_files:
        return "Test"
    else:
        return "Unknown"


class ModelInferenceApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Demo")
        # disallow resizing
        self.root.resizable(False, False)

        self.selected_model = tk.StringVar()
        # set by default the first model
        self.selected_model.set(list(models.keys())[0])

        self.image_path = None

        frame1 = tk.Frame(root)
        frame2 = tk.Frame(root)
        frame3 = tk.Frame(root)
        frame4 = tk.Frame(root)

        # make cell at row 0 column 1 more wide
        frame1.grid_columnconfigure(1, weight=1)
        frame1.grid_columnconfigure(1, weight=4)

        #same for frame3
        frame3.grid_columnconfigure(0, weight=1)
        frame3.grid_columnconfigure(1, weight=1)
        frame3.grid_columnconfigure(2, weight=1)

        # models menu
        model_label = tk.Label(frame1, text="model:")
        self.model_menu = ttk.Combobox(frame1, textvariable=self.selected_model)
        self.model_menu["values"] = list(models.keys())
   
        # buttons
        load_image_btn = tk.Button(frame2, text="load image and run", command=self.load_image)
        run_button = tk.Button(frame2, text="run on current", command=self.run_on_current)

    
        
        # labels
        self.filename_status_label = tk.Label(root, text="Image: -     Model: -     Split: -")

        original_image_label = tk.Label(frame3, text="Original Image")
        ground_truth_label = tk.Label(frame3, text="Ground Truth")
        processed_image_label = tk.Label(frame3, text="Model Result")
        
        # canvases
        self.original_image_canvas = tk.Canvas(frame4, width=IMAGE_W, height=IMAGE_H, bg="white") 
        self.ground_truth_canvas = tk.Canvas(frame4, width=IMAGE_W, height=IMAGE_H, bg="white")
        self.processed_image_canvas = tk.Canvas(frame4, width=IMAGE_W, height=IMAGE_H, bg="white")

        # make font bigger
        original_image_label.config(font=("Arial", 14))
        ground_truth_label.config(font=("Arial", 14))
        processed_image_label.config(font=("Arial", 14))

        


        # frame1 layout
        model_label.grid(row=0, column=0, padx=5)
        self.model_menu.grid(row=0, column=1, padx=5, sticky="ew")
        frame1.pack(fill="x", pady = 3, padx = 500)

        # frame2 layout
        load_image_btn.grid(row=0, column=0, padx=1)
        run_button.grid(row=0, column=1, padx=1)
        frame2.pack(pady = 0, padx = 400)

        self.filename_status_label.pack()

        # frame3 layout
        original_image_label.grid(row=0, column=0)
        ground_truth_label.grid(row=0, column=1)
        processed_image_label.grid(row=0, column=2)
        frame3.pack(fill = "x", expand=True)

        # frame4 layout
        self.original_image_canvas.grid(row=0, column=0)
        self.ground_truth_canvas.grid(row=0, column=1)
        self.processed_image_canvas.grid(row=0, column=2)
        frame4.pack(fill = "x", expand=True)

    def load_image(self):
        # ask user to select an image file
        file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg *.png *.jpeg")])
        if not file_path:
            return

        self.image_path = file_path

        # load image and display on original_image_canvas
        image = Image.open(file_path)
        # resize image (use bicubic for better quality)
        image = image.resize((IMAGE_W, IMAGE_H), Image.BICUBIC)
        self.image_tk = ImageTk.PhotoImage(image)
        self.original_image_canvas.create_image(0, 0, anchor=tk.NW, image=self.image_tk)


        # read the ground truth file and display it on the ground_truth_canvas
        gt_file = os.path.join("dataset", "labels - PASCAL VOC", os.path.basename(file_path).split(".")[0] + ".xml")
        if os.path.exists(gt_file):
            tree = ET.parse(gt_file)
            root = tree.getroot()

            boxes = []
            labels = []

            width = int(root.find("size").find("width").text)

            for obj in root.findall("object"):
                label = obj.find("name").text
                if label not in CATEGORY_MAP.values():
                    #print("label", label, "not found in the category map")
                    label = "other" # NOTE: we are ignoring that we have a misspelled label in the dataset, since it will become other anyway
                labels.append(label)
                box = obj.find("bndbox")
                x1 = int(box.find("xmin").text)/width * IMAGE_W
                y1 = int(box.find("ymin").text)/width * IMAGE_H
                x2 = int(box.find("xmax").text)/width * IMAGE_W
                y2 = int(box.find("ymax").text)/width * IMAGE_H
                boxes.append([x1, y1, x2, y2])

            # plot the ground truth boxes
            plt.figure(figsize=(10, 10))
            plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
            plt.imshow(image)
            ax = plt.gca()
            for box, label in zip(boxes, labels):
                x1, y1, x2, y2 = box
                w = x2 - x1
                h = y2 - y1
                rect = plt.Rectangle((x1, y1), w, h, fill=False, edgecolor='green', linewidth=4)
                ax.add_patch(rect)
                ax.text(x1, y1, label, fontsize=20, color='green', bbox = dict(facecolor='white', alpha=0.8))
            plt.axis('off')

            plt.savefig('temp1.png')

            # load temp.png
            processed_image = Image.open('temp1.png')
            processed_image = processed_image.resize((IMAGE_W, IMAGE_H), Image.BICUBIC)

            self.ground_truth_tk = ImageTk.PhotoImage(processed_image)
            self.ground_truth_canvas.create_image(0, 0, anchor=tk.NW, image=self.ground_truth_tk)

            os.remove('temp1.png')
            


        # check split and run inference
        model_name = self.selected_model.get()
        if model_name:
            filename_status = check_split(os.path.basename(file_path), model_name)
            self.filename_status_label.config(text=f"Image: {os.path.basename(file_path)}     Model: {model_name}     Split: {filename_status}")
            self.run_inference(file_path, model_name)

    def run_on_current(self):
        if not self.image_path:
            return
        
        # clear canvas
        #self.processed_image_canvas.delete("all")

        # make canvas semi-transparent
        self.processed_image_canvas.create_rectangle(0, 0, IMAGE_W, IMAGE_H, fill="white", outline="white", stipple="gray50")

        # update window
        self.processed_image_canvas.update()

        model_name = self.selected_model.get()
        if model_name:
            filename_status = check_split(os.path.basename(self.image_path), model_name)
            self.filename_status_label.config(text=f"Image: {os.path.basename(self.image_path)}     Model: {model_name}     Split: {filename_status}")
            self.run_inference(self.image_path, model_name)


    def run_inference(self, file_path, model_name):
        # load image
        image = Image.open(file_path)#.convert("RGB")

        # infer
        model = models[model_name]
        if "YOLO" in model_name:
            results = model(image)

            # extract results
            annotated_image = results[0].plot()  # Get image with annotations
            annotated_image = cv2.cvtColor(annotated_image, cv2.COLOR_BGR2RGB) # to RGB
            #bboxes = results[0].boxes.xyxy.cpu().numpy()  # Bounding box coordinates
            #confidences = results[0].boxes.conf.cpu().numpy()  # Confidence scores

            # plot the annotated image
            plt.figure(figsize=(10, 10))
            #set padding to 0
            plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
            plt.imshow(annotated_image)
            plt.axis('off')
            
            # save the plot as temp.png
            plt.savefig('temp2.png')

            # load temp.png
            processed_image = Image.open('temp2.png')
            processed_image = processed_image.resize((IMAGE_W, IMAGE_H), Image.BICUBIC)

            self.processed_image_tk = ImageTk.PhotoImage(processed_image)
            self.processed_image_canvas.create_image(0, 0, anchor=tk.NW, image=self.processed_image_tk)

            os.remove('temp2.png')
        
        else:
            assert "fasterrcnn" in model_name
            # trasform image to tensor
            transform = transforms.ToTensor()
            image = transform(image)

            results = model([image])

            pred_dict = results[0]

            boxes = pred_dict["boxes"].detach().numpy()
            labels = pred_dict["labels"].detach().numpy()
            scores = pred_dict["scores"].detach().numpy()

            threshold = 0.5
            idx = np.where(scores > threshold)[0]
            boxes = boxes[idx]
            labels = labels[idx]
            scores = scores[idx]

            plt.figure(figsize=(10, 10))
            plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
            plt.imshow(image.permute(1, 2, 0))
            ax = plt.gca()
            for box, label, score in zip(boxes, labels, scores):
                x1, y1, x2, y2 = box
                w = x2 - x1
                h = y2 - y1
                rect = plt.Rectangle((x1, y1), w, h, fill=False, edgecolor='red', linewidth=4)
                ax.add_patch(rect)
                ax.text(x1, y1, f"{CATEGORY_MAP[label]}: {score:.2f}", fontsize=20, color='red', bbox = dict(facecolor='white', alpha=0.8))
            plt.axis('off')

            plt.savefig('temp3.png')

            # load temp.png
            processed_image = Image.open('temp3.png')
            processed_image = processed_image.resize((IMAGE_W, IMAGE_H), Image.BICUBIC)

            self.processed_image_tk = ImageTk.PhotoImage(processed_image)
            self.processed_image_canvas.create_image(0, 0, anchor=tk.NW, image=self.processed_image_tk)

            os.remove('temp3.png')




if __name__ == "__main__":
    root = tk.Tk()
    app = ModelInferenceApp(root)
    root.mainloop()
