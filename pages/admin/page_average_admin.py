# page_average_admin.py
import tkinter as tk
from tkinter import ttk
from core.config import LIGHT_MODE, NON_GLOBAL_EQUIVALENCY_DATA, SUBJECT_GROUPS
from core.database import (
    get_student_grades_by_category,
    get_db_connection,
     get_current_term_index,
)
from core.subjects_data import CATEGORIZED_DEFAULT_SUBJECTS
from core import shared_results
class AveragePage(tk.Frame):

    def __init__(self, parent, student_number=None):
        super().__init__(parent, bg=LIGHT_MODE["window"])

        self.student_number = student_number
        # Register strict validation command on self
        vcmd = (self.register(self._validate_input), "%P")

        # Top Frame
        self.average_top_frame = tk.Frame(
            self,
            bg="#fff2bb",
            relief="solid",
            bd=1,
        )
        self.average_top_frame.pack(fill="x", padx=20, pady=20)

        self.average_title = tk.Label(
            self.average_top_frame,
            text="OVERALL WEIGHTED AVERAGE",
            font=("Titillium Web", 20, "bold"),
            bg="#fff2bb",
            fg="black",
        )
        self.average_title.pack(anchor="w", padx=170, pady=(15, 0))

        self.average_value = tk.Label(
            self.average_top_frame,
            text="--",
            font=("Titillium Web", 45, "bold"),
            bg="#fff2bb",
            fg="black",
        )
        self.average_value.pack(anchor="w", padx=170)

        self.average_status = tk.Label(
            self.average_top_frame,
            text="PASSED",
            font=("Titillium Web", 15),
            bg="white",
            fg="lime green",
            width=12,
        )
        self.average_status.pack(anchor="w", padx=170, pady=(0, 20))

        # Grade Component Frame (Top Right Inside Top Frame)
        self.component_frame = tk.Frame(
            self.average_top_frame,
            bg="#fff2bb",
            relief="solid",
            bd=1,
        )
        self.component_frame.place(
            relx=0.58, rely=0.12, relwidth=0.38, relheight=0.75
        )

        self.component_title = tk.Label(
            self.component_frame,
            text="GRADE COMPONENT",
            font=("Titillium Web", 12, "bold"),
            bg="white",
            fg="black",
            anchor="w",
        )
        self.component_title.pack(fill="x", padx=10, pady=5)

        self.written_label = tk.Label(
            self.component_frame,
            text="WRITTEN                         30%",
            font=("Titillium Web", 11, "bold"),
            bg="#fff2bb",
            fg="black",
            anchor="w",
        )
        self.written_label.pack(fill="x", padx=10, pady=5)

        self.quiz_label = tk.Label(
            self.component_frame,
            text="QUIZ/PTASK                    40%",
            font=("Titillium Web", 11, "bold"),
            bg="#fff2bb",
            fg="black",
            anchor="w",
        )
        self.quiz_label.pack(fill="x", padx=10, pady=5)

        self.exam_label = tk.Label(
            self.component_frame,
            text="PERIODICAL EXAM          30%",
            font=("Titillium Web", 11, "bold"),
            bg="#fff2bb",
            fg="black",
            anchor="w",
        )
        self.exam_label.pack(fill="x", padx=10, pady=5)

        # Subjects Frame (Bottom Left)
        self.subjects_frame = tk.Frame(
            self,
            bg="#fff2bb",
            relief="solid",
            bd=1,
        )
        self.subjects_frame.place(
            relx=0.02, rely=0.37, relwidth=0.62, relheight=0.58
        )

        self.subjects_title = tk.Label(
            self.subjects_frame,
            text="SUBJECTS",
            font=("Titillium Web", 17, "bold"),
            bg="#fff2bb",
            fg="black",
        )
        self.subjects_title.pack(anchor="w", padx=15, pady=10)

        self.term_dropdown = ttk.Combobox(
        self.subjects_frame,
        values=list(SUBJECT_GROUPS.keys()),
        state="readonly",
        font=("Arial", 11),
        width=20,
        )   
        
        self.term_dropdown.set("1st Year - 1st Sem")
        self.term_dropdown.place(relx=0.97, rely=0.02, anchor="ne")
        self.term_dropdown.bind(
            "<<ComboboxSelected>>", lambda e: self.refresh_table()
        )

        self.subjects_table_frame = tk.Frame(
            self.subjects_frame,
            bg=LIGHT_MODE["list"],
            relief="solid",
            bd=2,
        )
        self.subjects_table_frame.pack(
            fill="both", expand=True, padx=10, pady=5
        )

        self.average_scrollbar = tk.Scrollbar(
            self.subjects_table_frame, orient=tk.VERTICAL, width=16
        )
        self.average_scrollbar.pack(
            side=tk.LEFT, fill=tk.Y, padx=(3, 2), pady=8
        )

        self.subjects_table = ttk.Treeview(
            self.subjects_table_frame,
            columns=("Subject", "Final Grade", "Grade Point", "Remarks"),
            show="headings",
            yscrollcommand=self.average_scrollbar.set,
        )

        self.subjects_table.heading("Subject", text="SUBJECT")
        self.subjects_table.heading("Final Grade", text="FINAL GRADE")
        self.subjects_table.heading("Grade Point", text="GRADE POINT")
        self.subjects_table.heading("Remarks", text="REMARKS")

        for col in ("Subject", "Final Grade", "Grade Point", "Remarks"):
            self.subjects_table.column(col, width=150)

        self.subjects_table.pack(
            side=tk.RIGHT, fill="both", expand=True, padx=(0, 8), pady=8
        )
        self.average_scrollbar.config(command=self.subjects_table.yview)

        self.passed_label = tk.Label(
            self.subjects_frame,
            text="PASSED: 3",
            font=("Titillium Web", 12, "bold"),
            bg="#fff2bb",
            fg="black",
        )
        self.passed_label.place(relx=0.03, rely=0.88)

        self.failed_label = tk.Label(
            self.subjects_frame,
            text="FAILED: 1",
            font=("Titillium Web", 12, "bold"),
            bg="#fff2bb",
            fg="black",
        )
        self.failed_label.place(relx=0.20, rely=0.88)

        self.total_label = tk.Label(
            self.subjects_frame,
            text="TOTAL SUBJECTS: 4",
            font=("Titillium Web", 12, "bold"),
            bg="#fff2bb",
            fg="black",
        )
        self.total_label.place(relx=0.75, rely=0.88)

        # Grade Equivalency (Bottom Right)
        self.equivalency_frame = tk.Frame(
            self,
            bg="#fff2bb",
            relief="solid",
            bd=2,
        )
        self.equivalency_frame.place(
            relx=0.68, rely=0.37, relwidth=0.30, relheight=0.58
        )

        self.equivalency_title = tk.Label(
            self.equivalency_frame,
            text="GRADE EQUIVALENCY\nNON - GLOBAL SUBJECTS",
            font=("Titillium Web", 16, "bold"),
            bg="#fff2bb",
            fg="black",
            justify="center",
        )
        self.equivalency_title.pack(pady=15)

        self.equivalency_table = tk.Frame(
            self.equivalency_frame, bg=LIGHT_MODE["table"]
        )
        self.equivalency_table.pack(
            fill="both", expand=True, padx=0, pady=0
        )

        self.equivalency_table.grid_columnconfigure(0, weight=10)
        self.equivalency_table.grid_columnconfigure(1, weight=10)
        self.equivalency_table.grid_columnconfigure(2, weight=5)

        self.equivalency_entries = []
        for i in range(len(NON_GLOBAL_EQUIVALENCY_DATA)):
            row_entries = []
            self.equivalency_table.grid_rowconfigure(i, minsize=25)
            for j in range(3):
                e = tk.Entry(
                    self.equivalency_table,
                    font=("Titillium Web", 10, "bold"),
                    fg="black",
                    bg=LIGHT_MODE["table"],
                    relief="solid",
                    bd=1,
                    justify="left",
                    validate="key",
                    validatecommand=vcmd,
                )
                e.grid(row=i, column=j, sticky="nsew")

                # Temporarily turn off validation to populate initial values safely
                e.config(validate="none")
                val = str(NON_GLOBAL_EQUIVALENCY_DATA[i][j])
                e.insert(tk.END, val)
                e.config(validate="key")

                row_entries.append(e)
            self.equivalency_entries.append(row_entries)

        self.refresh_terms()

        shared_results.subscribe(
            on_save=self.add_saved_result,
            on_delete=self.clear_saved_result,
        )

    def _validate_input(self, P):
        """
        Validates input dynamically before it is drawn to the entry:
        - Allows empty string (backspace)
        - Allows single decimal point
        - Blocks letters and special symbols
        - Caps values at 99 (range: 0 to 99)
        """
        if P == "" or P == ".":
            return True

        try:
            val = float(P)
            # Maximum allowed value is 99 (and minimum 0)
            return 0 <= val <= 99
        except ValueError:
            # Rejects non-numeric text (letters, symbols, invalid floats)
            return False

    # Called by the calculator page when SAVE is pressed
    def add_saved_result(self, result):
        self.average_value.config(text=result["grade_point_text"])

        if result["status"] == "PASSED":
            self.average_status.config(text="PASSED", fg="lime green")
        else:
            self.average_status.config(text="FAILED", fg="red")

    # Called by the calculator page when DELETE is pressed
    def clear_saved_result(self, result):
        self.average_value.config(text="--")
        self.average_status.config(text="", fg="black")

    def calculate_grade_point(self, final_grade):
        if final_grade >= 94.8:
            return 1.00
        elif final_grade >= 89.2:
            return 1.25
        elif final_grade >= 83.6:
            return 1.50
        elif final_grade >= 78.0:
            return 1.75
        elif final_grade >= 72.4:
            return 2.00
        elif final_grade >= 66.8:
            return 2.25
        elif final_grade >= 61.2:
            return 2.50
        elif final_grade >= 55.6:
            return 2.75
        elif final_grade >= 50.0:
            return 3.00
        else:
            return 3.25


    def apply_theme(self, theme, ribbon_photo=None, ribbon_photo_white=None):
        self.configure(bg=theme["window"])

        if hasattr(self, "background_logo") and ribbon_photo and ribbon_photo_white:
            logo = (
                ribbon_photo_white
                if theme["window"] == "#1e1e1e"
                else ribbon_photo
            )
            self.background_logo.configure(bg=theme["window"], image=logo)

        if hasattr(self, "calculator_frame"):
            self.calculator_frame.configure(bg=theme["table"])

        if hasattr(self, "below_sep"):
            self.below_sep.configure(bg=theme["table"])
        if hasattr(self, "below_sep3"):
            self.below_sep3.configure(bg=theme["table"])

        if hasattr(self, "subject_label"):
            self.subject_label.configure(bg=theme["table"], fg=theme["text"])
        if hasattr(self, "enter_grades_label"):
            self.enter_grades_label.configure(bg=theme["table"], fg=theme["text"])
        if hasattr(self, "period1_text"):
            self.period1_text.configure(bg=theme["table"], fg=theme["text"])
        if hasattr(self, "period2_text"):
            self.period2_text.configure(bg=theme["table"], fg=theme["text"])
        if hasattr(self, "period3_text"):
            self.period3_text.configure(bg=theme["table"], fg=theme["text"])

        for entry in (
            getattr(self, "period1", None),
            getattr(self, "period2", None),
            getattr(self, "period3", None),
        ):
            if entry:
                entry.configure(
                    bg=theme["list"],
                    fg=theme["text"],
                    insertbackground=theme["text"],
                )

    def refresh_terms(self):
        terms = list(SUBJECT_GROUPS.keys())
        self.term_dropdown["values"] = terms
        if self.term_dropdown.get() not in terms:
            self.term_dropdown.set(terms[0])
        self.refresh_table()

    def refresh_table(self):
        term = self.term_dropdown.get()
        if term not in SUBJECT_GROUPS:
            return
        subjects, year, semester = SUBJECT_GROUPS[term]
        self.load_subjects_into_table(
            self.student_number, subjects, year, semester
        )

    def load_subjects_into_table(
        self, student_number, subjects, year_level, semester
    ):
        for row in self.subjects_table.get_children():
            self.subjects_table.delete(row)

        grades = {}
        if student_number:
            for item in get_student_grades_by_category(
                student_number, year_level, semester
            ):
                grades[item["subject_code"].strip()] = item.get("final_grade")

        passed_count = failed_count = 0

        for code in subjects:
            final_g = grades.get(code)
            if not final_g:
                values = (code, "-", "-", "Pending")
            else:
                final_g = float(final_g)
                gp = self.calculate_grade_point(final_g)
                remarks = "Passed" if gp <= 3.00 else "Failed"
                if remarks == "Passed":
                    passed_count += 1
                else:
                    failed_count += 1
                values = (code, f"{final_g:.2f}", f"{gp:.2f}", remarks)
            self.subjects_table.insert("", "end", values=values)

        self.passed_label.config(text=f"PASSED: {passed_count}")
        self.failed_label.config(text=f"FAILED: {failed_count}")
        self.total_label.config(text=f"TOTAL SUBJECTS: {len(subjects)}")