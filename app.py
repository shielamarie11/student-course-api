"""
Campus Connect - Integrated Student Enrollment and Information System
Flask + SQLite REST API  (Laboratory 3 + Laboratory 4 integration)

Run locally:
    python app.py

The REST API is served at:  http://127.0.0.1:5000/api
A small browser test console is served at: http://127.0.0.1:5000/
"""

import os
import sqlite3
from datetime import datetime, timezone

from flask import Flask, g, jsonify, render_template, request
from flask_cors import CORS

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_PATH = os.environ.get("DATABASE_PATH", os.path.join(BASE_DIR, "database.db"))

app = Flask(__name__)
# The Campus Connect frontend runs on a different origin (Base44, Vercel, localhost),
# so the browser needs permission to call these endpoints.
CORS(app)

STATUSES = ("Pending", "Approved", "Rejected", "Cancelled")

SCHEMA = """
CREATE TABLE IF NOT EXISTS students (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    student_number TEXT NOT NULL UNIQUE,
    first_name     TEXT NOT NULL,
    last_name      TEXT NOT NULL,
    email          TEXT NOT NULL,
    program        TEXT NOT NULL,
    year_level     TEXT NOT NULL,
    contact_number TEXT,
    created_date   TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS courses (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    course_code TEXT NOT NULL UNIQUE,
    course_name TEXT NOT NULL,
    department  TEXT NOT NULL,
    capacity    INTEGER NOT NULL DEFAULT 40,
    description TEXT,
    created_date TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS enrollments (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id      INTEGER NOT NULL,
    course_id       INTEGER NOT NULL,
    enrollment_date TEXT NOT NULL,
    status          TEXT NOT NULL DEFAULT 'Pending',
    FOREIGN KEY (student_id) REFERENCES students (id) ON DELETE CASCADE,
    FOREIGN KEY (course_id)  REFERENCES courses (id)  ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS announcements (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    title       TEXT NOT NULL,
    content     TEXT NOT NULL,
    author      TEXT NOT NULL,
    date_posted TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role          TEXT NOT NULL DEFAULT 'registrar',
    created_date  TEXT NOT NULL DEFAULT (datetime('now'))
);
"""

SEED_STUDENTS = [
    ("2024-00101", "Maria Clara", "Santos", "mc.santos@campusconnect.edu.ph", "BS Information Technology", "3rd Year", "0917 555 0142"),
    ("2024-00102", "Juan Miguel", "Dela Cruz", "jm.delacruz@campusconnect.edu.ph", "BS Computer Science", "2nd Year", "0918 555 0231"),
    ("2024-00103", "Ana Sofia", "Reyes", "as.reyes@campusconnect.edu.ph", "BS Information Systems", "4th Year", "0919 555 0388"),
    ("2024-00104", "Paolo Emmanuel", "Garcia", "pe.garcia@campusconnect.edu.ph", "BS Information Technology", "1st Year", "0920 555 0417"),
    ("2024-00105", "Bea Isabella", "Mendoza", "bi.mendoza@campusconnect.edu.ph", "BS Computer Science", "3rd Year", "0921 555 0564"),
    ("2024-00106", "Rafael Luis", "Torres", "rl.torres@campusconnect.edu.ph", "BS Information Systems", "2nd Year", "0922 555 0619"),
]

SEED_COURSES = [
    ("CS101", "Introduction to Computing", "Computer Studies", 45, "Foundations of computing, hardware and software concepts."),
    ("IT210", "Data Structures and Algorithms", "Information Technology", 40, "Arrays, lists, trees, graphs and algorithm analysis."),
    ("IS315", "Systems Integration and Architecture", "Information Systems", 35, "Enterprise integration patterns, APIs and middleware."),
    ("CS220", "Database Management Systems", "Computer Studies", 40, "Relational modelling, SQL and transaction management."),
    ("IT330", "Web Systems and Technologies", "Information Technology", 40, "Client-server web applications and REST services."),
    ("GE105", "Purposive Communication", "General Education", 50, "Academic and professional communication skills."),
]

SEED_ENROLLMENTS = [
    (1, 1, "2026-11-18", "Approved"),
    (1, 4, "2026-11-18", "Approved"),
    (2, 2, "2026-11-19", "Pending"),
    (3, 3, "2026-11-19", "Pending"),
    (4, 1, "2026-11-20", "Approved"),
    (5, 2, "2026-11-20", "Rejected"),
    (6, 5, "2026-11-21", "Approved"),
    (3, 4, "2026-11-21", "Cancelled"),
    (6, 3, "2026-11-22", "Pending"),
]

SEED_ANNOUNCEMENTS = [
    ("Enrollment for 2nd Semester Now Open", "Online enrollment for the second semester runs until December 12, 2026. Log in to your student portal to submit your course requests.", "Office of the Registrar", "2026-11-22"),
    ("Systems Integration Laboratory Schedule", "The IS315 laboratory section has been moved to Room 402, Computer Studies Building, every Tuesday and Thursday at 1:00 PM.", "College of Computer Studies", "2026-11-20"),
    ("Final Examination Period", "Final examinations will be held from December 15 to 19, 2026. Please check your enrollment records for your official subject list.", "Academic Affairs", "2026-11-17"),
    ("Library Extended Hours", "The university library will remain open until 9:00 PM on weekdays during the examination period.", "University Library", "2026-11-14"),
]

ENROLLMENT_QUERY = """
SELECT e.id, e.student_id, e.course_id, e.enrollment_date, e.status,
       s.student_number,
       s.first_name || ' ' || s.last_name AS student_name,
       c.course_code, c.course_name
FROM enrollments e
JOIN students s ON s.id = e.student_id
JOIN courses  c ON c.id = e.course_id
"""


# --------------------------------------------------------------------------- #
# Database helpers
# --------------------------------------------------------------------------- #
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


@app.teardown_appcontext
def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    """Create the tables (if missing) and add sample rows the first time."""
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.executescript(SCHEMA)

    if connection.execute("SELECT COUNT(*) AS total FROM students").fetchone()["total"] == 0:
        connection.executemany(
            "INSERT INTO students (student_number, first_name, last_name, email, program, year_level, contact_number) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            SEED_STUDENTS,
        )

    if connection.execute("SELECT COUNT(*) AS total FROM courses").fetchone()["total"] == 0:
        connection.executemany(
            "INSERT INTO courses (course_code, course_name, department, capacity, description) "
            "VALUES (?, ?, ?, ?, ?)",
            SEED_COURSES,
        )

    if connection.execute("SELECT COUNT(*) AS total FROM enrollments").fetchone()["total"] == 0:
        connection.executemany(
            "INSERT INTO enrollments (student_id, course_id, enrollment_date, status) VALUES (?, ?, ?, ?)",
            SEED_ENROLLMENTS,
        )

    if connection.execute("SELECT COUNT(*) AS total FROM announcements").fetchone()["total"] == 0:
        connection.executemany(
            "INSERT INTO announcements (title, content, author, date_posted) VALUES (?, ?, ?, ?)",
            SEED_ANNOUNCEMENTS,
        )

    connection.commit()
    connection.close()


def as_dict(row):
    return {key: row[key] for key in row.keys()}


def payload():
    return request.get_json(silent=True) or {}


def fail(message, status=400):
    return jsonify({"error": message}), status


def missing_fields(data, fields):
    empty = [field for field in fields if str(data.get(field, "")).strip() == ""]
    if empty:
        return "Missing required field(s): " + ", ".join(empty)
    return None


def find_row(table, row_id):
    row = get_db().execute("SELECT * FROM " + table + " WHERE id = ?", (row_id,)).fetchone()
    return as_dict(row) if row else None


def enrollment_by_id(enrollment_id):
    row = get_db().execute(ENROLLMENT_QUERY + " WHERE e.id = ?", (enrollment_id,)).fetchone()
    return as_dict(row) if row else None


def update_row(table, row_id, data, allowed):
    changes = {key: data[key] for key in allowed if key in data}
    if not changes:
        return fail("Nothing to update.")
    assignments = ", ".join(key + " = ?" for key in changes)
    values = list(changes.values()) + [row_id]
    get_db().execute("UPDATE " + table + " SET " + assignments + " WHERE id = ?", values)
    get_db().commit()
    return None


# --------------------------------------------------------------------------- #
# Health
# --------------------------------------------------------------------------- #
@app.get("/api/health")
def health():
    try:
        get_db().execute("SELECT 1").fetchone()
        return jsonify(
            {
                "status": "ok",
                "database": "connected",
                "engine": "sqlite",
                "time": datetime.now(timezone.utc).isoformat(),
            }
        )
    except Exception as exc:  # pragma: no cover - only when the file is unreadable
        return jsonify({"status": "error", "database": "disconnected", "error": str(exc)}), 500


# --------------------------------------------------------------------------- #
# Students  (GET / POST / PUT / DELETE)
# --------------------------------------------------------------------------- #
@app.get("/api/students")
def list_students():
    rows = get_db().execute("SELECT * FROM students ORDER BY student_number").fetchall()
    return jsonify([as_dict(row) for row in rows])


@app.get("/api/students/<int:student_id>")
def get_student(student_id):
    student = find_row("students", student_id)
    if not student:
        return fail("Student not found.", 404)
    return jsonify(student)


@app.post("/api/students")
def create_student():
    data = payload()
    problem = missing_fields(data, ["student_number", "first_name", "last_name", "email", "program", "year_level"])
    if problem:
        return fail(problem)
    try:
        cursor = get_db().execute(
            "INSERT INTO students (student_number, first_name, last_name, email, program, year_level, contact_number) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                data["student_number"].strip(),
                data["first_name"].strip(),
                data["last_name"].strip(),
                data["email"].strip(),
                data["program"].strip(),
                data["year_level"].strip(),
                str(data.get("contact_number", "")).strip(),
            ),
        )
        get_db().commit()
    except sqlite3.IntegrityError:
        return fail("That student ID already exists.", 409)
    return jsonify(find_row("students", cursor.lastrowid)), 201


@app.put("/api/students/<int:student_id>")
def update_student(student_id):
    if not find_row("students", student_id):
        return fail("Student not found.", 404)
    data = payload()
    problem = update_row(
        "students",
        student_id,
        data,
        ["student_number", "first_name", "last_name", "email", "program", "year_level", "contact_number"],
    )
    if problem:
        return problem
    return jsonify(find_row("students", student_id))


@app.delete("/api/students/<int:student_id>")
def delete_student(student_id):
    if not find_row("students", student_id):
        return fail("Student not found.", 404)
    get_db().execute("DELETE FROM students WHERE id = ?", (student_id,))
    get_db().commit()
    return jsonify({"success": True, "deleted_id": student_id})


# --------------------------------------------------------------------------- #
# Courses  (Laboratory 3 - Student Course Management API)
# --------------------------------------------------------------------------- #
@app.get("/api/courses")
def list_courses():
    rows = get_db().execute("SELECT * FROM courses ORDER BY course_code").fetchall()
    return jsonify([as_dict(row) for row in rows])


@app.get("/api/courses/<int:course_id>")
def get_course(course_id):
    course = find_row("courses", course_id)
    if not course:
        return fail("Course not found.", 404)
    return jsonify(course)


@app.post("/api/courses")
def create_course():
    data = payload()
    problem = missing_fields(data, ["course_code", "course_name", "department"])
    if problem:
        return fail(problem)
    try:
        cursor = get_db().execute(
            "INSERT INTO courses (course_code, course_name, department, capacity, description) VALUES (?, ?, ?, ?, ?)",
            (
                data["course_code"].strip().upper(),
                data["course_name"].strip(),
                data["department"].strip(),
                int(data.get("capacity") or 40),
                str(data.get("description", "")).strip(),
            ),
        )
        get_db().commit()
    except sqlite3.IntegrityError:
        return fail("That course code already exists.", 409)
    return jsonify(find_row("courses", cursor.lastrowid)), 201


@app.put("/api/courses/<int:course_id>")
def update_course(course_id):
    if not find_row("courses", course_id):
        return fail("Course not found.", 404)
    data = payload()
    if "course_code" in data:
        data["course_code"] = str(data["course_code"]).strip().upper()
    if "capacity" in data:
        data["capacity"] = int(data["capacity"] or 40)
    problem = update_row(
        "courses", course_id, data, ["course_code", "course_name", "department", "capacity", "description"]
    )
    if problem:
        return problem
    return jsonify(find_row("courses", course_id))


@app.delete("/api/courses/<int:course_id>")
def delete_course(course_id):
    if not find_row("courses", course_id):
        return fail("Course not found.", 404)
    get_db().execute("DELETE FROM courses WHERE id = ?", (course_id,))
    get_db().commit()
    return jsonify({"success": True, "deleted_id": course_id})


# --------------------------------------------------------------------------- #
# Enrollments (the feature that joins students and courses)
# --------------------------------------------------------------------------- #
@app.get("/api/enrollments")
def list_enrollments():
    rows = get_db().execute(ENROLLMENT_QUERY + " ORDER BY e.enrollment_date DESC, e.id DESC").fetchall()
    return jsonify([as_dict(row) for row in rows])


@app.get("/api/enrollments/<int:enrollment_id>")
def get_enrollment(enrollment_id):
    enrollment = enrollment_by_id(enrollment_id)
    if not enrollment:
        return fail("Enrollment not found.", 404)
    return jsonify(enrollment)


@app.post("/api/enrollments")
def create_enrollment():
    data = payload()
    problem = missing_fields(data, ["student_id", "course_id"])
    if problem:
        return fail(problem)

    student_id = int(data["student_id"])
    course_id = int(data["course_id"])
    status = data.get("status") or "Pending"

    if status not in STATUSES:
        return fail("Status must be one of: " + ", ".join(STATUSES))
    if not find_row("students", student_id):
        return fail("Student not found.", 404)
    if not find_row("courses", course_id):
        return fail("Course not found.", 404)

    duplicate = get_db().execute(
        "SELECT id FROM enrollments WHERE student_id = ? AND course_id = ? AND status != 'Cancelled'",
        (student_id, course_id),
    ).fetchone()
    if duplicate:
        return fail("This student is already enrolled in that course.", 409)

    cursor = get_db().execute(
        "INSERT INTO enrollments (student_id, course_id, enrollment_date, status) VALUES (?, ?, ?, ?)",
        (
            student_id,
            course_id,
            data.get("enrollment_date") or datetime.now(timezone.utc).date().isoformat(),
            status,
        ),
    )
    get_db().commit()
    return jsonify(enrollment_by_id(cursor.lastrowid)), 201


@app.put("/api/enrollments/<int:enrollment_id>")
def update_enrollment(enrollment_id):
    if not enrollment_by_id(enrollment_id):
        return fail("Enrollment not found.", 404)
    data = payload()
    if "status" in data and data["status"] not in STATUSES:
        return fail("Status must be one of: " + ", ".join(STATUSES))
    problem = update_row("enrollments", enrollment_id, data, ["status", "enrollment_date"])
    if problem:
        return problem
    return jsonify(enrollment_by_id(enrollment_id))


@app.delete("/api/enrollments/<int:enrollment_id>")
def delete_enrollment(enrollment_id):
    if not enrollment_by_id(enrollment_id):
        return fail("Enrollment not found.", 404)
    get_db().execute("DELETE FROM enrollments WHERE id = ?", (enrollment_id,))
    get_db().commit()
    return jsonify({"success": True, "deleted_id": enrollment_id})


# --------------------------------------------------------------------------- #
# Announcements (Laboratory 4 - Campus Connect portal)
# --------------------------------------------------------------------------- #
@app.get("/api/announcements")
def list_announcements():
    rows = get_db().execute("SELECT * FROM announcements ORDER BY date_posted DESC, id DESC").fetchall()
    return jsonify([as_dict(row) for row in rows])


@app.get("/api/announcements/<int:announcement_id>")
def get_announcement(announcement_id):
    announcement = find_row("announcements", announcement_id)
    if not announcement:
        return fail("Announcement not found.", 404)
    return jsonify(announcement)


@app.post("/api/announcements")
def create_announcement():
    data = payload()
    problem = missing_fields(data, ["title", "content", "author"])
    if problem:
        return fail(problem)
    cursor = get_db().execute(
        "INSERT INTO announcements (title, content, author, date_posted) VALUES (?, ?, ?, ?)",
        (
            data["title"].strip(),
            data["content"].strip(),
            data["author"].strip(),
            data.get("date_posted") or datetime.now(timezone.utc).date().isoformat(),
        ),
    )
    get_db().commit()
    return jsonify(find_row("announcements", cursor.lastrowid)), 201


@app.put("/api/announcements/<int:announcement_id>")
def update_announcement(announcement_id):
    if not find_row("announcements", announcement_id):
        return fail("Announcement not found.", 404)
    problem = update_row("announcements", announcement_id, payload(), ["title", "content", "author", "date_posted"])
    if problem:
        return problem
    return jsonify(find_row("announcements", announcement_id))


@app.delete("/api/announcements/<int:announcement_id>")
def delete_announcement(announcement_id):
    if not find_row("announcements", announcement_id):
        return fail("Announcement not found.", 404)
    get_db().execute("DELETE FROM announcements WHERE id = ?", (announcement_id,))
    get_db().commit()
    return jsonify({"success": True, "deleted_id": announcement_id})


# --------------------------------------------------------------------------- #
# Browser pages (a small test console that uses the same REST API)
# --------------------------------------------------------------------------- #
@app.get("/")
def page_index():
    return render_template("index.html")


@app.get("/students")
def page_students():
    return render_template("students.html")


@app.get("/courses")
def page_courses():
    return render_template("courses.html")


@app.get("/enrollment")
def page_enrollment():
    return render_template("enrollment.html")


@app.get("/announcements")
def page_announcements():
    return render_template("announcements.html")


@app.errorhandler(404)
def not_found(_error):
    if request.path.startswith("/api/"):
        return jsonify({"error": "Endpoint not found."}), 404
    return "Page not found", 404


init_db()

if __name__ == "__main__":
    print("Campus Connect API running on http://127.0.0.1:5000/api")
    print("Database file: " + DATABASE_PATH)
    app.run(host="127.0.0.1", port=5000, debug=True)