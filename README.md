# VisionGuard – API & Demo

 The final model used here is `yolo26s_exp1` (`best.pt`), with `imgsz=640`.

 ### Classes

 - Person
- Hardhat
- NO-Hardhat
- Safety Vest
- NO-Safety Vest

 ## Files

 - `main.py` — FastAPI service with image and video endpoints
- `compliance.py` — Logic for converting detections into a `COMPLIANT` / `VIOLATION` decision
- `streamlit_app.py` — Simple UI that communicates with the API
- `weights/best.pt` — Trained model weights (`yolo26s_exp1`)
- `requirements.txt`

 ## Local Setup

 ### 1\. Install the dependencies

```
pip install -r requirements.txt
```

 ### 2\. Start the API

 Keep this terminal open:

```
uvicorn main:app --reload
```

 Once the server is running, open:

 `http://127.0.0.1:8000/docs`

 You will see the automatically generated API documentation, including all available endpoints.

 ### 3\. Start the Streamlit UI

 Open a second terminal and run:

```
streamlit run streamlit_app.py
```

 The interface will open in your browser, where you can upload an image or video and view the results.

 ## Endpoints

 ### `POST /predict/image`

 - **Parameter:** Image file (`file`)
- **Optional parameter:** `conf` — confidence threshold, default is `0.25`
- **Returns:**
  - List of detections
  - Compliance summary
  - Processing time
  - Annotated image with bounding boxes encoded as Base64

 ### `POST /predict/video`

 - **Parameter:** Video file (`file`)
- **Optional parameters:**
  - `conf`
  - `frame_skip`
- The endpoint analyzes **one frame every `frame_skip` frames** instead of processing the entire video frame-by-frame, making it faster.
- **Returns:**
  - Number of frames containing violations
  - Results for each analyzed frame

 ## Optional Construction Animation (Lottie)

 The UI already includes CSS animations that work without any additional setup. If you want to add a ready-made construction-themed animation:

 1. Go to  LottieFiles  and search for **“construction”** or **“hard hat”**.
2. Open any free animation.
3. Click **Embed → Lottie URL** and copy the URL. It should end with `.json`.
4. Paste the URL into the `HERO_LOTTIE_URL` variable at the beginning of `streamlit_app.py`.

 ## Video Processing Note

 The video endpoint processes the video **after it has been uploaded**, rather than in real time. This batch-processing approach is sufficient for the project requirements.

 Processing every frame is not practical on a typical computer, so the system analyzes a sample of frames instead, based on the selected `frame_skip` value.