# E:\attendance_cctv\tools\build_encodings.py
import os, pickle, sys
import numpy as np
import face_recognition

DATA_DIR = r"E:\dataset-attendance\clean_faces"
ENC_PATH = r"E:\attendance_cctv\encodings.pickle"

encodings = []
names = []

if not os.path.isdir(DATA_DIR):
    print(f"Dataset folder not found: {DATA_DIR}")
    sys.exit(1)

for person in os.listdir(DATA_DIR):
    person_dir = os.path.join(DATA_DIR, person)
    if not os.path.isdir(person_dir):
        continue
    for f in os.listdir(person_dir):
        if not f.lower().endswith((".jpg",".jpeg",".png")):
            continue
        path = os.path.join(person_dir, f)
        image = face_recognition.load_image_file(path)
        boxes = face_recognition.face_locations(image, model="hog")
        if not boxes:
            print(f"No face found in {path}, skipping")
            continue
        encs = face_recognition.face_encodings(image, boxes)
        for enc in encs:
            encodings.append(enc)
            names.append(person)

data = {"encodings": encodings, "names": names}
with open(ENC_PATH, "wb") as f:
    pickle.dump(data, f)
print(f"Encodings saved to {ENC_PATH} for {len(encodings)} faces from {len(set(names))} students.")