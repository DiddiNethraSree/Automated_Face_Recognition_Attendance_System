# 🎓 Automated Face Recognition Attendance System

> A real-time, AI-powered attendance management system built for Bapatla Engineering College using CCTV cameras, face recognition, and a Flask web dashboard.

---

## 📌 Table of Contents

- [About the Project](#about-the-project)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [How It Works](#how-it-works)
- [User Roles](#user-roles)
- [Screenshots](#screenshots)
- [Database](#database)
- [Future Scope](#future-scope)

---

## 📖 About the Project

The **Automated Face Recognition Attendance System (AFRAS)** eliminates the need for manual roll calls by automatically detecting and recognizing students' faces through CCTV cameras. Attendance is recorded period-wise in a local SQLite database and is accessible through a web dashboard for both HODs and students.

This project was developed as a final-year B.Tech project at **Bapatla Engineering College**.

---

## ✨ Features

- 🎥 **Real-time CCTV face recognition** using OpenCV + `face_recognition` library
- 📆 **Period-wise attendance tracking** (6 periods per day)
- 🧑‍💼 **HOD Dashboard** — view, filter, and manually edit attendance
- 🎓 **Student Dashboard** — view personal attendance percentage & history
- 🔐 **Secure login** with role-based access (HOD / Student)
- 📝 **Student self-registration** with live webcam photo capture
- 🔁 **Forgot Password** recovery using Date of Birth verification
- 📊 **Attendance categories**: Eligible (≥75%), Condonation (65–75%), Detained (<65%)
- 🏢 **Multi-department support** — HOD accounts auto-scoped to their department
- 📅 **Working day detection** — weekends and holidays auto-skipped
- 📤 **Manual attendance entry** by HOD for missed records
- 🔄 **Dynamic face encoding** — new students are immediately recognized after signup

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | Python, Flask |
| **Face Recognition** | `face_recognition`, `dlib`, OpenCV (`cv2`) |
| **Database** | SQLite3 (local) |
| **Frontend** | HTML5, CSS3, Jinja2 templates, JavaScript |
| **Image Processing** | NumPy, Pillow |
| **Server** | Flask dev server / `.bat` launcher |

---

## 📁 Project Structure

```
attendance_cctv/
│
├── app.py                    # Main Flask application (all routes)
├── database.py               # DB schema, init, backfill logic
├── cctv_attendance.py        # CCTV face detection & auto-marking script
├── encode_faces.py           # Script to encode face images → encodings.pickle
├── sanitize_images.py        # Utility to clean face image dataset
│
├── attendance.db             # SQLite database (attendance history)
├── encodings.pickle          # Precomputed face encodings (auto-generated)
│
├── requirements.txt          # Python dependencies
├── start_attendance_server.bat  # One-click server launcher (Windows)
├── run_server_hidden.vbs     # Hidden background server launcher
│
├── templates/                # Jinja2 HTML templates
│   ├── base.html
│   ├── login.html
│   ├── hod_dashboard.html
│   ├── student_dashboard.html
│   ├── student_signup.html
│   ├── hod_signup.html
│   ├── hod_manual_attendance.html
│   └── ...
│
└── static/                   # CSS, JS, images, fonts
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.9 or 3.10 (recommended)
- Windows OS (tested)
- Webcam / CCTV camera connected
- `cmake` and Visual Studio Build Tools (for `dlib` compilation)

### Installation

**1. Clone the repository**
```bash
git clone https://github.com/DiddiNethraSree/Automated_Face_Recognition_Attendance_System.git
cd Automated_Face_Recognition_Attendance_System
```

**2. Create and activate a virtual environment**
```bash
python -m venv venv
venv\Scripts\activate
```

**3. Install dependencies**
```bash
pip install -r requirements.txt
```

**4. Run the Flask server**
```bash
python app.py
```

**5. Open in browser**
```
http://127.0.0.1:5000
```

> **Note:** To run CCTV auto-detection in parallel, open a second terminal and run:
> ```bash
> python cctv_attendance.py
> ```

### Re-generate Face Encodings (if needed)

If you add new face images manually to `clean_faces/`:
```bash
python encode_faces.py
```

---

## ⚙️ How It Works

```
CCTV Camera → OpenCV Frame Capture
        ↓
Face Detection (HOG model via face_recognition)
        ↓
Face Encoding + Match against encodings.pickle
        ↓
Student ID identified → attendance.db updated
        ↓
Flask Dashboard → HOD/Student views attendance
```

1. `cctv_attendance.py` continuously reads frames from the connected camera
2. Detected faces are compared against stored encodings
3. When a match is found, the student's attendance is marked as **Present** for the active period
4. The Flask web app reads from the SQLite database to show real-time results

---

## 👤 User Roles

### 🧑‍💼 HOD (Head of Department)
- Register at `/hod/signup` (auto-scoped to department)
- View all attendance records with filters (date, year, branch, section)
- Manually add/edit attendance for any student
- Delete student records
- View attendance categories (Eligible / Condonation / Detained)

### 🎓 Student
- Register at `/student/signup` (webcam photo capture required)
- View personal attendance percentage
- View period-wise attendance history day by day
- Update profile and change password

---

## 🗄️ Database

The project uses a local **SQLite** database (`attendance.db`) with the following main tables:

| Table | Purpose |
|---|---|
| `users` | Stores student & HOD accounts (user_id, password, role, branch, year, section) |
| `attendance` | Legacy daily attendance records |
| `period_attendance` | Period-wise daily records (6 periods/day, present/absent/value) |

> The `attendance.db` file is included in this repository so that existing attendance history is preserved.

---

## 🔮 Future Scope

- ☁️ Migrate from SQLite to cloud database (PostgreSQL / Firebase)
- 📧 Email/SMS alerts for low attendance students
- 📱 Mobile app for students
- 🤖 Upgrade face recognition to CNN-based deep learning model
- 📊 Analytics dashboard with charts and export to Excel/PDF
- 🌐 Deploy on cloud server (AWS / Render / Railway)
- 📷 Support for multiple simultaneous cameras

---

## 🏫 Institution

**Bapatla Engineering College**  
Bapatla, Andhra Pradesh, India

---

## 📄 License

This project is developed for academic purposes.

---

> ⭐ If you found this project helpful, please give it a star!
