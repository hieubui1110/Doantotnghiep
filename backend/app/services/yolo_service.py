import os
import random
from typing import List, Dict, Any
from app.core.config import settings

class YOLOService:
    def __init__(self, model_path: str = None):
        self.model_path = model_path or settings.YOLO_MODEL_PATH
        self.model = None
        self.is_mock = True
        
        if os.path.exists(self.model_path):
            try:
                from ultralytics import YOLO
                self.model = YOLO(self.model_path)
                self.is_mock = False
                print(f"[+] YOLO Model loaded successfully from {self.model_path}")
            except Exception as e:
                print(f"[!] Failed to load YOLO model: {e}. Running in Mock Mode.")
        else:
            print(f"[!] YOLO Model file not found at '{self.model_path}'. Running in Mock Mode.")

    def detect(self, image_data_or_path: Any, conf_threshold: float = None) -> List[Dict[str, Any]]:
        threshold = conf_threshold or settings.YOLO_CONFIDENCE_THRESHOLD
        
        if not self.is_mock and self.model:
            try:
                results = self.model(image_data_or_path, conf=threshold)
                detections = []
                for r in results:
                    for box in r.boxes:
                        cls_id = int(box.cls[0])
                        label = self.model.names[cls_id]
                        # Map to supported vehicle types in database design
                        # DB accepts: 'car', 'truck', 'bus', 'motorcycle', 'bicycle'
                        vehicle_map = {
                            "car": "car",
                            "truck": "truck",
                            "bus": "bus",
                            "motorbike": "motorcycle",
                            "motorcycle": "motorcycle",
                            "bicycle": "bicycle",
                            "person": "bicycle" # fallback/dummy mapping if any
                        }
                        vehicle_type = vehicle_map.get(label, "car")
                        
                        conf = float(box.conf[0])
                        xyxy = box.xyxy[0].tolist()
                        
                        detections.append({
                            "class_id": cls_id,
                            "class_name": vehicle_type,
                            "confidence": conf,
                            "bbox": {
                                "x1": int(xyxy[0]),
                                "y1": int(xyxy[1]),
                                "x2": int(xyxy[2]),
                                "y2": int(xyxy[3])
                            }
                        })
                return detections
            except Exception as e:
                print(f"[-] YOLO Inference failed: {e}. Falling back to Mock.")
                
        # Generate mock detections for development
        labels = ["car", "motorcycle", "truck", "bus", "bicycle"]
        detections = []
        num_objects = random.randint(2, 6)
        for i in range(num_objects):
            label = random.choice(labels)
            conf = random.uniform(0.55, 0.97)
            x1 = random.randint(10, 300)
            y1 = random.randint(10, 300)
            x2 = x1 + random.randint(50, 150)
            y2 = y1 + random.randint(50, 150)
            
            # Optionally add license plate or speed metadata
            meta = {}
            if label in ["car", "truck"]:
                meta["license_plate"] = f"{random.randint(29, 99)}A-{random.randint(100, 999)}.{random.randint(10, 99)}"
                meta["speed_kmh"] = random.randint(30, 90)
            
            detections.append({
                "class_id": labels.index(label),
                "class_name": label,
                "confidence": conf,
                "bbox": {
                    "x1": x1,
                    "y1": y1,
                    "x2": x2,
                    "y2": y2
                },
                "metadata": meta
            })
        return detections

yolo_service = YOLOService()
