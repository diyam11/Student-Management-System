
from pathlib import Path
import sqlite3

from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

# Keep the existing database in the project directory.
DB_PATH = Path(__file__).resolve().parent / "students.db"


def connect_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    conn.execute("""
        CREATE TABLE IF NOT EXISTS students (
            student_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE COLLATE NOCASE,
            course TEXT NOT NULL,
            marks REAL NOT NULL CHECK(marks >= 0 AND marks <= 100)
        )
    """)

    return conn


def validate_student(data):
    name = str(data.get("name", "")).strip()
    email = str(data.get("email", "")).strip()
    course = str(data.get("course", "")).strip()

    try:
        marks = float(data.get("marks"))
    except (TypeError, ValueError):
        return None, "Enter valid marks."

    if not name or not email or not course:
        return None, "All fields are required."

    if len(name) > 100:
        return None, "Name must not exceed 100 characters."

    if len(email) > 150:
        return None, "Email must not exceed 150 characters."

    if "@" not in email or "." not in email.rsplit("@", 1)[-1]:
        return None, "Enter a valid email address."

    if not 0 <= marks <= 100:
        return None, "Marks must be between 0 and 100."

    return {
        "name": name,
        "email": email,
        "course": course,
        "marks": marks
    }, None


@app.route("/")
def home():
    return render_template("index.html")


@app.get("/api/students")
def get_students():
    search = request.args.get("search", "").strip()
    pattern = f"%{search}%"

    with connect_db() as conn:
        rows = conn.execute("""
            SELECT student_id, name, email, course, marks
            FROM students
            WHERE name LIKE ?
               OR email LIKE ?
               OR course LIKE ?
            ORDER BY student_id DESC
        """, (pattern, pattern, pattern)).fetchall()

    return jsonify([dict(row) for row in rows])


@app.get("/api/students/<int:student_id>")
def get_student(student_id):
    with connect_db() as conn:
        row = conn.execute("""
            SELECT student_id, name, email, course, marks
            FROM students
            WHERE student_id = ?
        """, (student_id,)).fetchone()

    if row is None:
        return jsonify({"error": "Student not found."}), 404

    return jsonify(dict(row))


@app.post("/api/students")
def add_student():
    data = request.get_json(silent=True) or {}

    student, error = validate_student(data)

    if error:
        return jsonify({"error": error}), 400

    try:
        with connect_db() as conn:
            cursor = conn.execute("""
                INSERT INTO students (name, email, course, marks)
                VALUES (?, ?, ?, ?)
            """, (
                student["name"],
                student["email"],
                student["course"],
                student["marks"]
            ))

            new_id = cursor.lastrowid

        return jsonify({
            "message": "Student added successfully.",
            "student_id": new_id
        }), 201

    except sqlite3.IntegrityError:
        return jsonify({
            "error": "That email address already exists."
        }), 409


@app.put("/api/students/<int:student_id>")
def update_student(student_id):
    data = request.get_json(silent=True) or {}

    student, error = validate_student(data)

    if error:
        return jsonify({"error": error}), 400

    try:
        with connect_db() as conn:
            existing = conn.execute("""
                SELECT student_id
                FROM students
                WHERE student_id = ?
            """, (student_id,)).fetchone()

            if existing is None:
                return jsonify({
                    "error": "Student not found."
                }), 404

            conn.execute("""
                UPDATE students
                SET name = ?,
                    email = ?,
                    course = ?,
                    marks = ?
                WHERE student_id = ?
            """, (
                student["name"],
                student["email"],
                student["course"],
                student["marks"],
                student_id
            ))

        return jsonify({
            "message": "Student updated successfully."
        })

    except sqlite3.IntegrityError:
        return jsonify({
            "error": "That email address is already used by another student."
        }), 409


@app.delete("/api/students/<int:student_id>")
def delete_student(student_id):
    with connect_db() as conn:
        cursor = conn.execute("""
            DELETE FROM students
            WHERE student_id = ?
        """, (student_id,))

        deleted = cursor.rowcount

    if deleted == 0:
        return jsonify({
            "error": "Student not found."
        }), 404

    return jsonify({
        "message": "Student deleted successfully."
    })


@app.get("/api/analytics")
def analytics():
    with connect_db() as conn:
        summary = conn.execute("""
            SELECT
                COUNT(*) AS total_students,
                ROUND(COALESCE(AVG(marks), 0), 2) AS average_marks,
                ROUND(COALESCE(MAX(marks), 0), 2) AS highest_marks,
                COUNT(DISTINCT course) AS total_courses
            FROM students
        """).fetchone()

        courses = conn.execute("""
            SELECT
                course,
                COUNT(*) AS student_count,
                ROUND(AVG(marks), 2) AS average_marks
            FROM students
            GROUP BY course
            ORDER BY course
        """).fetchall()

    return jsonify({
        "summary": dict(summary),
        "courses": [dict(row) for row in courses]
    })


if __name__ == "__main__":
    with connect_db():
        pass

    app.run(debug=True)
