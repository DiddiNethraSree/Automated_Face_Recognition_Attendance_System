import os
import cv2
import face_recognition
import pickle

DATASET_PATH = r"E:\dataset-attendance\clean_faces"
ENCODINGS_PATH = "encodings.pickle"

known_encodings = []
known_names = []

for student_id in os.listdir(DATASET_PATH):
    student_folder = os.path.join(DATASET_PATH, student_id)

    if not os.path.isdir(student_folder):
        continue

    print(f"[INFO] Processing {student_id}")

    for file in os.listdir(student_folder):
        if not file.lower().endswith((".jpg", ".png", ".jpeg")):
            continue

        img_path = os.path.join(student_folder, file)

        image = cv2.imread(img_path)
        if image is None:
            print(f"[ERROR] Could not read {file}")
            continue

        # OpenCV → RGB
        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        boxes = face_recognition.face_locations(
            rgb,
            model="hog",
            number_of_times_to_upsample=2
        )


        if len(boxes) == 0:
            print(f"[DEBUG] No face detected in {img_path}")
            cv2.imshow("DEBUG IMAGE", image)
            cv2.waitKey(1000)
            cv2.destroyAllWindows()
            continue


        encodings = face_recognition.face_encodings(rgb, boxes)

        for encoding in encodings:
            known_encodings.append(encoding)
            known_names.append(student_id)
            print(f"[OK] Encoded {student_id} from {file}")

print(f"\n[OK] Encoded {len(known_encodings)} face images successfully")

data = {
    "encodings": known_encodings,
    "names": known_names
}

with open(ENCODINGS_PATH, "wb") as f:
    pickle.dump(data, f)

print("💾 Encodings saved to encodings.pickle") 
# py -3.10 -m venv venv -- to get into venv
#venv\Scripts\activate
