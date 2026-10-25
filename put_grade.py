"""
put_grade.py  -  record a student's period scores in the database.

Run it from your project folder (same folder as database.py):

    python put_grade.py

It asks for the student number, the term, the subject, and the scores.
Press Enter to skip a score you don't want to change.
After this, the student sees the grades in the calculator when they pick
that subject.

Each period shown in the calculator = average of that period's
CLASS STANDING and EXAM (same rule as the Grade History page).
Tip: to make a period show exactly 85, enter 85 for both.
"""

from core.database import get_db_connection, student_exists
from core.subjects_data import CATEGORIZED_DEFAULT_SUBJECTS
from core.config import SUBJECT_GROUPS

# Column name -> label shown when asking. Fixed list, never user input.
SCORE_COLUMNS = [
    ("p1_class_standing", "Period 1 - Class Standing"),
    ("p1_exam", "Period 1 - Exam"),
    ("p2_class_standing", "Period 2 - Class Standing"),
    ("p2_exam", "Period 2 - Exam"),
    ("p3_class_standing", "Period 3 - Class Standing"),
    ("p3_exam", "Period 3 - Exam"),
]


def ask_choice(title, options):
    """Show a numbered list and return the chosen index."""
    print(f"\n{title}")
    for i, option in enumerate(options, start=1):
        print(f"  {i}. {option}")
    while True:
        answer = input("Enter number: ").strip()
        if answer.isdigit() and 1 <= int(answer) <= len(options):
            return int(answer) - 1
        print("  Invalid choice, try again.")


def ask_score(label):
    """Return a float 0-100, or None if the user presses Enter."""
    while True:
        answer = input(f"{label} (Enter to skip): ").strip()
        if answer == "":
            return None
        try:
            value = float(answer)
        except ValueError:
            print("  Please type a number.")
            continue
        if 0 <= value <= 100:
            return value
        print("  Score must be between 0 and 100.")


def subject_title_for(subject_code, year_level, semester):
    for subj in CATEGORIZED_DEFAULT_SUBJECTS:
        if (
            subj["code"] == subject_code
            and subj["year_level"] == year_level
            and subj["semester"] == semester
        ):
            return subj["title"]
    return None


def save_scores(student_number, year_level, semester, subject_code, scores):
    """Insert the subject row if missing, otherwise update only given scores."""
    provided = {col: val for col, val in scores.items() if val is not None}
    if not provided:
        return False

    title = subject_title_for(subject_code, year_level, semester)

    columns = ["student_number", "year_level", "semester", "subject_code", "subject_title"]
    values = [student_number, year_level, semester, subject_code, title]
    for col, val in provided.items():
        columns.append(col)
        values.append(val)

    placeholders = ", ".join(["%s"] * len(columns))
    updates = ", ".join(f"{col} = EXCLUDED.{col}" for col in provided)

    query = (
        f"INSERT INTO student_grades ({', '.join(columns)}) "
        f"VALUES ({placeholders}) "
        f"ON CONFLICT ON CONSTRAINT unique_student_subject_categorized "
        f"DO UPDATE SET {updates};"
    )

    conn = get_db_connection()
    if not conn:
        raise ConnectionError("Could not connect to the database.")

    cursor = None
    try:
        cursor = conn.cursor()
        cursor.execute(query, values)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        if cursor:
            cursor.close()
        conn.close()
    return True


def main():
    print("=== GRAD-O: put a student's grades ===")

    student_number = input("\nStudent number: ").strip()
    if not student_number:
        print("No student number entered.")
        return

    try:
        if not student_exists(student_number):
            print(f"No student with number '{student_number}' was found.")
            return
    except Exception as e:
        print(f"Database error: {e}")
        return

    term_names = list(SUBJECT_GROUPS.keys())
    term_name = term_names[ask_choice("Choose the term:", term_names)]
    subjects, year_level, semester = SUBJECT_GROUPS[term_name]

    subject_code = subjects[ask_choice("Choose the subject:", subjects)]

    print(f"\nEnter the scores for {subject_code} ({year_level}, {semester}):")
    scores = {col: ask_score(label) for col, label in SCORE_COLUMNS}

    if all(v is None for v in scores.values()):
        print("\nNo scores entered, nothing saved.")
        return

    print("\nAbout to save:")
    print(f"  Student : {student_number}")
    print(f"  Subject : {subject_code} ({year_level}, {semester})")
    for col, label in SCORE_COLUMNS:
        if scores[col] is not None:
            print(f"  {label}: {scores[col]:.2f}")

    if input("\nSave? (y/n): ").strip().lower() != "y":
        print("Cancelled.")
        return

    try:
        save_scores(student_number, year_level, semester, subject_code, scores)
    except Exception as e:
        print(f"Could not save: {e}")
        return

    print("\nSaved! The student will see it in the calculator.")


if __name__ == "__main__":
    main()