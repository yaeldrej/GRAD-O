import os
from pathlib import Path
import bcrypt
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor
from core.subjects_data import CATEGORIZED_DEFAULT_SUBJECTS
from core.config import SUBJECT_GROUPS

# Load environment variables
load_dotenv()

# Absolute path to .env in the same folder as this script
BASE_DIR = Path(__file__).resolve().parent
env_path = BASE_DIR / "database.env"

if not env_path.exists():
    print(f"CRITICAL ERROR: Could not find .env file at {env_path}")
else:
    load_dotenv(dotenv_path=env_path, override=True)

def get_db_connection():
    """Establish connection to PostgreSQL."""
    try:
        connection = psycopg2.connect(
            host=os.getenv("DB_HOST"),
            database=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            port=int(os.getenv("DB_PORT")),
        )
        return connection
    except Exception as error:
        print(f"Error connecting to database: {error}")
        return None


# STUDENT DATABASE FUNCTIONS
def add_person(
    student_number,
    first_name,
    middle_name,
    last_name,
    phinmaed_email,
    username,
    password,
    role="student",
):
    """Insert a new user into the database and assign fixed categorized subjects for students."""
    conn = get_db_connection()
    if not conn:
        return False

    is_teacher = role == "teacher"
    target_table = "teacher" if is_teacher else "person"

    cursor = None
    try:
        hashed_password = bcrypt.hashpw(
            password.encode("utf-8"), bcrypt.gensalt()
        ).decode("utf-8")

        cursor = conn.cursor()

        if not is_teacher:
            # 1. Register student account
            query = """
                INSERT INTO person (
                    student_number, 
                    first_name, 
                    middle_name, 
                    last_name,
                    phinmaed_email,
                    username,
                    password_hash,
                    role
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
            """
            cursor.execute(
                query,
                (
                    student_number,
                    first_name,
                    middle_name,
                    last_name,
                    phinmaed_email,
                    username,
                    hashed_password,
                    role,
                ),
            )

            # 2. Automatically insert fixed default subjects for this student
            grade_query = """
                INSERT INTO student_grades (
                    student_number, year_level, semester, 
                    subject_code, subject_title, final_grade, remarks
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING;
            """

            for subj in CATEGORIZED_DEFAULT_SUBJECTS:
                cursor.execute(
                    grade_query,
                    (
                        student_number,
                        subj["year_level"],
                        subj["semester"],
                        subj["code"],
                        subj["title"],
                        0.00,
                        "Pending",
                    ),
                )
        else:
            query = """
                INSERT INTO teacher (
                    employee_number, 
                    first_name, 
                    middle_name, 
                    last_name,
                    phinmaed_email,
                    username,
                    password_hash
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s);
            """
            cursor.execute(
                query,
                (
                    student_number,
                    first_name,
                    middle_name,
                    last_name,
                    phinmaed_email,
                    username,
                    hashed_password,
                ),
            )

        conn.commit()
        print(
            f"Record successfully added to '{target_table}' with default subjects!"
        )
        return True
    except Exception as e:
        print(f"Error inserting into {target_table}: {e}")
        conn.rollback()
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def check_person(username, password, role="student"):
    """Verify credentials against the appropriate role table."""
    conn = get_db_connection()
    if not conn:
        return False

    is_teacher = role == "teacher"
    target_table = "teacher" if is_teacher else "person"
    password_column = "password_hash"

    cursor = None
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        query = f"SELECT {password_column} FROM {target_table} WHERE username = %s;"
        cursor.execute(query, (username,))
        result = cursor.fetchone()

        if (
            result
            and password_column in result
            and result[password_column]
        ):
            stored_hash = result[password_column].encode("utf-8")
            return bcrypt.checkpw(password.encode("utf-8"), stored_hash)

        return False
    except Exception as e:
        print(f"Error checking person in {target_table}: {e}")
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def get_student_grades_by_category(student_number, year_level, semester):
    """Fetch subjects and grades filtered specifically by Year Level and Semester."""
    conn = get_db_connection()
    if not conn:
        return []

    cursor = None
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        query = """
            SELECT 
                subject_code, 
                subject_title, 
                final_grade, 
                remarks
            FROM student_grades
            WHERE student_number = %s 
              AND year_level = %s 
              AND semester = %s;
        """
        cursor.execute(query, (student_number, year_level, semester))
        return cursor.fetchall()
    except Exception as e:
        print(f"Error fetching categorized grades: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def get_grades_by_student_number(student_number):
    """Fetch all grade records belonging strictly to one student number."""
    conn = get_db_connection()
    if not conn:
        return []

    cursor = None
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        query = """
            SELECT 
                p.first_name,
                p.last_name,
                g.student_number,
                g.year_level,
                g.semester,
                g.subject_code,
                g.subject_title,
                g.final_grade,
                g.remarks
            FROM student_grades g
            JOIN person p ON g.student_number = p.student_number
            WHERE g.student_number = %s
            ORDER BY g.year_level ASC, g.semester ASC;
        """
        cursor.execute(query, (student_number,))
        return cursor.fetchall()
    except Exception as e:
        print(f"Error fetching grades for {student_number}: {e}")
        return []
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# dropdown text -> (column suffix, max raw score, points it is worth)
# dropdown text -> column suffix
COMPONENTS = {
    "ACTIVITIES": "activities",
    "QUIZZES": "quizzes",
    "EXAMS": "exam",
    "ATTENDANCE": "attendance",
}

WRITTEN_WEIGHT = 0.30
QUIZ_WEIGHT = 0.40
EXAM_WEIGHT = 0.30
ACTIVITY_SHARE = 2 / 3      # inside Written
ATTENDANCE_SHARE = 1 / 3    # inside Written

def _subject_title(cursor, subject_code):
    """Reuse the title already stored for this subject, or fall back to the code."""
    cursor.execute(
        "SELECT subject_title FROM student_grades "
        "WHERE subject_code = %s AND subject_title IS NOT NULL LIMIT 1;",
        (subject_code,),
    )
    row = cursor.fetchone()
    return row[0] if row else subject_code

def save_activity_period_score(
    student_number,
    subject_code,
    period,
    component,
    score,
    year_level="1st Year",
    semester="1st Semester",
):
    """Save the raw score (0-100), then refresh the period grade."""
    period_key = {"Period 1": "p1", "Period 2": "p2"}.get(period, "p3")

    if component not in COMPONENTS:
        raise ValueError(f"Unknown assessment component: {component}")
    suffix = COMPONENTS[component]

    if not 0 <= score <= 100:
        raise ValueError("Score must be between 0 and 100.")
    target_column = f"{period_key}_{suffix}"

    conn = get_db_connection()
    if not conn:
        raise ConnectionError("Could not connect to the database.")

    cursor = None
    try:
        cursor = conn.cursor()
        title = _subject_title(cursor, subject_code)

        cursor.execute(
            f"""
            INSERT INTO student_grades (
                student_number, year_level, semester, subject_code,
                subject_title, {target_column}
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT ON CONSTRAINT unique_student_subject_categorized
            DO UPDATE SET {target_column} = EXCLUDED.{target_column};
            """,
            (student_number, year_level, semester, subject_code, title, score),
        )

        # Period grade = weighted sum, once all four parts are recorded
        w = {k: v[1] for k, v in COMPONENTS.items()}
                # Period grade = 30% written (activities + attendance)
        #              + 40% quiz/ptask + 30% exam, once all four exist
        cursor.execute(
            f"""
            UPDATE student_grades
            SET {period_key} = ROUND(
                (({period_key}_activities * %s::numeric
                  + {period_key}_attendance * %s::numeric) * %s::numeric)
              + ({period_key}_quizzes * %s::numeric)
              + ({period_key}_exam * %s::numeric), 2)
            WHERE student_number = %s AND year_level = %s
              AND semester = %s AND subject_code = %s
              AND {period_key}_activities IS NOT NULL
              AND {period_key}_attendance IS NOT NULL
              AND {period_key}_quizzes IS NOT NULL
              AND {period_key}_exam IS NOT NULL;
            """,
            (ACTIVITY_SHARE, ATTENDANCE_SHARE, WRITTEN_WEIGHT,
             QUIZ_WEIGHT, EXAM_WEIGHT,
             student_number, year_level, semester, subject_code),
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        if cursor:
            cursor.close()
        conn.close()

def get_history_grades(
    student_number, year_level="1st Year", semester="1st Semester"
):
    """Fetch the recorded P1, P2, P3 and overall grade of every subject in a term."""
    conn = get_db_connection()
    if not conn:
        return {}

    cursor = None
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(
            """
            SELECT subject_code, p1, p2, p3, final_grade
            FROM student_grades
            WHERE student_number = %s
              AND year_level = %s
              AND semester = %s;
            """,
            (student_number, year_level, semester),
        )
        rows = cursor.fetchall()
    finally:
        if cursor:
            cursor.close()
        conn.close()

    history_data = {}
    for row in rows:
        p1 = float(row["p1"] or 0)
        p2 = float(row["p2"] or 0)
        p3 = float(row["p3"] or 0)

        final = float(row["final_grade"] or 0)
        if final > 0:
            overall = final
        elif p1 and p2 and p3:
            # same weights as the calculator: 33% / 33% / 34%
            overall = round(p1 * 0.33 + p2 * 0.33 + p3 * 0.34, 2)
        else:
            overall = 0.0

        history_data[row["subject_code"]] = {
            "p1": p1,
            "p2": p2,
            "p3": p3,
            "overall": overall,
        }

    return history_data

# PASSWORD RESET FUNCTIONS
# Hard-coded mapping. Table/column names must never come from user input.
ROLE_TABLES = {
    "student": {"table": "person", "password_col": "password_hash"},
    "teacher": {"table": "teacher", "password_col": "password_hash"},  # "password_hash" if you rename
}


def get_email_by_username(username, role):
    """Return the account's email, or None if the username doesn't exist."""
    cfg = ROLE_TABLES.get(role)
    if not cfg:
        return None

    conn = get_db_connection()
    if not conn:
        raise ConnectionError("Could not connect to the database.")

    cursor = None
    try:
        cursor = conn.cursor()
        cursor.execute(
            f"SELECT phinmaed_email FROM {cfg['table']} WHERE username = %s;",
            (username,),
        )
        row = cursor.fetchone()
        return row[0] if row else None
    finally:
        if cursor:
            cursor.close()
        conn.close()


def update_password(username, new_password, role):
    """Hash and store a new password. Raises on failure."""
    cfg = ROLE_TABLES.get(role)
    if not cfg:
        raise ValueError(f"Unknown role: {role}")

    conn = get_db_connection()
    if not conn:
        raise ConnectionError("Could not connect to the database.")

    hashed = bcrypt.hashpw(
        new_password.encode("utf-8"), bcrypt.gensalt()
    ).decode("utf-8")

    cursor = None
    try:
        cursor = conn.cursor()
        cursor.execute(
            f"UPDATE {cfg['table']} SET {cfg['password_col']} = %s "
            f"WHERE username = %s;",
            (hashed, username),
        )
        if cursor.rowcount != 1:
            conn.rollback()
            raise RuntimeError("Account not found.")
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        if cursor:
            cursor.close()
        conn.close()

def get_student_number_by_username(username):
    """Return the student_number for a student username, or None."""
    conn = get_db_connection()
    if not conn:
        raise ConnectionError("Could not connect to the database.")
    cursor = None
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT student_number FROM person WHERE username = %s;",
            (username,),
        )
        row = cursor.fetchone()
        return row[0] if row else None
    finally:
        if cursor:
            cursor.close()
        conn.close()

def student_exists(student_number):
    conn = get_db_connection()
    if not conn:
        raise ConnectionError("Could not connect to the database.")
    cursor = None
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT 1 FROM person WHERE student_number = %s;",
            (student_number,),
        )
        return cursor.fetchone() is not None
    finally:
        if cursor:
            cursor.close()
        conn.close()



def get_current_term_index(student_number):
    """Return the student's current term position (0 if not found)."""
    conn = get_db_connection()
    if not conn:
        raise ConnectionError("Could not connect to the database.")
    cursor = None
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT current_term_index FROM person WHERE student_number = %s;",
            (student_number,),
        )
        row = cursor.fetchone()
        return row[0] if row else 0
    finally:
        if cursor:
            cursor.close()
        conn.close()

def get_student_name(student_number):
    """Return 'Last, First M.' for a student number, or None if not found."""
    conn = get_db_connection()
    if not conn:
        raise ConnectionError("Could not connect to the database.")
    cursor = None
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT first_name, middle_name, last_name "
            "FROM person WHERE student_number = %s;",
            (student_number,),
        )
        row = cursor.fetchone()
        if row is None:
            return None
        first, middle, last = row
        initial = f" {middle[0]}." if middle else ""
        return f"{last}, {first}{initial}"
    finally:
        if cursor:
            cursor.close()
        conn.close()

# ADD THIS FUNCTION to database.py (e.g. right after get_student_name)

def get_all_students():
    """Return [(student_number, 'Last, First M.'), ...] sorted by name."""
    conn = get_db_connection()
    if not conn:
        raise ConnectionError("Could not connect to the database.")
    cursor = None
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT student_number, first_name, middle_name, last_name "
            "FROM person ORDER BY last_name, first_name;"
        )
        students = []
        for number, first, middle, last in cursor.fetchall():
            initial = f" {middle[0]}." if middle else ""
            students.append((number, f"{last}, {first}{initial}"))
        return students
    finally:
        if cursor:
            cursor.close()
        conn.close()


# ----------------------------------------------------------------------
# SECTION PER YEAR LEVEL (15 sections per year, max 30 students each)
# ----------------------------------------------------------------------
SECTION_COUNT = 15       # sections per college year
SECTION_CAPACITY = 30    # students per section


def _ensure_section_table(cursor):
    """Create the table the first time it is needed."""
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS student_sections (
            student_number VARCHAR(25) NOT NULL
                REFERENCES person (student_number) ON DELETE CASCADE,
            year_level     TEXT        NOT NULL,
            section        SMALLINT    NOT NULL CHECK (section BETWEEN 1 AND 15),
            PRIMARY KEY (student_number, year_level)
        );
        """
    )


def get_section_counts(year_level):
    """Return {section_number: students_enrolled} for one year level."""
    conn = get_db_connection()
    if not conn:
        raise ConnectionError("Could not connect to the database.")
    cursor = None
    try:
        cursor = conn.cursor()
        _ensure_section_table(cursor)
        cursor.execute(
            "SELECT section, COUNT(*) FROM student_sections "
            "WHERE year_level = %s GROUP BY section;",
            (year_level,),
        )
        counts = {int(sec): int(n) for sec, n in cursor.fetchall()}
        conn.commit()
        return counts
    except Exception:
        conn.rollback()
        raise
    finally:
        if cursor:
            cursor.close()
        conn.close()


def get_student_section(student_number, year_level):
    """Return the student's section number (1-15) for a year, or None."""
    conn = get_db_connection()
    if not conn:
        raise ConnectionError("Could not connect to the database.")
    cursor = None
    try:
        cursor = conn.cursor()
        _ensure_section_table(cursor)
        cursor.execute(
            "SELECT section FROM student_sections "
            "WHERE student_number = %s AND year_level = %s;",
            (student_number, year_level),
        )
        row = cursor.fetchone()
        conn.commit()
        return row[0] if row else None
    except Exception:
        conn.rollback()
        raise
    finally:
        if cursor:
            cursor.close()
        conn.close()


def set_student_section(student_number, year_level, section):
    """Assign (or change) a student's section for one year level.
    Raises ValueError if the section already has 30 other students."""
    section = int(section)
    if not 1 <= section <= SECTION_COUNT:
        raise ValueError("Invalid section")
    conn = get_db_connection()
    if not conn:
        raise ConnectionError("Could not connect to the database.")
    cursor = None
    try:
        cursor = conn.cursor()
        _ensure_section_table(cursor)

        # One person at a time per section, so two sign-ups can't both
        # grab the last seat.
        cursor.execute(
            "SELECT pg_advisory_xact_lock(hashtext(%s));",
            (f"section:{year_level}:{section}",),
        )
        cursor.execute(
            "SELECT COUNT(*) FROM student_sections "
            "WHERE year_level = %s AND section = %s AND student_number <> %s;",
            (year_level, section, student_number),
        )
        if cursor.fetchone()[0] >= SECTION_CAPACITY:
            conn.rollback()
            raise ValueError(f"Section full ({SECTION_CAPACITY}/{SECTION_CAPACITY})")

        cursor.execute(
            """
            INSERT INTO student_sections (student_number, year_level, section)
            VALUES (%s, %s, %s)
            ON CONFLICT (student_number, year_level)
            DO UPDATE SET section = EXCLUDED.section;
            """,
            (student_number, year_level, section),
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        if cursor:
            cursor.close()
        conn.close()


def get_students_in_section(year_level, section):
    """Return [(student_number, 'Last, First M.'), ...] for one section of
    one year level, sorted by name."""
    conn = get_db_connection()
    if not conn:
        raise ConnectionError("Could not connect to the database.")
    cursor = None
    try:
        cursor = conn.cursor()
        _ensure_section_table(cursor)
        cursor.execute(
            """
            SELECT p.student_number, p.first_name, p.middle_name, p.last_name
            FROM student_sections s
            JOIN person p ON p.student_number = s.student_number
            WHERE s.year_level = %s AND s.section = %s
            ORDER BY p.last_name, p.first_name;
            """,
            (year_level, int(section)),
        )
        students = []
        for number, first, middle, last in cursor.fetchall():
            initial = f" {middle[0]}." if middle else ""
            students.append((number, f"{last}, {first}{initial}"))
        conn.commit()
        return students
    except Exception:
        conn.rollback()
        raise
    finally:
        if cursor:
            cursor.close()
        conn.close()


PERIOD_KEYS = {"Period 1": "p1", "Period 2": "p2", "Period 3": "p3"}

def get_student_profile(student_number):
    """Return the logged-in student's profile as a dict, or None if not found."""
    conn = get_db_connection()
    if not conn:
        raise ConnectionError("Could not connect to the database.")
    cursor = None
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(
            """
            SELECT first_name, middle_name, last_name,
                   phinmaed_email, student_number
            FROM person
            WHERE student_number = %s;
            """,
            (student_number,),
        )
        return cursor.fetchone()
    finally:
        if cursor:
            cursor.close()
        conn.close()


def update_student_profile(student_number, first_name, middle_name,
                           last_name, phinmaed_email):
    """Update the logged-in student's own profile. The student number itself
    is never changed here (it links the student to their grades)."""
    conn = get_db_connection()
    if not conn:
        raise ConnectionError("Could not connect to the database.")
    cursor = None
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE person
            SET first_name = %s, middle_name = %s, last_name = %s,
                phinmaed_email = %s
            WHERE student_number = %s;
            """,
            (first_name, middle_name, last_name, phinmaed_email,
             student_number),
        )
        if cursor.rowcount != 1:
            conn.rollback()
            raise RuntimeError("Account not found.")
        conn.commit()
    except psycopg2.IntegrityError:
        conn.rollback()
        raise ValueError("That email address is already used by another account.")
    except Exception:
        conn.rollback()
        raise
    finally:
        if cursor:
            cursor.close()
        conn.close()


def save_period_result(student_number, year_level, semester, subject_code,
                       period, written, quiz, exam, grade):
    """Save one period's scores and grade for one subject of one student."""
    key = PERIOD_KEYS[period]

    conn = get_db_connection()
    if not conn:
        raise ConnectionError("Could not connect to the database.")

    cursor = None
    try:
        cursor = conn.cursor()
        title = _subject_title(cursor, subject_code)
        cursor.execute(
            f"""
            INSERT INTO student_grades (
                student_number, year_level, semester, subject_code,
                subject_title,
                {key}_class_standing, {key}_quizzes, {key}_exam, {key}
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT ON CONSTRAINT unique_student_subject_categorized
            DO UPDATE SET
                {key}_class_standing = EXCLUDED.{key}_class_standing,
                {key}_quizzes        = EXCLUDED.{key}_quizzes,
                {key}_exam           = EXCLUDED.{key}_exam,
                {key}                = EXCLUDED.{key};
            """,
            (student_number, year_level, semester, subject_code, title,
             written, quiz, exam, grade),
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        if cursor:
            cursor.close()
        conn.close()

def get_period_components(student_number, year_level, semester,
                          subject_code, period):
    """Return the saved written / quiz / exam scores for one period,
    or None if the student has no row for that subject."""
    key = PERIOD_KEYS[period]

    conn = get_db_connection()
    if not conn:
        raise ConnectionError("Could not connect to the database.")

    cursor = None
    try:
        cursor = conn.cursor()
        cursor.execute(
            f"""
            SELECT {key}_activities, {key}_attendance,
                   {key}_quizzes, {key}_exam, {key}_class_standing
            FROM student_grades
            WHERE student_number = %s AND year_level = %s
              AND semester = %s AND subject_code = %s
            LIMIT 1;
            """,
            (student_number, year_level, semester, subject_code),
        )
        row = cursor.fetchone()
    finally:
        if cursor:
            cursor.close()
        conn.close()

    if row is None:
        return None

    activities, attendance, quizzes, exam, class_standing = (
        None if v is None else float(v) for v in row
    )

    if activities is not None and attendance is not None:
        written = activities * ACTIVITY_SHARE + attendance * ATTENDANCE_SHARE
    elif class_standing:          # skips both None and 0
        written = class_standing
    else:
        written = None            # Written is not complete yet

    return {"written": written, "quiz": quizzes, "exam": exam}

def set_current_term_index(student_number, index):
    """Teacher action: move a student to another term."""
    index = max(0, min(int(index), len(SUBJECT_GROUPS) - 1))
    conn = get_db_connection()
    if not conn:
        raise ConnectionError("Could not connect to the database.")
    cursor = None
    try:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE person SET current_term_index = %s WHERE student_number = %s;",
            (index, student_number),
        )
        if cursor.rowcount != 1:
            conn.rollback()
            raise RuntimeError("Student not found.")
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        if cursor:
            cursor.close()
        conn.close()

def save_final_grade(student_number, year_level, semester,
                     subject_code, final_grade, remarks):
    """Save the calculator's final grade for one subject."""
    conn = get_db_connection()
    if not conn:
        raise ConnectionError("Could not connect to the database.")
    cursor = None
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO student_grades (
                student_number, year_level, semester,
                subject_code, final_grade, remarks
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT ON CONSTRAINT unique_student_subject_categorized
            DO UPDATE SET final_grade = EXCLUDED.final_grade,
                          remarks = EXCLUDED.remarks;
            """,
            (student_number, year_level, semester,
             subject_code, final_grade, remarks),
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        if cursor:
            cursor.close()
        conn.close()


def clear_final_grade(student_number, year_level, semester, subject_code):
    """Reset a subject back to Pending (same defaults as registration)."""
    conn = get_db_connection()
    if not conn:
        raise ConnectionError("Could not connect to the database.")
    cursor = None
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE student_grades
            SET final_grade = 0.00, remarks = 'Pending'
            WHERE student_number = %s AND year_level = %s
              AND semester = %s AND subject_code = %s;
            """,
            (student_number, year_level, semester, subject_code),
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        if cursor:
            cursor.close()
        conn.close()

def get_subject_period_grades(student_number, year_level, semester, subject_code):
    """Return {"p1": x, "p2": y, "p3": z} for ONE subject, read from the
    p1, p2 and p3 columns. 0.0 means nothing is recorded for that period."""
    empty = {"p1": 0.0, "p2": 0.0, "p3": 0.0}

    conn = get_db_connection()
    if not conn:
        return empty

    cursor = None
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(
            """
            SELECT p1, p2, p3
            FROM student_grades
            WHERE student_number = %s
              AND year_level = %s
              AND semester = %s
              AND subject_code = %s
            LIMIT 1;
            """,
            (student_number, year_level, semester, subject_code),
        )
        row = cursor.fetchone()
        if not row:
            return empty

        return {
            "p1": float(row["p1"] or 0),
            "p2": float(row["p2"] or 0),
            "p3": float(row["p3"] or 0),
        }
    except Exception as e:
        print(f"Error fetching subject period grades: {e}")
        return empty
    finally:
        if cursor:
            cursor.close()
        conn.close()

def save_subject_period_grades(student_number, year_level, semester,
                               subject_code, p1, p2, p3,
                               final_grade=None, remarks=None):
    """Save P1/P2/P3 for one subject of one student.
    A blank period is passed as None and stored as NULL.
    final_grade/remarks are only touched when final_grade is given."""
    conn = get_db_connection()
    if not conn:
        raise ConnectionError("Could not connect to the database.")

    cursor = None
    try:
        cursor = conn.cursor()
        title = _subject_title(cursor, subject_code)

        update_sql = "p1 = EXCLUDED.p1, p2 = EXCLUDED.p2, p3 = EXCLUDED.p3"
        if final_grade is None:
            insert_final, insert_remarks = 0.00, "Pending"
        else:
            insert_final, insert_remarks = final_grade, remarks
            update_sql += (", final_grade = EXCLUDED.final_grade"
                           ", remarks = EXCLUDED.remarks")

        cursor.execute(
            f"""
            INSERT INTO student_grades (
                student_number, year_level, semester, subject_code,
                subject_title, p1, p2, p3, final_grade, remarks
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT ON CONSTRAINT unique_student_subject_categorized
            DO UPDATE SET {update_sql};
            """,
            (student_number, year_level, semester, subject_code, title,
             p1, p2, p3, insert_final, insert_remarks),
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        if cursor:
            cursor.close()
        conn.close()

def get_employee_number_by_username(username):
    """Return the employee_number for a teacher username, or None."""
    conn = get_db_connection()
    if not conn:
        raise ConnectionError("Could not connect to the database.")
    cursor = None
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT employee_number FROM teacher WHERE username = %s;",
            (username,),
        )
        row = cursor.fetchone()
        return row[0] if row else None
    finally:
        if cursor:
            cursor.close()
        conn.close()


def get_teacher_profile(employee_number):
    """Return the logged-in teacher's profile as a dict, or None if not found."""
    conn = get_db_connection()
    if not conn:
        raise ConnectionError("Could not connect to the database.")
    cursor = None
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(
            """
            SELECT first_name, middle_name, last_name,
                   phinmaed_email, employee_number
            FROM teacher
            WHERE employee_number = %s;
            """,
            (employee_number,),
        )
        return cursor.fetchone()
    finally:
        if cursor:
            cursor.close()
        conn.close()


def update_teacher_profile(employee_number, first_name, middle_name,
                           last_name, phinmaed_email):
    """Update the logged-in teacher's own profile. The employee number
    itself is never changed here."""
    conn = get_db_connection()
    if not conn:
        raise ConnectionError("Could not connect to the database.")
    cursor = None
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE teacher
            SET first_name = %s, middle_name = %s, last_name = %s,
                phinmaed_email = %s
            WHERE employee_number = %s;
            """,
            (first_name, middle_name, last_name, phinmaed_email,
             employee_number),
        )
        if cursor.rowcount != 1:
            conn.rollback()
            raise RuntimeError("Account not found.")
        conn.commit()
    except psycopg2.IntegrityError:
        conn.rollback()
        raise ValueError("That email address is already used by another account.")
    except Exception:
        conn.rollback()
        raise
    finally:
        if cursor:
            cursor.close()
        conn.close()

def test_connection():
    """Verify active database connection and print PostgreSQL version."""
    conn = get_db_connection()
    if not conn:
        print("Failed to establish a connection.")
        return False

    cursor = None
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        db_version = cursor.fetchone()
        print("Successfully connected to the database!")
        print(f"PostgreSQL version: {db_version[0]}")
        return True
    except Exception as e:
        print(f"Connection test failed: {e}")
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# Run the connection test
if __name__ == "__main__":
    test_connection()