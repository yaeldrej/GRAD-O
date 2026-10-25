#page_activity_logic
import tkinter as tk
from tkinter import messagebox


def calculate_activity_average(entries, target_entry=None):
    valid_scores = []

    for entry in entries:
        val = entry.get().strip()
        if val:
            try:
                valid_scores.append(float(val))
            except ValueError:
                messagebox.showerror(
                    "Invalid Input", "Please enter valid numerical scores."
                )
                return None

    if not valid_scores:
        messagebox.showwarning(
            "No Input", "Please enter at least one score."
        )
        return None

    avg = sum(valid_scores) / len(valid_scores)

    if target_entry:
        target_entry.delete(0, tk.END)
        target_entry.insert(0, f"{avg:.2f}")

    return avg


def calculate_overall_final_grade(category_scores):
    weights = {
        "Activity": 0.20,
        "Quiz/PTask": 0.30,
        "Exam": 0.40,
        "Attendance": 0.10,
    }

    final_grade = 0.0

    for category, weight in weights.items():
        score = category_scores.get(category, 0.0)
        final_grade += score * weight

    return final_grade