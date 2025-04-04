import cv2
import torch
import face_recognition
import numpy as np
from ultralytics import YOLO

model = YOLO("yolov8n.pt")

def detect_faces_yolo(image_path):
    image = cv2.imread(image_path)
    results = model(image)

    face_locations = []
    for result in results:
        for box in result.boxes.xyxy:
            x1, y1, x2, y2 = map(int, box)
            face_locations.append((y1, x2, y2, x1))

    return image, face_locations

def get_face_encoding(image, face_locations):
    encodings = face_recognition.face_encodings(image, face_locations)
    return encodings if encodings else None
