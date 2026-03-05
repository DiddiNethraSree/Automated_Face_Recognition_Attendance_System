import sqlite3
from datetime import datetime, date, time, timedelta
import urllib.request
import re

DB_PATH = "attendance.db"

# ---------------- PERIOD CONFIGURATION ----------------
# 6 periods: (start_hour, start_min, end_hour, end_min)
PERIODS = {
    1: (7, 30, 8, 20),
    2: (8, 20, 9, 10),
    3: (9, 10, 10, 0),
    4: (10, 30, 11, 20),
    5: (11, 20, 12, 10),
    6: (12, 10, 13, 0),
}

# Thresholds removed as per user request: any capture during period is purely Present (1.0).

def now_ist():
    try:
        from zoneinfo import ZoneInfo
        return datetime.now(ZoneInfo("Asia/Kolkata"))
    except Exception:
        # Fallback to system local time if tzdata not available
        return datetime.now()

# ---------------- INITIALIZE DATABASE ----------------
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS attendance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id TEXT,
        date TEXT,
        first_seen_time TEXT,
        present INTEGER,
        class TEXT,
        UNIQUE(student_id, date)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id TEXT PRIMARY KEY,
        password TEXT,
        role TEXT,
        dob TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS holidays (
        date TEXT PRIMARY KEY,
        name TEXT
    )
    """)

    # Period-wise attendance table (new)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS period_attendance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id TEXT,
        date TEXT,
        period INTEGER,
        status TEXT DEFAULT 'absent',
        value REAL DEFAULT 0.0,
        first_seen_time TEXT,
        UNIQUE(student_id, date, period)
    )
    """)

    # Check and add missing columns for backwards compatibility
    cursor.execute("PRAGMA table_info(users)")
    columns = [column[1] for column in cursor.fetchall()]
    if 'dob' not in columns:
        cursor.execute("ALTER TABLE users ADD COLUMN dob TEXT")
    if 'branch' not in columns:
        cursor.execute("ALTER TABLE users ADD COLUMN branch TEXT")
    if 'name' not in columns:
        cursor.execute("ALTER TABLE users ADD COLUMN name TEXT")
    if 'year' not in columns:
        cursor.execute("ALTER TABLE users ADD COLUMN year TEXT")
    if 'section' not in columns:
        cursor.execute("ALTER TABLE users ADD COLUMN section TEXT")

    # Seed only verified student accounts (hod accounts must be created via /hod/signup)
    users = [
        ('21CSE001', '123', 'student', '2003-05-15'),
        ('21CSE002', '123', 'student', '2003-05-16'),
        ('21CSE003', '123', 'student', '2003-05-17'),
        ('21CSE004', '123', 'student', '2003-05-18'),
        ('21CSE005', '123', 'student', '2003-05-19'),
        ('21CSE006', '123', 'student', '2003-05-20'),
        ('24CSE001', '123', 'student', '2005-08-10'),
    ]
    cursor.executemany("INSERT OR IGNORE INTO users (user_id, password, role, dob) VALUES (?, ?, ?, ?)", users)

    try:
        sync_holidays_google()
    except Exception:
        pass

    conn.commit()
    conn.close()

# ---------------- HOLIDAYS & WORKING DAY ----------------
def is_working_day(date_str: str) -> bool:
    dt = datetime.strptime(date_str, "%Y-%m-%d").date()
    if dt.weekday() == 6:
        return False
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM holidays WHERE date=?", (date_str,))
    row = cur.fetchone()
    conn.close()
    return row is None

def sync_holidays_google():
    year = now_ist().date().year
    url = "https://calendar.google.com/calendar/ical/en.indian%23holiday%40group.v.calendar.google.com/public/basic.ics"
    with urllib.request.urlopen(url, timeout=5) as resp:
        content = resp.read().decode("utf-8", errors="ignore")
    events = re.split(r"BEGIN:VEVENT", content)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    for ev in events:
        mdate = re.search(r"DTSTART;VALUE=DATE:(\d{8})", ev)
        msum = re.search(r"SUMMARY:(.+)", ev)
        if mdate and msum:
            ymd = mdate.group(1)
            y, m, d = ymd[0:4], ymd[4:6], ymd[6:8]
            if int(y) in (year, year+1):
                ds = f"{y}-{m}-{d}"
                name = msum.group(1).strip()
                cur.execute("INSERT OR IGNORE INTO holidays (date, name) VALUES (?, ?)", (ds, name))
    conn.commit()
    conn.close()

# ---------------- MARK ALL STUDENTS ABSENT FOR TODAY ----------------
def init_today(all_students):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    today = now_ist().strftime("%Y-%m-%d")

    for student in all_students:
        cursor.execute("""
        INSERT OR IGNORE INTO attendance (student_id, date, first_seen_time, present)
        VALUES (?, ?, NULL, 0)
        """, (student, today))

    conn.commit()
    conn.close()


# ---------------- MARK STUDENT PRESENT ----------------
def mark_present(student_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    today = now_ist().strftime("%Y-%m-%d")
    time_now = now_ist().strftime("%H:%M:%S")

    cursor.execute("""
    UPDATE attendance
    SET present = 1, first_seen_time = ?
    WHERE student_id = ? AND date = ?
    """, (time_now, student_id, today))

    conn.commit()
    conn.close()


# ================================================================
#  PERIOD-WISE ATTENDANCE SYSTEM
# ================================================================

def get_current_period(now_time=None):
    """Return current period number (1-6) or None if outside all periods."""
    t = now_time or now_ist().time()
    for pnum, (sh, sm, eh, em) in PERIODS.items():
        start = time(sh, sm)
        end = time(eh, em)
        if start <= t < end:
            return pnum
    return None


def get_period_status(period_num, capture_time_str):
    """
    Given a period number and a capture time string (HH:MM:SS or HH:MM),
    return (status, value):
      - ('present', 1.0)  always, as soon as they are captured in the period.
    """
    return ('present', 1.0)


def init_today_periods(all_students):
    """Insert 6 absent rows per student for today (one per period)."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    today = now_ist().strftime("%Y-%m-%d")

    for student in all_students:
        for pnum in PERIODS:
            cursor.execute("""
            INSERT OR IGNORE INTO period_attendance
                (student_id, date, period, status, value, first_seen_time)
            VALUES (?, ?, ?, 'absent', 0.0, NULL)
            """, (student, today, pnum))

    conn.commit()
    conn.close()


def mark_period_present(student_id, period_num=None):
    """
    Mark a student's period attendance based on current time.
    Auto-detects the current period if period_num is None.
    Returns (period_num, status, value) or None if no active period.
    """
    now = now_ist()
    today = now.strftime("%Y-%m-%d")
    time_now = now.strftime("%H:%M:%S")

    if period_num is None:
        period_num = get_current_period(now.time())
    if period_num is None:
        return None

    status, value = get_period_status(period_num, time_now)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Only update if not already marked present (don't downgrade)
    cursor.execute("""
    SELECT value FROM period_attendance
    WHERE student_id=? AND date=? AND period=?
    """, (student_id, today, period_num))
    row = cursor.fetchone()

    if row is None:
        # Row doesn't exist yet — insert
        cursor.execute("""
        INSERT INTO period_attendance
            (student_id, date, period, status, value, first_seen_time)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (student_id, today, period_num, status, value, time_now))
    elif row[0] < value:
        # Only upgrade (don't downgrade from present to late)
        cursor.execute("""
        UPDATE period_attendance
        SET status=?, value=?, first_seen_time=?
        WHERE student_id=? AND date=? AND period=?
        """, (status, value, time_now, student_id, today, period_num))

    conn.commit()
    conn.close()
    return (period_num, status, value)


# ================================================================
#  BACKFILL MISSING WORKING DAYS WITH ABSENT PERIOD RECORDS
# ================================================================

def backfill_student_periods(student_id):
    """
    Fill in absent period_attendance records for all past working days
    that are missing for this student. Uses the student's OWN earliest
    date so late-enrolled students are not penalised with pre-enrollment absents.
    """
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Find the earliest date THIS student has in either table
    cur.execute("SELECT MIN(date) FROM period_attendance WHERE student_id=?", (student_id,))
    d1 = cur.fetchone()[0]
    cur.execute("SELECT MIN(date) FROM attendance WHERE student_id=?", (student_id,))
    d2 = cur.fetchone()[0]

    dates = [d for d in [d1, d2] if d]
    if not dates:
        conn.close()
        return

    start = datetime.strptime(min(dates), "%Y-%m-%d").date()
    end = now_ist().date()

    current = start
    while current <= end:
        ds = current.strftime("%Y-%m-%d")
        if is_working_day(ds):
            cur.execute(
                "SELECT COUNT(*) FROM period_attendance WHERE student_id=? AND date=?",
                (student_id, ds)
            )
            if cur.fetchone()[0] == 0:
                for pnum in PERIODS:
                    cur.execute("""
                        INSERT OR IGNORE INTO period_attendance
                            (student_id, date, period, status, value, first_seen_time)
                        VALUES (?, ?, ?, 'absent', 0.0, NULL)
                    """, (student_id, ds, pnum))
        current += timedelta(days=1)

    conn.commit()
    conn.close()


def backfill_all_students():
    """Backfill missing working days for every student in the users table."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT user_id FROM users WHERE role='student'")
    student_ids = [r[0] for r in cur.fetchall()]
    conn.close()
    for sid in student_ids:
        backfill_student_periods(sid)
