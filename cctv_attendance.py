import cv2
import face_recognition
import pickle
import numpy as np
from datetime import datetime, time
from database import (
    init_today, mark_present, is_working_day,
    init_today_periods, mark_period_present, get_current_period, PERIODS
)

# ---------------- CONFIG ----------------
THRESHOLD = 0.45
ENCODINGS_PATH = "encodings.pickle"

# ---------------- LOAD ENCODINGS ----------------
with open(ENCODINGS_PATH, "rb") as f:
    data = pickle.load(f)

known_encodings = np.array(data["encodings"])
known_names = np.array(data["names"])

all_students = set(known_names)
present_students = set()          # For legacy daily attendance
present_period_set = set()        # Track (student_id, period) combos already marked

# Build attendance windows from PERIODS config
def in_attendance_window(now=None):
    now_dt = now or datetime.now().time()
    try:
        from zoneinfo import ZoneInfo
        now_dt = now or datetime.now(ZoneInfo("Asia/Kolkata")).time()
    except Exception:
        pass
    for pnum, (sh, sm, eh, em) in PERIODS.items():
        if time(sh, sm) <= now_dt < time(eh, em):
            return True
    return False

# Initialize today's attendance only on working days
try:
    from zoneinfo import ZoneInfo
    IST = ZoneInfo("Asia/Kolkata")
except Exception:
    IST = None

today_str = (datetime.now(IST) if IST else datetime.now()).strftime("%Y-%m-%d")
if is_working_day(today_str):
    init_today(all_students)
    init_today_periods(all_students)

# ---------------- START CAMERA ----------------
cap = cv2.VideoCapture(0)
print("Press 'Q' to stop")
print(f"📋 Period Schedule: {', '.join(f'P{k}: {v[0]:02d}:{v[1]:02d}-{v[2]:02d}:{v[3]:02d}' for k, v in PERIODS.items())}")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Resize for speed
    small = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
    rgb = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)

    boxes = face_recognition.face_locations(rgb, model="hog")
    encodings = face_recognition.face_encodings(rgb, boxes)

    for (top, right, bottom, left), encoding in zip(boxes, encodings):
        distances = face_recognition.face_distance(known_encodings, encoding)
        best_idx = np.argmin(distances)
        best_dist = distances[best_idx]

        # Scale back box
        top, right, bottom, left = top*2, right*2, bottom*2, left*2

        now_dt = datetime.now(IST) if IST else datetime.now()
        if best_dist < THRESHOLD and in_attendance_window() and is_working_day(now_dt.strftime("%Y-%m-%d")):
            student_id = known_names[best_idx]
            accuracy = round((1 - best_dist) * 100, 2)

            # Legacy daily attendance (unchanged)
            if student_id not in present_students:
                mark_present(student_id)
                present_students.add(student_id)

            # Period-wise attendance (new)
            current_period = get_current_period(now_dt.time())
            if current_period is not None:
                combo = (student_id, current_period)
                if combo not in present_period_set:
                    result = mark_period_present(student_id, current_period)
                    if result:
                        present_period_set.add(combo)
                        pnum, status, value = result
                        status_icon = "✅" if status == "present" else "❌"
                        print(f"  {status_icon} {student_id} → P{pnum} {status} ({value})")

            label = f"{student_id} ({accuracy}%)"
            color = (0, 255, 0)
        else:
            label = "UNKNOWN"
            color = (0, 0, 255)

        # Draw box & label
        cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
        cv2.rectangle(frame, (left, top - 30), (right, top), color, -1)
        cv2.putText(
            frame, label,
            (left + 5, top - 5),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7, (255, 255, 255), 2
        )

    cv2.imshow("CCTV Attendance", frame)

    if cv2.waitKey(1) & 0xFF in (ord('q'), ord('Q')):
        print("✔ Attendance session ended by user")
        break

# ---------------- CLEAN EXIT ----------------
cap.release()
cv2.destroyAllWindows()

# ---------------- FINAL SUMMARY ----------------
print("\n📊 ATTENDANCE SUMMARY (PRESENT ONLY)")
print(f"Present: {len(present_students)}")
for s in sorted(present_students):
    print(" ✔", s)

print(f"\n📋 PERIOD-WISE MARKS: {len(present_period_set)} period entries recorded")

