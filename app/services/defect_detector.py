import torch
import numpy as np
import cv2

model = torch.hub.load('WongKinYiu/yolov11', 'custom', path='best.pt', source='github')

def detect_defects(image):
    results = model(image)
    return results.pandas().xyxy[0].to_dict(orient="records")
