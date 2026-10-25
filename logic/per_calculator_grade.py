# per_calculator_grade.py

def _percent(page, entry_text, key, name):
    """Turn a raw score and its 'out of' value into a 0-100 percentage."""
    raw = float(entry_text)
    max_entry = getattr(page, "percal_max_entries", {}).get(key)
    max_text = max_entry.get().strip() if max_entry else "100"
    maximum = float(max_text) if max_text else 100.0

    if maximum <= 0:
        raise ValueError(f"{name}: 'out of' must be greater than 0.")
    if raw > maximum:
        raise ValueError(f"{name}: score cannot be higher than {maximum:g}.")
    return round(raw / maximum * 100, 2)


def per_calculate_grade(page):
    """
    Weighted period grade (each score is converted to a percentage first):
    - Written Works: 30%
    - Quiz / Performance Task: 40%
    - Periodical Exam: 30%
    """
    try:
        written_raw = page.written_works.get().strip()
        quiz_raw = page.quiz_ptask.get().strip()
        exam_raw = page.exam.get().strip()

        if not written_raw or not quiz_raw or not exam_raw:
            return {"error": "Please enter values for all grade fields."}

        written = _percent(page, written_raw, "written", "Written Works")
        quiz = _percent(page, quiz_raw, "quiz", "Quiz / PTask")
        exam = _percent(page, exam_raw, "exam", "Exam")

        total = round(written * 0.30 + quiz * 0.40 + exam * 0.30, 2)

        return {
            "written": written,
            "quiz": quiz,
            "exam": exam,
            "total": total,
            "error": None,
        }

    except ValueError as e:
        msg = str(e)
        if "could not convert" in msg:
            msg = "Please enter valid numeric values for all grades."
        return {"error": msg}