# Campus Connect — Flask + SQLite REST API

**Integrated Student Enrollment and Information System**
Laboratory 3 (Student Course Management API) + Laboratory 4 (Student Information Portal) combined into one system.

This folder is the **backend only**. The Campus Connect frontend (dashboard, tables, forms) is a
separate web app that talks to this API over HTTP with JSON.

```
Frontend (browser)  ──HTTP/JSON──▶  Flask REST API  ──SQL──▶  SQLite (database.db)
```

---

## 1. What is inside

| File | Purpose |
| --- | --- |
| `app.py` | The whole backend: Flask app, REST endpoints, SQLite connection, table creation and sample data. |
| `database.db` | The SQLite database. **Created automatically** the first time `app.py` runs. |
| `requirements.txt` | The Python packages the project needs (`Flask`, `flask-cors`, `gunicorn`). |
| `run.bat` | Windows one-click setup: creates a virtual environment, installs requirements, starts the server. |
| `start.bat` | Windows quick start once `run.bat` has been run at least once. |
| `render.yaml` | Optional Render blueprint (service + persistent disk). |
| `.gitignore` | Keeps `venv/`, `__pycache__/` and `database.db` out of GitHub. Rename `gitignore.txt` to `.gitignore`. |
| `templates/` | Small browser pages (`/`, `/students`, `/courses`, `/enrollment`, `/announcements`) that read the API. |
| `static/css/style.css` | Styling for those browser pages. |
| `static/javascript/script.js` | Fetches data from the REST API and fills the tables. |
| `screenshots/` | Put your laboratory screenshots here. |

---

## 2. Run it on Windows (recommended for the laboratory)

1. Install **Python 3.10 or newer** from <https://python.org>. During setup tick **“Add Python to PATH”**.
2. Put this folder anywhere, for example `C:\Campus-Connect`.
3. Double-click **`run.bat`**.
   * The first run creates `venv\` and installs Flask (it needs internet).
   * It then starts the server and prints:
     ```
     Campus Connect API running on http://127.0.0.1:5000/api
     Database file: C:\Campus-Connect\database.db
     ```
4. Open <http://127.0.0.1:5000> — you should see **“Connected to the Flask API”**.
5. Leave that window open while you use the frontend. Close it (or press `CTRL+C`) to stop the server.

Next time you only need **`start.bat`**.

### Run it on macOS / Linux

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

---

## 3. Database

SQLite file: `database.db` (created on first run, seeded with fictional sample records).

| Table | Important columns |
| --- | --- |
| `students` | `id` (primary key), `student_number` (unique), `first_name`, `last_name`, `email`, `program`, `year_level`, `contact_number` |
| `courses` | `id` (primary key), `course_code` (unique), `course_name`, `department`, `capacity`, `description` |
| `enrollments` | `id` (primary key), `student_id` → students, `course_id` → courses, `enrollment_date`, `status` |
| `announcements` | `id` (primary key), `title`, `content`, `author`, `date_posted` |
| `users` | `id`, `username`, `password_hash`, `role` — reserved for the registrar login requirement |

* `enrollments.student_id` and `enrollments.course_id` are **foreign keys** with `ON DELETE CASCADE`,
  so deleting a student also removes that student's enrollment rows.
* Deleting `database.db` and restarting the server rebuilds and reseeds the database.

---

## 4. REST API reference

Base URL: `http://127.0.0.1:5000/api` — all requests and responses are JSON.

| Method | Endpoint | Body / notes |
| --- | --- | --- |
| GET | `/health` | `{ "status": "ok", "database": "connected" }` |
| GET | `/students` | List of students |
| GET | `/students/<id>` | One student, `404` if missing |
| POST | `/students` | `student_number, first_name, last_name, email, program, year_level, contact_number` |
| PUT | `/students/<id>` | Any of the fields above |
| DELETE | `/students/<id>` | `{ "success": true }` |
| GET | `/courses` | List of courses |
| GET | `/courses/<id>` | One course |
| POST | `/courses` | `course_code, course_name, department, capacity, description` |
| PUT | `/courses/<id>` | Any of the fields above |
| DELETE | `/courses/<id>` | `{ "success": true }` |
| GET | `/enrollments` | Enrollment rows **joined** with student and course names |
| POST | `/enrollments` | `student_id, course_id, enrollment_date, status` |
| PUT | `/enrollments/<id>` | `status` (`Pending`, `Approved`, `Rejected`, `Cancelled`) or `enrollment_date` |
| DELETE | `/enrollments/<id>` | `{ "success": true }` |
| GET | `/announcements` | Newest first |
| POST | `/announcements` | `title, content, author, date_posted` |
| PUT | `/announcements/<id>` | Any of the fields above |
| DELETE | `/announcements/<id>` | `{ "success": true }` |

**Errors** always come back as `{ "error": "message" }` with a real HTTP status code:

| Status | Meaning |
| --- | --- |
| `400` | Missing or invalid field |
| `404` | Record does not exist |
| `409` | Duplicate student ID, duplicate course code, or the student is already enrolled in that course |

Quick test in PowerShell:

```powershell
Invoke-RestMethod http://127.0.0.1:5000/api/students | Format-Table
```

---

## 5. Connect the frontend

1. Open the Campus Connect frontend.
2. Go to **API Settings** in the sidebar.
3. Paste the API base URL — `http://127.0.0.1:5000/api` for local development — and press **Save & test**.
4. The status pill in the header turns green (**API connected**) and every screen now reads and writes SQLite.

If it stays red, the Flask window is closed, the URL is wrong, or the port is not 5000.

---

## 6. Deploy to Render

1. Push this folder to GitHub (see below).
2. In Render: **New → Web Service**, pick the repository.
3. **Build command:** `pip install -r requirements.txt`
4. **Start command:** `gunicorn app:app`
5. **Environment variables:**
   * `PYTHON_VERSION` = `3.11.9`
   * `DATABASE_PATH` = `/data/database.db`
6. **Disk (important):** add a persistent disk, name `campus-connect-data`, mount path `/data`, 1 GB.
   Render's own filesystem is temporary — without a disk, `database.db` is wiped on every deploy.
   *Persistent disks require a paid instance type; the free plan always starts with an empty database.*
7. Deploy, then open `https://YOUR-SERVICE.onrender.com/api/health`. It must return `"status": "ok"`.
8. Copy `https://YOUR-SERVICE.onrender.com/api` into the frontend's **API Settings**.

`localhost` will **not** work after deployment — the frontend must use the public Render URL.

---

## 7. Upload to GitHub

```bash
cd Campus-Connect
git init
git add .
git commit -m "Campus Connect Flask API with SQLite"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/campus-connect-api.git
git push -u origin main
```

* Rename `gitignore.txt` to `.gitignore` first so `venv/` and `database.db` are never uploaded.
* Never commit passwords, secret keys or `.env` files.
* To update later: `git add . && git commit -m "describe the change" && git push`.

---

## 8. Why this project combines Lab 3 and Lab 4

| Laboratory | What it contributed | Where it lives now |
| --- | --- | --- |
| **Lab 3** — Student Course Management API | The courses table and the course CRUD endpoints | `courses` table + `/api/courses` endpoints |
| **Lab 4** — Campus Connect portal | Student records, announcements, the dashboard idea | `students`, `announcements` tables + `/api/students`, `/api/announcements` |
| **New in this integration** | Enrollment: the feature that connects a student to a course | `enrollments` table + `/api/enrollments` |

The enrollments table is the *join* between the two laboratories: it stores a `student_id`
(Lab 4) and a `course_id` (Lab 3), which is why one integrated system can answer
“which courses is this student taking?” in a single request.

---

## 9. Testing checklist

| # | Action | Expected result |
| --- | --- | --- |
| 1 | Open the frontend dashboard | Four cards show totals; the header pill is green |
| 2 | Add a student | Row appears in Students; `database.db` gains a row |
| 3 | Add a course | Row appears in Courses |
| 4 | Edit a course | The changed values stay after refresh |
| 5 | Delete a course | Row disappears |
| 6 | Enroll a student | Enrollment row with status `Pending` |
| 7 | Enroll the same student twice | Red error: “already enrolled” (HTTP 409) |
| 8 | Approve the enrollment | Status badge turns green |
| 9 | Create an announcement | It appears on the dashboard |
| 10 | Stop the Flask server, then click Refresh | Red **API offline** state with an error message — no fake success |
