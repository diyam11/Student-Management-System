
import sqlite3
from pathlib import Path

# Keep the database in the same folder as this Python file
DB_PATH = Path(__file__).resolve().parent / "students.db"


# ---------------- DATABASE SETUP ----------------

def connect_db():
    return sqlite3.connect(DB_PATH)


def initialize_db():
    try:
        with connect_db() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS students (
                    student_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    email TEXT NOT NULL COLLATE NOCASE UNIQUE,
                    course TEXT NOT NULL,
                    marks REAL NOT NULL
                        CHECK (marks >= 0 AND marks <= 100)
                )
            """)
        print("Database initialized successfully.")
    except sqlite3.Error as e:
        print(f"Database initialization error: {e}")


# ---------------- INPUT VALIDATION ----------------

def read_marks():
    while True:
        try:
            marks = float(input("Enter marks (0-100): ").strip())
            if 0 <= marks <= 100:
                return marks
            print("Marks must be between 0 and 100.")
        except ValueError:
            print("Invalid input. Enter a number.")


def read_student_id(prompt):
    value = input(prompt).strip()
    if not value.isdigit() or int(value) <= 0:
        print("Please enter a valid positive student ID.")
        return None
    return int(value)


# ---------------- ADD STUDENT ----------------

def add_student():
    print("\n--- ADD STUDENT ---")

    name = input("Enter student name: ").strip()
    email = input("Enter email: ").strip().lower()
    course = input("Enter course: ").strip()

    if not name or not email or not course:
        print("Name, email, and course cannot be empty.")
        return

    marks = read_marks()

    try:
        with connect_db() as conn:
            cursor = conn.execute("""
                INSERT INTO students (name, email, course, marks)
                VALUES (?, ?, ?, ?)
            """, (name, email, course, marks))

            student_id = cursor.lastrowid

        print(f"Student added successfully! Student ID: {student_id}")

    except sqlite3.IntegrityError:
        print("Could not add student. Email may already exist.")
    except sqlite3.Error as e:
        print(f"Database error: {e}")


# ---------------- VIEW ALL STUDENTS (OPTION 2) ----------------

def list_students():
    print("\n--- ALL STUDENT RECORDS ---")

    try:
        with connect_db() as conn:
            rows = conn.execute("""
                SELECT student_id, name, email, course, marks
                FROM students
                ORDER BY student_id
            """).fetchall()

        if not rows:
            print("No student records found. Add a student first.")
            return

        print("-" * 95)
        print(
            f"{'ID':<6}{'Name':<22}{'Email':<30}"
            f"{'Course':<22}{'Marks':>10}"
        )
        print("-" * 95)

        for student_id, name, email, course, marks in rows:
            print(
                f"{student_id:<6}{name[:21]:<22}{email[:29]:<30}"
                f"{course[:21]:<22}{marks:>10.2f}"
            )

        print("-" * 95)
        print(f"Total records displayed: {len(rows)}")

    except sqlite3.Error as e:
        print(f"Error displaying students: {e}")


# ---------------- SEARCH STUDENT ----------------

def search_student():
    print("\n--- SEARCH STUDENT ---")
    term = input("Enter student ID or name: ").strip()

    if not term:
        print("Please enter an ID or name.")
        return

    try:
        with connect_db() as conn:
            if term.isdigit():
                rows = conn.execute("""
                    SELECT student_id, name, email, course, marks
                    FROM students
                    WHERE student_id = ?
                """, (int(term),)).fetchall()
            else:
                rows = conn.execute("""
                    SELECT student_id, name, email, course, marks
                    FROM students
                    WHERE name LIKE ? COLLATE NOCASE
                    ORDER BY name
                """, (f"%{term}%",)).fetchall()

        if not rows:
            print("No matching student found.")
            return

        for sid, name, email, course, marks in rows:
            print(f"\nStudent ID: {sid}")
            print(f"Name: {name}")
            print(f"Email: {email}")
            print(f"Course: {course}")
            print(f"Marks: {marks:.2f}")

    except sqlite3.Error as e:
        print(f"Search error: {e}")


# ---------------- UPDATE STUDENT ----------------

def update_student():
    print("\n--- UPDATE STUDENT ---")
    student_id = read_student_id("Enter student ID to update: ")

    if student_id is None:
        return

    try:
        with connect_db() as conn:
            student = conn.execute("""
                SELECT student_id, name, email, course, marks
                FROM students
                WHERE student_id = ?
            """, (student_id,)).fetchone()

        if not student:
            print("Student not found.")
            return

        print("Press Enter to keep the existing value.")

        name = input(f"Name [{student[1]}]: ").strip() or student[1]
        email = input(f"Email [{student[2]}]: ").strip().lower() or student[2]
        course = input(f"Course [{student[3]}]: ").strip() or student[3]

        marks_text = input(f"Marks [{student[4]}]: ").strip()

        if marks_text:
            try:
                marks = float(marks_text)
                if not 0 <= marks <= 100:
                    print("Marks must be between 0 and 100.")
                    return
            except ValueError:
                print("Invalid marks. Enter a number.")
                return
        else:
            marks = student[4]

        if not name or not email or not course:
            print("Name, email, and course cannot be empty.")
            return

        with connect_db() as conn:
            conn.execute("""
                UPDATE students
                SET name = ?, email = ?, course = ?, marks = ?
                WHERE student_id = ?
            """, (name, email, course, marks, student_id))

        print("Student record updated successfully.")

    except sqlite3.IntegrityError:
        print("Update failed. That email may already be in use.")
    except sqlite3.Error as e:
        print(f"Update error: {e}")


# ---------------- DELETE STUDENT ----------------

def delete_student():
    print("\n--- DELETE STUDENT ---")
    student_id = read_student_id("Enter student ID to delete: ")

    if student_id is None:
        return

    try:
        with connect_db() as conn:
            student = conn.execute("""
                SELECT name FROM students WHERE student_id = ?
            """, (student_id,)).fetchone()

            if not student:
                print("Student not found.")
                return

            confirm = input(
                f"Delete {student[0]} permanently? (y/n): "
            ).strip().lower()

            if confirm == "y":
                conn.execute("""
                    DELETE FROM students WHERE student_id = ?
                """, (student_id,))
                print("Student deleted successfully.")
            else:
                print("Deletion cancelled.")

    except sqlite3.Error as e:
        print(f"Delete error: {e}")


# ---------------- STATISTICS (OPTION 6) ----------------


def show_statistics():
    print("\nDEBUG: Option 6 selected")
    print("\n========== STUDENT STATISTICS ==========")

    try:
        conn = connect_db()
        cursor = conn.cursor()

        # Calculate overall statistics
        cursor.execute("""
            SELECT COUNT(*), AVG(marks), MIN(marks), MAX(marks)
            FROM students
        """)
        result = cursor.fetchone()

        total = result[0]
        average = result[1]
        lowest = result[2]
        highest = result[3]

        print(f"Total students: {total}")

        if total == 0:
            print("No student records found.")
            conn.close()
            return

        print(f"Average marks: {average:.2f}")
        print(f"Highest marks: {highest:.2f}")
        print(f"Lowest marks: {lowest:.2f}")

        # Calculate course-wise statistics
        cursor.execute("""
            SELECT course, COUNT(*), AVG(marks)
            FROM students
            GROUP BY course
            ORDER BY course
        """)
        courses = cursor.fetchall()

        print("\n--- COURSE-WISE STATISTICS ---")
        print("-" * 55)
        print(f"{'Course':<25}{'Students':>12}{'Avg Marks':>15}")
        print("-" * 55)

        for course, count, avg in courses:
            print(f"{course:<25}{count:>12}{avg:>15.2f}")

        print("-" * 55)
        conn.close()

    except Exception as e:
        print(f"ERROR in option 6: {type(e).__name__}: {e}")

    input("\nPress Enter to return to the menu...")



# ---------------- MAIN MENU ----------------

def main():
    initialize_db()

    while True:
        print("\n========================================")
        print("   STUDENT RECORD MANAGEMENT SYSTEM")
        print("========================================")
        print("1. Add Student")
        print("2. View All Students")
        print("3. Search Student")
        print("4. Update Student")
        print("5. Delete Student")
        print("6. View Statistics")
        print("0. Exit")
        print("========================================")

        choice = input("Enter your choice (0-6): ").strip()

        if choice == "1":
            add_student()
        elif choice == "2":
            print("DEBUG: Option 2 selected")
            list_students()
            print("DEBUG: Option 2 finished")
            input("Press Enter to continue...")
        elif choice == "3":
            search_student()
        elif choice == "4":
            update_student()
        elif choice == "5":
            delete_student()
        elif choice == "6":
            show_statistics()
        elif choice == "0":
            print("Thank you for using Student Record Management System!")
            break
        else:
            print("Invalid choice. Please enter a number from 0 to 6.")


if __name__ == "__main__":
    main()
