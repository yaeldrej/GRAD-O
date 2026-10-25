# page_calculator_admin.py
import tkinter as tk
from tkinter import ttk
from core.config import SUBJECT_GROUPS, LIGHT_MODE, GLOBAL_EQUIVALENCY_DATA
from logic.entrylimitor import validate_input
from logic.calculator_logic import calculate_grades
from tkinter import messagebox
from core.database import (
    get_subject_period_grades,
    get_section_counts,
    get_students_in_section,
    save_subject_period_grades,
    SECTION_COUNT,
    SECTION_CAPACITY,
)

# Subjects per (year, semester), e.g. ("3rd Year", "1st Semester") -> [...]
TERM_SUBJECTS = {}
for _subjects, _year, _semester in SUBJECT_GROUPS.values():
    TERM_SUBJECTS[(_year, _semester)] = _subjects

YEARS = list(dict.fromkeys(y for _, y, _ in SUBJECT_GROUPS.values()))
SEMESTERS = list(dict.fromkeys(s for _, _, s in SUBJECT_GROUPS.values()))

STUDENT_PLACEHOLDER = "Select a section first"


class CalculatorPage(tk.Frame):

    def __init__(self, parent, ribbon_photo=None, on_save=None, on_delete=None):
        super().__init__(parent, bg=LIGHT_MODE["window"])

        # Kept so the existing call signature still works
        self.on_save = on_save
        self.on_delete = on_delete
        self.current_theme = LIGHT_MODE

        # Students of the chosen section: display name -> student number
        self.student_map = {}
        self.all_student_names = []
        self.selected_student_number = None

        vcmd = (self.register(validate_input), "%P")

        # Calculator Box
        self.calculator_frame = tk.Frame(
            self, bg="#fff2bb", relief="solid", bd=2,
        )
        self.calculator_frame.place(
            relx=0, rely=0, x=15, y=15,
            relwidth=0.6, relheight=1, height=-30, width=-22,
        )

        # Bigger text in the dropdown lists
        self.option_add("*TCombobox*Listbox.font", ("Arial", 13))

        self.subject_label = tk.Label(
            self.calculator_frame, text="Select Subject",
            bg="#fff2bb", font=("Arial", 20, "bold"),
        )
        self.subject_label.place(relx=0.04, rely=0.012, anchor="nw")

        # ---- Row 1: year level -> section -> student ----
        self.year_caption = tk.Label(
            self.calculator_frame, text="YEAR LEVEL",
            bg="#fff2bb", fg="black", font=("Arial", 10, "bold"),
        )
        self.year_caption.place(relx=0.04, rely=0.072, anchor="nw")

        self.section_caption = tk.Label(
            self.calculator_frame, text="SECTION",
            bg="#fff2bb", fg="black", font=("Arial", 10, "bold"),
        )
        self.section_caption.place(relx=0.30, rely=0.072, anchor="nw")

        self.section_info = tk.Label(
            self.calculator_frame, text="",
            bg="#fff2bb", fg="black", font=("Arial", 9, "italic"),
        )
        self.section_info.place(relx=0.39, rely=0.073, anchor="nw")

        self.student_caption = tk.Label(
            self.calculator_frame, text="STUDENT NAME",
            bg="#fff2bb", fg="black", font=("Arial", 10, "bold"),
        )
        self.student_caption.place(relx=0.56, rely=0.072, anchor="nw")

        self.student_hint = tk.Label(
            self.calculator_frame, text="",
            bg="#fff2bb", fg="#990000", font=("Arial", 9, "italic"),
        )
        self.student_hint.place(relx=0.69, rely=0.073, anchor="nw")

        self.year_dropdown = ttk.Combobox(
            self.calculator_frame, values=YEARS, state="readonly",
            font=("Arial", 13),
        )
        self.year_dropdown.set(YEARS[0])
        self.year_dropdown.place(relx=0.04, rely=0.100, relwidth=0.22, height=34)
        self.year_dropdown.bind("<<ComboboxSelected>>", self.on_year_change)

        self.section_dropdown = ttk.Combobox(
            self.calculator_frame, values=[], state="readonly",
            font=("Arial", 13), postcommand=self.refresh_section_labels,
        )
        self.section_dropdown.place(relx=0.30, rely=0.100, relwidth=0.22, height=34)
        self.section_dropdown.bind("<<ComboboxSelected>>", self.on_section_selected)

        self.student_dropdown = ttk.Combobox(
            self.calculator_frame, values=[], font=("Arial", 13),
        )
        self.student_dropdown.place(relx=0.56, rely=0.100, relwidth=0.42, height=34)
        self.student_dropdown.bind("<KeyRelease>", self.on_student_typed)
        self.student_dropdown.bind("<<ComboboxSelected>>", self.on_student_chosen)
        self.student_dropdown.bind("<Return>", self.on_student_chosen)
        self.student_dropdown.bind("<FocusOut>", self.on_student_chosen)
        self.lock_student_dropdown(STUDENT_PLACEHOLDER)

        # ---- Row 2: semester / subject ----
        self.semester_caption = tk.Label(
            self.calculator_frame, text="SEMESTER",
            bg="#fff2bb", fg="black", font=("Arial", 10, "bold"),
        )
        self.semester_caption.place(relx=0.04, rely=0.165, anchor="nw")

        self.subject_caption = tk.Label(
            self.calculator_frame, text="SUBJECT",
            bg="#fff2bb", fg="black", font=("Arial", 10, "bold"),
        )
        self.subject_caption.place(relx=0.56, rely=0.165, anchor="nw")

        self.semester_dropdown = ttk.Combobox(
            self.calculator_frame, values=SEMESTERS, state="readonly",
            font=("Arial", 13),
        )
        self.semester_dropdown.set(SEMESTERS[0])
        self.semester_dropdown.place(relx=0.04, rely=0.193, relwidth=0.48, height=34)
        self.semester_dropdown.bind("<<ComboboxSelected>>", self.on_semester_change)

        self.subject_dropdown = ttk.Combobox(
            self.calculator_frame,
            values=TERM_SUBJECTS.get((YEARS[0], SEMESTERS[0]), []),
            state="readonly", font=("Arial", 13),
        )
        self.subject_dropdown.place(relx=0.56, rely=0.193, relwidth=0.42, height=34)
        self.subject_dropdown.bind("<<ComboboxSelected>>", self.load_subject_grades)

        self.separator = tk.Frame(self.calculator_frame, height=2, bg="#000000")
        self.separator.place(relx=0.001, rely=0.265, relwidth=1)

        self.below_sep = tk.Frame(self.calculator_frame, bg="#f5f5dc")
        self.below_sep.place(relx=0, rely=0.268, relwidth=1, relheight=0.732)

        self.enter_grades_label = tk.Label(
            self.below_sep, text="Enter Grades",
            bg="#f5f5dc", font=("Arial", 20, "bold"),
        )
        self.enter_grades_label.place(relx=0.05, rely=0.03, anchor="nw")

        # Period Grades
        self.period1 = tk.Entry(
            self.below_sep, width=10, font=("Arial", 15),
            validate="key", validatecommand=vcmd, justify="center",
        )
        self.period1.place(relx=0.04, rely=0.250, relwidth=0.26, height=50)

        self.period2 = tk.Entry(
            self.below_sep, width=10, font=("Arial", 15),
            validate="key", validatecommand=vcmd, justify="center",
        )
        self.period2.place(relx=0.38, rely=0.250, relwidth=0.26, height=50)

        self.period3 = tk.Entry(
            self.below_sep, width=10, font=("Arial", 15),
            validate="key", validatecommand=vcmd, justify="center",
        )
        self.period3.place(relx=0.72, rely=0.250, relwidth=0.26, height=50)

        self.period1_text = tk.Label(
            self.below_sep, text="PERIOD 1",
            bg="#f5f5dc", font=("Arial", 15, "bold"),
        )
        self.period1_text.place(relx=0.04, rely=0.155)

        self.period2_text = tk.Label(
            self.below_sep, text="PERIOD 2",
            bg="#f5f5dc", font=("Arial", 15, "bold"),
        )
        self.period2_text.place(relx=0.38, rely=0.155)

        self.period3_text = tk.Label(
            self.below_sep, text="PERIOD 3",
            bg="#f5f5dc", font=("Arial", 15, "bold"),
        )
        self.period3_text.place(relx=0.72, rely=0.155)

        self.equiv_title = tk.Label(
            self.below_sep, text="GRADE EQUIVALENCY",
            font=("Titillium Web", 14, "bold"), bg="#f5f5dc", fg="black",
        )
        self.equiv_title.place(relx=0.04, rely=0.40, anchor="nw")

        self.equiv_frame = tk.Frame(self.below_sep, bg="#f5f5dc")
        self.equiv_frame.place(relx=0.04, rely=0.47, relwidth=0.92, relheight=0.38)
        for col in range(3):
            self.equiv_frame.columnconfigure(col, weight=1, uniform="eq")

        self.equiv_cells = []
        for r, row_data in enumerate(GLOBAL_EQUIVALENCY_DATA):
            self.equiv_frame.rowconfigure(r, weight=1, uniform="eqrows")
            for c, text in enumerate(row_data):
                cell = tk.Label(
                    self.equiv_frame, text=text,
                    font=("Titillium Web", 10, "bold" if r == 0 else "normal"),
                    bg="#fff2bb", fg="black", relief="solid", bd=1,
                )
                cell.grid(row=r, column=c, sticky="nsew")
                self.equiv_cells.append(cell)

        # Calculate Button Separator
        self.separator3 = tk.Frame(self.calculator_frame, height=2, bg="#000000")
        self.separator3.place(relx=0.05, rely=0.90, relwidth=0.9)

        self.below_sep3 = tk.Frame(self.calculator_frame, bg="#f5f5dc")
        self.below_sep3.place(
            relx=0, rely=0.903, relwidth=1, relheight=0.097,
        )

        # Results Panel
        self.result_frame = tk.Frame(
            self, bg="#fff2bb", borderwidth=2, relief="solid",
        )

        self.result_text = tk.Label(
            self.result_frame, text="RESULTS",
            bg="#fff2bb", fg="black", font=("Titillium Web", 15, "bold"),
        )
        self.result_text.pack(fill="x", pady=20, padx=10, anchor="nw")

        self.res_separator = tk.Frame(self.result_frame, height=2, bg="#000000")
        self.res_separator.place(relx=0.001, rely=0.2, relwidth=1)

        self.below_res_sep = tk.Frame(self.result_frame, bg="#f5f5dc")
        self.below_res_sep.place(
            relx=0, rely=0.203, relwidth=1, relheight=0.797,
        )

        self.final_grade_heading = tk.Label(
            self.below_res_sep, text="FINAL GRADE",
            font=("Titillium Web", 11, "bold"), bg="#f5f5dc", fg="black",
        )
        self.final_grade_heading.place(relx=0.03, rely=0.03, relwidth=0.45)

        self.grade_point_heading = tk.Label(
            self.below_res_sep, text="GRADE POINT",
            font=("Titillium Web", 11, "bold"), bg="#f5f5dc", fg="black",
        )
        self.grade_point_heading.place(relx=0.52, rely=0.03, relwidth=0.45)

        self.result_vertical_separator = tk.Frame(
            self.below_res_sep, width=2, bg="#000000",
        )
        self.result_vertical_separator.place(
            relx=0.5, rely=0.02, relheight=0.35
        )

        self.final_grade_value = tk.Label(
            self.below_res_sep, text="--",
            font=("Titillium Web", 22, "bold"), bg="#f5f5dc", fg="black",
        )
        self.final_grade_value.place(relx=0.03, rely=0.20, relwidth=0.45)

        self.grade_point_value = tk.Label(
            self.below_res_sep, text="--",
            font=("Titillium Web", 22, "bold"), bg="#f5f5dc", fg="black",
        )
        self.grade_point_value.place(relx=0.52, rely=0.20, relwidth=0.45)

        self.status_result = tk.Label(
            self.below_res_sep, text="",
            font=("Titillium Web", 12, "bold"),
            bg="#f5f5dc", fg="black",
            anchor="center", justify="center", padx=10,
        )
        self.status_result.place(
            relx=0.5, rely=0.6, relwidth=0.88, height=60, anchor="center",
        )

        # Save / Cancel buttons (under the PASSED / FAILED bar)
        self.save_button = tk.Button(
            self.below_res_sep, text="💾 SAVE GRADE",
            font=("Titillium Web", 12, "bold"),
            bg="#fff2bb", fg="black",
            activebackground="#887b40", activeforeground="black",
            command=self.click_save_button,
        )
        self.save_button.place(relx=0.05, rely=0.72, relwidth=0.42, height=70)

        self.cancel_button = tk.Button(
            self.below_res_sep, text="✖ CANCEL",
            font=("Titillium Web", 12, "bold"),
            bg="#fff2bb", fg="black",
            activebackground="#887b40", activeforeground="black",
            command=self.click_cancel_button,
        )
        self.cancel_button.place(relx=0.53, rely=0.72, relwidth=0.42, height=70)
    
        # Store Result Information
        self.current_result = None

        # Calculate Button
        self.calculator_button = tk.Button(
            self.below_sep3, text="🖩 CALCULATE",
            bg="#fff2bb", fg="black",
            activebackground="#887b40", activeforeground="black",
            command=self.click_calculate_button,
        )
        self.calculator_button.place(relx=0.05, rely=0.1, relwidth=0.9, relheight=0.8)

        self.bind("<Configure>", self.update_popup_position)
        self.refresh_section_labels()
        self.place_result_panel()

    # ------------------------------------------------------------------
    # Step 1: year level -> Step 2: section -> Step 3: student
    # ------------------------------------------------------------------
    def update_subjects(self):
        key = (self.year_dropdown.get(), self.semester_dropdown.get())
        self.subject_dropdown["values"] = TERM_SUBJECTS.get(key, [])
        self.subject_dropdown.set("")
        self.clear_period_entries()

    def on_year_change(self, event=None):
        """A new year level means a new set of sections and students."""
        self.update_subjects()
        self.section_dropdown.set("")
        self.section_info.config(text="")
        self.reset_students()
        self.refresh_section_labels()

    def on_semester_change(self, event=None):
        self.update_subjects()

    def refresh_section_labels(self):
        """List 'Section N (students/30)' for the chosen year level."""
        try:
            counts = get_section_counts(self.year_dropdown.get())
        except Exception as e:
            print(f"[DEBUG] Could not load section counts: {e}")
            counts = {}
        self.section_dropdown["values"] = [
            f"Section {n}   ({counts.get(n, 0)}/{SECTION_CAPACITY})"
            for n in range(1, SECTION_COUNT + 1)
        ]

    def get_section_number(self):
        try:
            return int(self.section_dropdown.get().split()[1])
        except (IndexError, ValueError):
            return None

    def lock_student_dropdown(self, message):
        self.student_dropdown.config(state="normal")
        self.student_dropdown.set(message)
        self.student_dropdown.config(state="disabled")

    def reset_students(self):
        self.student_map = {}
        self.all_student_names = []
        self.selected_student_number = None
        self.student_dropdown["values"] = []
        self.student_hint.config(text="")
        self.lock_student_dropdown(STUDENT_PLACEHOLDER)
        self.clear_period_entries()

    def on_section_selected(self, event=None):
        self.reset_students()
        self.load_section_students()

    def load_section_students(self, keep_selection=False):
        """Fill the student dropdown with the students of the chosen section."""
        section = self.get_section_number()
        if section is None:
            return

        previous = self.student_dropdown.get().strip() if keep_selection else ""

        try:
            students = get_students_in_section(
                self.year_dropdown.get(), section
            )
        except Exception as e:
            print(f"[DEBUG] Could not load students: {e}")
            students = []

        self.student_map = {}
        for number, name in students:
            label = name
            if label in self.student_map:      # two students, same name
                label = f"{name} ({number})"
            self.student_map[label] = number
        self.all_student_names = list(self.student_map.keys())

        total = len(students)
        self.section_info.config(
            text=f"{total} student{'s' if total != 1 else ''}"
        )

        if not students:
            self.lock_student_dropdown("No students in this section")
            return

        self.student_dropdown.config(state="normal")
        self.student_dropdown["values"] = self.all_student_names
        self.student_dropdown.set("")

        if previous in self.student_map:
            self.student_dropdown.set(previous)
            self.on_student_chosen()

    def refresh_students(self):
        """Called when the page is opened: reload the section's students."""
        self.refresh_section_labels()
        if self.get_section_number() is not None:
            self.load_section_students(keep_selection=True)

    # ------------------------------------------------------------------
    # Student name lookup (only inside the chosen section)
    # ------------------------------------------------------------------
    def on_student_typed(self, event=None):
        """Narrow the dropdown list as the admin types a name."""
        if str(self.student_dropdown.cget("state")) == "disabled":
            return
        if event is not None and event.keysym in (
            "Up", "Down", "Left", "Right", "Return", "Tab", "Escape",
        ):
            return
        typed = self.student_dropdown.get().strip().lower()
        if typed:
            matches = [n for n in self.all_student_names if typed in n.lower()]
        else:
            matches = self.all_student_names
        self.student_dropdown["values"] = matches

    def resolve_student(self):
        """Match the typed name to a student number (None if no match)."""
        typed = self.student_dropdown.get().strip().lower()
        if not typed:
            return None
        for name, number in self.student_map.items():
            if name.lower() == typed:
                return number
        return None

    def on_student_chosen(self, event=None):
        if str(self.student_dropdown.cget("state")) == "disabled":
            return
        number = self.resolve_student()
        typed = self.student_dropdown.get().strip()

        if number is None:
            self.selected_student_number = None
            self.student_hint.config(text="Student not found" if typed else "")
            self.clear_period_entries()
            return

        self.student_hint.config(text="")
        if number != self.selected_student_number:
            self.selected_student_number = number
            self.load_subject_grades()

    # ------------------------------------------------------------------
    # Grade loading
    # ------------------------------------------------------------------
    def _set_entry(self, entry, value):
        entry.config(validate="none")
        entry.delete(0, tk.END)
        if value and value > 0:
            entry.insert(0, f"{value:.2f}")
        entry.config(validate="key")

    def clear_period_entries(self):
        for entry in (self.period1, self.period2, self.period3):
            self._set_entry(entry, 0)

    def load_subject_grades(self, event=None):
        """Fill Period 1/2/3 from the selected student's saved grades."""
        subject = self.subject_dropdown.get()
        if not subject or not self.selected_student_number:
            self.clear_period_entries()
            return

        try:
            grades = get_subject_period_grades(
                self.selected_student_number,
                self.year_dropdown.get(),
                self.semester_dropdown.get(),
                subject,
            )
        except Exception as e:
            print(f"[DEBUG] Could not load grades: {e}")
            grades = {}

        self._set_entry(self.period1, grades.get("p1", 0))
        self._set_entry(self.period2, grades.get("p2", 0))
        self._set_entry(self.period3, grades.get("p3", 0))

    # ------------------------------------------------------------------
    # Results panel
    # ------------------------------------------------------------------
    def update_popup_position(self, event=None):
        if event is not None and event.widget is not self:
            return
        if self.result_frame.winfo_ismapped():
            self.place_result_panel()

    def place_result_panel(self):
        self.result_frame.place(
            relx=0.6, rely=0, x=7, y=15,
            relwidth=0.4, relheight=1,
            width=-22, height=-30,
        )
        self.result_frame.lift()

    def get_grade_point(self, final_grade):
        if final_grade >= 94.8:
            return 1.0
        elif final_grade >= 89.2:
            return 1.25
        elif final_grade >= 83.6:
            return 1.50
        elif final_grade >= 78.0:
            return 1.75
        elif final_grade >= 72.4:
            return 2.0
        elif final_grade >= 66.8:
            return 2.25
        elif final_grade >= 61.2:
            return 2.50
        elif final_grade >= 55.6:
            return 2.75
        elif final_grade >= 50.0:
            return 3.0
        else:
            return 3.25

    def click_calculate_button(self):
        if not self.subject_dropdown.get():
            self.show_result_error("Please select a subject first.")
            return

        if not any(
            e.get().strip() for e in (self.period1, self.period2, self.period3)
        ):
            self.current_result = None
            self.final_grade_value.config(text="--")
            self.grade_point_value.config(text="--")
            self.show_result_error("No grades entered for this subject yet.")
            return

        result = calculate_grades(self)

        if result.get("error"):
            self.current_result = None
            self.final_grade_value.config(text="--")
            self.grade_point_value.config(text="--")
            self.show_result_error(result["error"])
            return

        try:
            final_grade = float(result["total"])

            if not 0 <= final_grade <= 100:
                raise ValueError("The final grade must be between 0 and 100.")

            if result.get("grade_point") is not None:
                grade_point = float(result["grade_point"])
            else:
                grade_point = self.get_grade_point(final_grade)

            if grade_point <= 3.0:
                status, status_bg, status_fg = "PASSED", "#91ff00", "black"
            else:
                status, status_bg, status_fg = "FAILED", "#ff3333", "white"

            point_display = {
                1.0: "1.0", 1.25: "1.25", 1.5: "1.50", 1.75: "1.75",
                2.0: "2.0", 2.25: "2.25", 2.5: "2.50", 2.75: "2.75",
                3.0: "3.0", 3.25: "3.25",
            }

            self.final_grade_value.config(text=f"{final_grade:.2f}")
            self.grade_point_value.config(
                text=point_display.get(grade_point, f"{grade_point:.2f}")
            )
            self.status_result.config(
                text=f"● {status}", bg=status_bg, fg=status_fg,
            )

            self.current_result = {
                "student": self.student_dropdown.get().strip(),
                "student_number": self.selected_student_number,
                "section": self.get_section_number(),
                "subject": self.subject_dropdown.get(),
                "year_level": self.year_dropdown.get(),
                "semester": self.semester_dropdown.get(),
                "final_grade": final_grade,
                "grade_point": grade_point,
                "grade_point_text": point_display.get(
                    grade_point, f"{grade_point:.2f}"
                ),
                "status": status,
            }

        except (KeyError, TypeError, ValueError) as error:
            self.current_result = None
            self.final_grade_value.config(text="--")
            self.grade_point_value.config(text="--")
            self.show_result_error(str(error))

        self.place_result_panel()

    def _read_period(self, entry, label):
        """Entry text -> float (0-100) or None if blank."""
        text = entry.get().strip()
        if not text:
            return None
        value = float(text)
        if not 0 <= value <= 100:
            raise ValueError(f"{label} must be between 0 and 100.")
        return value

    def click_save_button(self):
        if not self.selected_student_number:
            messagebox.showwarning("Save", "Select a student first.")
            return
        if not self.subject_dropdown.get():
            messagebox.showwarning("Save", "Select a subject first.")
            return

        try:
            p1 = self._read_period(self.period1, "Period 1")
            p2 = self._read_period(self.period2, "Period 2")
            p3 = self._read_period(self.period3, "Period 3")
        except ValueError as e:
            messagebox.showerror("Save", str(e))
            return

        if p1 is None and p2 is None and p3 is None:
            messagebox.showwarning("Save", "Enter at least one period grade.")
            return

        # Final grade + remarks are saved only when all 3 periods exist
        final_grade, remarks = None, None
        if None not in (p1, p2, p3):
            self.click_calculate_button()
            if self.current_result is not None:
                final_grade = self.current_result["final_grade"]
                remarks = self.current_result["status"]      # PASSED / FAILED

        try:
            save_subject_period_grades(
                self.selected_student_number,
                self.year_dropdown.get(),
                self.semester_dropdown.get(),
                self.subject_dropdown.get(),
                p1, p2, p3, final_grade, remarks,
            )
        except Exception as e:
            messagebox.showerror("Save failed", str(e))
            return

        if self.on_save:
            self.on_save(self.current_result)

        note = ("Final grade saved too." if final_grade is not None
                else "Final grade will be saved once all 3 periods are entered.")
        messagebox.showinfo(
            "Saved",
            f"Grades saved for {self.student_dropdown.get().strip()}.\n{note}",
        )

    def reset_results(self):
        """Put the results panel back to its empty state."""
        theme = self.current_theme
        self.current_result = None
        self.final_grade_value.config(text="--")
        self.grade_point_value.config(text="--")
        self.status_result.config(
            text="", bg=theme["window"], fg=theme["text"],
        )

    def click_cancel_button(self):
        """Discard unsaved edits: reload the saved grades and clear results."""
        self.reset_results()
        self.load_subject_grades()

    def show_result_error(self, error):
        theme = self.current_theme

        if theme["window"] == "#1e1e1e":
            error_bg, error_fg = "#5b2020", "#ffdada"
        else:
            error_bg, error_fg = "#ffcccc", "#990000"

        self.result_frame.configure(bg=theme["table"])
        self.result_text.configure(
            text="RESULTS", bg=theme["table"], fg=theme["text"],
        )
        self.below_res_sep.configure(bg=theme["window"])

        for label in (
            self.final_grade_heading,
            self.grade_point_heading,
            self.final_grade_value,
            self.grade_point_value,
        ):
            label.configure(bg=theme["window"], fg=theme["text"])

        self.status_result.configure(
            text=f"ERROR: {error}", bg=error_bg, fg=error_fg, wraplength=400,
        )
        self.place_result_panel()

    # ------------------------------------------------------------------
    # Light / Dark mode
    # ------------------------------------------------------------------
    def apply_theme(self, theme, ribbon_photo=None, ribbon_photo_white=None):
        self.current_theme = theme
        dark = theme["window"] == "#1e1e1e"

        self.configure(bg=theme["window"])

        # Calculator frames
        self.calculator_frame.configure(bg=theme["table"])
        self.below_sep.configure(bg=theme["window"])
        self.below_sep3.configure(bg=theme["window"])

        # Header labels sit on the calculator frame color
        for label in (
            self.subject_label,
            self.year_caption,
            self.section_caption,
            self.section_info,
            self.student_caption,
            self.semester_caption,
            self.subject_caption,
        ):
            label.configure(bg=theme["table"], fg=theme["text"])

        self.student_hint.configure(
            bg=theme["table"], fg="#ff9999" if dark else "#990000"
        )

        # Labels below the separator sit on the window color
        for label in (
            self.enter_grades_label,
            self.period1_text,
            self.period2_text,
            self.period3_text,
        ):
            label.configure(bg=theme["window"], fg=theme["text"])

        # Equivalency table
        self.equiv_title.configure(bg=theme["window"], fg=theme["text"])
        self.equiv_frame.configure(bg=theme["window"])
        for cell in self.equiv_cells:
            cell.configure(bg=theme["table"], fg=theme["text"])

        # Entries
        for entry in (self.period1, self.period2, self.period3):
            entry.configure(
                bg=theme["table"],
                fg=theme["text"],
                insertbackground=theme["text"],
            )

        # Separators
        for separator in (
            self.separator,
            self.separator3,
            self.res_separator,
            self.result_vertical_separator,
        ):
            separator.configure(bg=theme["text"])

        # Calculate / Save / Cancel buttons
        for button in (
            self.calculator_button,
            self.save_button,
            self.cancel_button,
        ):
            button.configure(
                bg=theme["table"], fg=theme["text"],
                activebackground=theme["sidebar"], activeforeground=theme["text"],
            )

        # Results panel
        self.result_frame.configure(bg=theme["table"])
        self.below_res_sep.configure(bg=theme["window"])
        self.result_text.configure(bg=theme["table"], fg=theme["text"])

        for label in (
            self.final_grade_heading,
            self.grade_point_heading,
            self.final_grade_value,
            self.grade_point_value,
        ):
            label.configure(bg=theme["window"], fg=theme["text"])

        # Keep the status / error colors meaningful
        if self.status_result.cget("text").startswith("ERROR:"):
            self.status_result.configure(
                bg="#5b2020" if dark else "#ffcccc",
                fg="#ffdada" if dark else "#990000",
            )
        elif self.current_result is not None and self.current_result.get("status"):
            if self.current_result["status"] == "PASSED":
                self.status_result.configure(bg="#91ff00", fg="black")
            else:
                self.status_result.configure(bg="#ff3333", fg="white")
        else:
            self.status_result.configure(bg=theme["window"], fg=theme["text"])

        if self.result_frame.winfo_ismapped():
            self.result_frame.lift()