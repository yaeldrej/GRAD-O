def calculate_grades(page):

    p1_val = page.period1.get()
    p2_val = page.period2.get()
    p3_val = page.period3.get()

    try:
        v1 = float(p1_val) if p1_val.strip() else 0.0
        v2 = float(p2_val) if p2_val.strip() else 0.0
        v3 = float(p3_val) if p3_val.strip() else 0.0
    except ValueError:
        return {"error": "Please enter valid numbers."}

    total = (v1 * 0.33) + (v2 * 0.33) + (v3 * 0.34)
    return {"total": round(total, 2), "error": None}