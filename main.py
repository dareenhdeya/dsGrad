"""
VisionGuard - FastAPI inference service.

Two endpoints:
  POST /predict/image  -> runs detection on a single uploaded image
  POST /predict/video   -> runs detection on a sample of frames from an uploaded video

Run with:
  uvicorn main:app --reload
"""

import time
import base64

import cv2
import numpy as np
from fastapi import FastAPI, File, UploadFile, HTTPException, Query
from ultralytics import YOLO

from compliance import summarize_detections, CLASS_NAMES

MODEL_PATH = "weights/best.pt"
IMG_SIZE = 640

app = FastAPI(title="VisionGuard API")

# the model is loaded once when the service starts, not on every request
model = YOLO(MODEL_PATH)

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/jpg"}
ALLOWED_VIDEO_TYPES = {"video/mp4", "video/avi", "video/quicktime"}


@app.get("/health")
def health():
    return {"status": "ok", "model": MODEL_PATH}


def run_detection(image, conf):
    """Run the model on one image (numpy array, BGR) and return a list of boxes."""
    result = model.predict(source=image, imgsz=IMG_SIZE, conf=conf, verbose=False)[0]

    boxes = []
    for i in range(len(result.boxes)):
        class_id = int(result.boxes.cls[i])
        confidence = float(result.boxes.conf[i])
        x1, y1, x2, y2 = result.boxes.xyxy[i].tolist()
        boxes.append({
            "class_id": class_id,
            "class_name": CLASS_NAMES[class_id],
            "confidence": round(confidence, 3),
            "box": [round(x1, 1), round(y1, 1), round(x2, 1), round(y2, 1)],
        })

    annotated = result.plot()  # BGR image with boxes drawn on it
    return boxes, annotated


def encode_image_base64(image_bgr):
    success, buffer = cv2.imencode(".jpg", image_bgr)
    if not success:
        return None
    return base64.b64encode(buffer).decode("utf-8")


@app.post("/predict/image")
async def predict_image(file: UploadFile = File(...), conf: float = Query(0.25, ge=0.05, le=0.95)):
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=400, detail="File must be a JPEG or PNG image")

    file_bytes = await file.read()
    if len(file_bytes) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    image_array = np.frombuffer(file_bytes, dtype=np.uint8)
    image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
    if image is None:
        raise HTTPException(status_code=400, detail="Could not read image file")

    start_time = time.time()
    boxes, annotated = run_detection(image, conf)
    processing_time_ms = round((time.time() - start_time) * 1000, 1)

    summary = summarize_detections(boxes)

    return {
        "detections": boxes,
        "compliance": summary,
        "confidence_threshold": conf,
        "processing_time_ms": processing_time_ms,
        "annotated_image_base64": encode_image_base64(annotated),
    }


@app.post("/predict/video")
async def predict_video(
    file: UploadFile = File(...),
    conf: float = Query(0.25, ge=0.05, le=0.95),
    frame_skip: int = Query(10, ge=1, description="analyze 1 out of every N frames"),
):
    if file.content_type not in ALLOWED_VIDEO_TYPES:
        raise HTTPException(status_code=400, detail="File must be an MP4, AVI, or MOV video")

    file_bytes = await file.read()
    if len(file_bytes) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    # OpenCV needs the video written to disk to open it
    temp_path = "temp_upload_video.mp4"
    with open(temp_path, "wb") as f:
        f.write(file_bytes)

    capture = cv2.VideoCapture(temp_path)
    if not capture.isOpened():
        raise HTTPException(status_code=400, detail="Could not open video file")

    fps = capture.get(cv2.CAP_PROP_FPS) or 0

    start_time = time.time()
    frame_results = []
    violation_frames = []  # frames with an annotated image, capped below
    frame_index = 0
    violations_found = 0
    max_violation_frames_returned = 12

    while True:
        success, frame = capture.read()
        if not success:
            break

        if frame_index % frame_skip == 0:
            boxes, annotated = run_detection(frame, conf)
            summary = summarize_detections(boxes)
            timestamp_sec = round(frame_index / fps, 2) if fps else None

            if summary["status"] == "VIOLATION":
                violations_found += 1
                if len(violation_frames) < max_violation_frames_returned:
                    violation_frames.append({
                        "frame_index": frame_index,
                        "timestamp_sec": timestamp_sec,
                        "compliance": summary,
                        "annotated_image_base64": encode_image_base64(annotated),
                    })

            frame_results.append({
                "frame_index": frame_index,
                "timestamp_sec": timestamp_sec,
                "compliance": summary,
            })

        frame_index += 1

    capture.release()
    processing_time_ms = round((time.time() - start_time) * 1000, 1)

    return {
        "frames_analyzed": len(frame_results),
        "total_frames": frame_index,
        "frames_with_violation": violations_found,
        "confidence_threshold": conf,
        "processing_time_ms": processing_time_ms,
        "frame_results": frame_results,
        "violation_frames": violation_frames,
    }
