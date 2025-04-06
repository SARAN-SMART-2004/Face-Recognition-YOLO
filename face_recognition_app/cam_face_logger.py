import cv2
import face_recognition
import numpy as np
import os
import pandas as pd
from datetime import datetime
from threading import Thread
from .models import KnownPerson

# Define camera RTSP streams
CAMERA_STREAMS = {
    1: "rtsp://user:pass@192.168.1.101/Streaming/Channels/101/",
    2: "rtsp://user:pass@192.168.1.102/Streaming/Channels/101/",
    3: "rtsp://user:pass@192.168.1.103/Streaming/Channels/101/",
    4: "rtsp://user:pass@192.168.1.104/Streaming/Channels/101/",
    5: "rtsp://user:pass@192.168.1.105/Streaming/Channels/101/",
    6: "rtsp://user:pass@192.168.1.106/Streaming/Channels/101/",
    7: "rtsp://user:pass@192.168.1.107/Streaming/Channels/101/",
    8: "rtsp://user:pass@192.168.1.108/Streaming/Channels/101/",
}

# Excel log file
def get_log_file():
    today = datetime.now().strftime("%Y-%m-%d")
    return f"attendance_{today}.xlsx"

def load_log():
    file = get_log_file()
    if os.path.exists(file):
        return pd.read_excel(file)
    return pd.DataFrame(columns=["Date", "IN Time", "Name", "OUT Time"])

def save_log(df):
    df.to_excel(get_log_file(), index=False)

def log_entry(name, camera_id):
    df = load_log()
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M:%S")

    if camera_id != 8:
        if not ((df["Name"] == name) & (df["Date"] == date_str)).any():
            new_row = {"Date": date_str, "IN Time": time_str, "Name": name, "OUT Time": ""}
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            save_log(df)
            print(f"🟢 IN logged for {name} at {time_str} (Cam {camera_id})")
    else:
        # OUT detection on camera 8
        match = df[(df["Name"] == name) & (df["Date"] == date_str) & (df["OUT Time"] == "")]
        if not match.empty:
            df.loc[match.index[-1], "OUT Time"] = time_str
            save_log(df)
            print(f"🔴 OUT logged for {name} at {time_str} (Cam 8)")

def get_known_faces():
    known_people = KnownPerson.objects.all()
    encodings, names = [], []
    for person in known_people:
        encoding = np.frombuffer(person.encoding, dtype=np.float64)
        if encoding.size == 128:
            encodings.append(encoding)
            names.append(person.name)
    return encodings, names

def process_camera(camera_id, stream_url, known_encodings, known_names):
    cap = cv2.VideoCapture(stream_url)

    if not cap.isOpened():
        print(f"⚠️ Could not open camera {camera_id}")
        return

    while True:
        ret, frame = cap.read()
        if not ret:
            continue

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_frame)
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

        for face_encoding in face_encodings:
            matches = face_recognition.compare_faces(known_encodings, face_encoding)
            if True in matches:
                index = matches.index(True)
                name = known_names[index]
                log_entry(name, camera_id)

        # Optional: show live feed (comment this in headless server)
        # cv2.imshow(f"Camera {camera_id}", frame)
        # if cv2.waitKey(1) & 0xFF == ord('q'):
        #     break

    cap.release()
    cv2.destroyAllWindows()

def start_all_cameras():
    known_encodings, known_names = get_known_faces()
    for cam_id, stream in CAMERA_STREAMS.items():
        Thread(target=process_camera, args=(cam_id, stream, known_encodings, known_names), daemon=True).start()

