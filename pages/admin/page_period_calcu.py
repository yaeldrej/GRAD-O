# page_period_calculator.py
import tkinter as tk
from tkinter import ttk, messagebox
from core.config import SUBJECT_GROUPS, LIGHT_MODE
from logic.entrylimitor import validate_input
from logic.per_calculator_grade import per_calculate_grade
from core import shared_results
from core.database import (
    get_section_counts,
    get_students_in_section,
    save_period_result,
    get_period_components,
    SECTION_COUNT,
    SECTION_CAPACITY,
)

# Subjects per (year, semester), and the SUBJECT_GROUPS key of each term
TERM_SUBJECTS = {}
TERM_KEY = {}
for _key, (_subjects, _year, _semester) in SUBJECT_GROUPS.items():
    TERM_SUBJECTS[(_year, _semester)] = _subjects
    TERM_KEY[(_year, _semester)] = _key

YEARS = list(dict.fromkeys(y for _, y, _ in SUBJECT_GROUPS.values()))
SEMESTERS = list(dict.fromkeys(s for _, _, s in SUBJECT_GROUPS.values()))
PERIODS = ["Period 1", "Period 2", "Period 3"]

STUDENT_PLACEHOLDER = "Select a section first"
PASSING_MARK = 75.0


class PeriodCalculatorPage(tk.Frame):

    def __init__(self, parent, ribbon_photo=None, on_save=None, on_delete=None):
        super().__init__(parent, bg=LIGHT_MODE["window"])

        # Callbacks so other pages can react when a result is saved
        self.on_save = on_save
        self.on_delete = on_delete   # kept so the old call signature still works
        self.current_theme = LIGHT_MODE

        # Students of the chosen section: display name -> student number
        self.student_map = {}
        self.all_student_names = []
        self.selected_student_number = None

        # Store Result Information
        self.percal_current_result = None
        self.percal_saved_results = []

        vcmd = (self.register(validate_input), "%P")

        # Bigger text in the dropdown lists
        self.option_add("*TCombobox*Listbox.font", ("Arial", 13))

        # ---------------- Left panel ----------------
        self.percal_calculator_frame = tk.Frame(
            self, bg="#fff2bb", relief="solid", bd=2,
        )
        self.percal_calculator_frame.place(
            relx=0, rely=0, x=15, y=15,
            relwidth=0.6, relheight=1, height=-30, width=-22,
        )

        self.percal_subject_label = tk.Label(
            self.percal_calculator_frame, text="Select Subject",
            bg="#fff2bb", font=("Arial", 20, "bold"),
        )
        self.percal_subject_label.place(relx=0.04, rely=0.012, anchor="nw")

        # ---- Row 1: year level -> section -> student ----
        self.year_caption = self._caption("YEAR LEVEL", 0.04, 0.072)
        self.section_caption = self._caption("SECTION", 0.30, 0.072)
        self.student_caption = self._caption("STUDENT NAME", 0.56, 0.072)

        self.section_info = tk.Label(
            self.percal_calculator_frame, text="",
            bg="#fff2bb", fg="black", font=("Arial", 9, "italic"),
        )
        self.section_info.place(relx=0.39, rely=0.073, anchor="nw")

        self.student_hint = tk.Label(
            self.percal_calculator_frame, text="",
            bg="#fff2bb", fg="#990000", font=("Arial", 9, "italic"),
        )
        self.student_hint.place(relx=0.69, rely=0.073, anchor="nw")

        self.year_dropdown = ttk.Combobox(
            self.percal_calculator_frame, values=YEARS, state="readonly",
            font=("Arial", 13),
        )
        self.year_dropdown.set(YEARS[0])
        self.year_dropdown.place(relx=0.04, rely=0.100, relwidth=0.22, height=34)
        self.year_dropdown.bind("<<ComboboxSelected>>", self.on_year_change)

        self.section_dropdown = ttk.Combobox(
            self.percal_calculator_frame, values=[], state="readonly",
            font=("Arial", 13), postcommand=self.refresh_section_labels,
        )
        self.section_dropdown.place(relx=0.30, rely=0.100, relwidth=0.22, height=34)
        self.section_dropdown.bind("<<ComboboxSelected>>", self.on_section_selected)

        self.student_dropdown = ttk.Combobox(
            self.percal_calculator_frame, values=[], font=("Arial", 13),
        )
        self.student_dropdown.place(relx=0.56, rely=0.100, relwidth=0.42, height=34)
        self.student_dropdown.bind("<KeyRelease>", self.on_student_typed)
        self.student_dropdown.bind("<<ComboboxSelected>>", self.on_student_chosen)
        self.student_dropdown.bind("<Return>", self.on_student_chosen)
        self.student_dropdown.bind("<FocusOut>", self.on_student_chosen)
        self.lock_student_dropdown(STUDENT_PLACEHOLDER)

        # ---- Row 2: semester / subject / period ----
        self.semester_caption = self._caption("SEMESTER", 0.04, 0.165)
        self.subject_caption = self._caption("SUBJECT", 0.30, 0.165)
        self.period_caption = self._caption("PERIOD", 0.56, 0.165)

        self.semester_dropdown = ttk.Combobox(
            self.percal_calculator_frame, values=SEMESTERS, state="readonly",
            font=("Arial", 13),
        )
        self.semester_dropdown.set(SEMESTERS[0])
        self.semester_dropdown.place(relx=0.04, rely=0.193, relwidth=0.22, height=34)
        self.semester_dropdown.bind("<<ComboboxSelected>>", self.on_semester_change)

        self.percal_subject_dropdown = ttk.Combobox(
            self.percal_calculator_frame,
            values=TERM_SUBJECTS.get((YEARS[0], SEMESTERS[0]), []),
            state="readonly", font=("Arial", 13),
        )
        self.percal_subject_dropdown.place(
            relx=0.30, rely=0.193, relwidth=0.22, height=34
        )
        self.percal_subject_dropdown.bind(
            "<<ComboboxSelected>>", self.on_subject_change
        )

        self.percal_period_dropdown = ttk.Combobox(
            self.percal_calculator_frame, values=PERIODS, state="readonly",
            font=("Arial", 13),
        )
        self.percal_period_dropdown.set(PERIODS[0])
        self.percal_period_dropdown.place(
            relx=0.56, rely=0.193, relwidth=0.22, height=34
        )
        self.percal_period_dropdown.bind(
            "<<ComboboxSelected>>", self.on_period_change
        )

        # Compatibility alias if external calculator logic expects subject_dropdown
        self.subject_dropdown = self.percal_subject_dropdown

        self.percal_separator = tk.Frame(
            self.percal_calculator_frame, height=2, bg="#000000"
        )
        self.percal_separator.place(relx=0.001, rely=0.265, relwidth=1)

        self.percal_below_sep = tk.Frame(self.percal_calculator_frame, bg="#f5f5dc")
        self.percal_below_sep.place(relx=0, rely=0.268, relwidth=1, relheight=0.732)

        self.percal_enter_grades_label = tk.Label(
            self.percal_below_sep, text="Enter Grades",
            bg="#f5f5dc", font=("Arial", 20, "bold"),
        )
        self.percal_enter_grades_label.place(relx=0.05, rely=0.03, anchor="nw")

        # Grade input fields: caption, entry, "out of" box
        self.percal_max_entries = {}
        self.percal_max_labels = []
        self.percal_captions = []

        def make_column(caption, relx, key):
            title = tk.Label(
                self.percal_below_sep, text=caption,
                bg="#f5f5dc", font=("Arial", 14, "bold"),
            )
            title.place(relx=relx, rely=0.16)
            self.percal_captions.append(title)

            entry = tk.Entry(
                self.percal_below_sep, width=10, font=("Arial", 15),
                validate="key", validatecommand=vcmd, justify="center",
            )
            entry.place(relx=relx, rely=0.25, relwidth=0.26, height=50)

            label = tk.Label(
                self.percal_below_sep, text="out of",
                bg="#f5f5dc", font=("Arial", 10),
            )
            label.place(relx=relx, rely=0.375)
            self.percal_max_labels.append(label)

            max_entry = tk.Entry(
                self.percal_below_sep, width=6, font=("Arial", 11),
                validate="key", validatecommand=vcmd, justify="center",
            )
            max_entry.insert(0, "100")
            max_entry.place(relx=relx + 0.09, rely=0.37, height=26)
            self.percal_max_entries[key] = max_entry
            return entry

        self.percal_written_works = make_column("WRITTEN WORKS", 0.04, "written")
        self.percal_quiz_ptask = make_column("QUIZ / PTASK", 0.38, "quiz")
        self.percal_exam = make_column("EXAM", 0.72, "exam")

        # Compatibility aliases for per_calculator_grade module access
        self.written_works = self.percal_written_works
        self.quiz_ptask = self.percal_quiz_ptask
        self.exam = self.percal_exam

        self.percal_load_button = tk.Button(
            self.percal_below_sep, text="LOAD SAVED SCORES",
            font=("Arial", 12, "bold"), bg="#fff2bb", fg="black",
            command=self.percal_load_scores,
        )
        self.percal_load_button.place(relx=0.04, rely=0.52, width=230, height=40)

        # Calculate Button
        self.percal_separator3 = tk.Frame(
            self.percal_calculator_frame, height=2, bg="#000000",
        )
        self.percal_separator3.place(relx=0.05, rely=0.90, relwidth=0.9)

        self.percal_below_sep3 = tk.Frame(
            self.percal_calculator_frame, bg="#f5f5dc",
        )
        self.percal_below_sep3.place(
            relx=0, rely=0.903, relwidth=1, relheight=0.097,
        )

        self.percal_calculator_button = tk.Button(
            self.percal_below_sep3, text="🖩 CALCULATE",
            bg="#fff2bb", fg="black",
            activebackground="#887b40", activeforeground="black",
            command=self.percal_click_calculate_button,
        )
        self.percal_calculator_button.place(
            relx=0.05, rely=0.1, relwidth=0.9, relheight=0.8
        )

        # ---------------- Results panel ----------------
        self.percal_result_frame = tk.Frame(
            self, bg="#fff2bb", borderwidth=2, relief="solid",
        )

        self.percal_result_text = tk.Label(
            self.percal_result_frame, text="RESULTS",
            bg="#fff2bb", fg="black", font=("Titillium Web", 15, "bold"),
        )
        self.percal_result_text.pack(fill="x", pady=(14, 0), padx=10, anchor="nw")

        self.percal_save_target = tk.Label(
            self.percal_result_frame, text="",
            bg="#fff2bb", fg="black", font=("Arial", 10, "bold"),
        )
        self.percal_save_target.pack(anchor="nw", padx=10, pady=(6, 0))

        self.percal_res_separator = tk.Frame(
            self.percal_result_frame, height=2, bg="#000000",
        )
        self.percal_res_separator.place(relx=0.001, rely=0.2, relwidth=1)

        self.percal_below_res_sep = tk.Frame(
            self.percal_result_frame, bg="#f5f5dc",
        )
        self.percal_below_res_sep.place(
            relx=0, rely=0.203, relwidth=1, relheight=0.797,
        )

        self.percal_score_heading = tk.Label(
            self.percal_below_res_sep, text="RESULT",
            font=("Titillium Web", 12, "bold"), bg="#f5f5dc", fg="black",
        )
        self.percal_score_heading.place(relx=0.05, rely=0.05, relwidth=0.9)

        self.percal_score_value = tk.Label(
            self.percal_below_res_sep, text="--",
            font=("Titillium Web", 28, "bold"), bg="#f5f5dc", fg="black",
        )
        self.percal_score_value.place(relx=0.05, rely=0.14, relwidth=0.9)

        self.percal_status_result = tk.Label(
            self.percal_below_res_sep, text="",
            font=("Titillium Web", 12, "bold"),
            bg="#f5f5dc", fg="black",
            anchor="center", justify="center", padx=10, wraplength=400,
        )
        self.percal_status_result.place(
            relx=0.5, rely=0.62, relwidth=0.88, height=60, anchor="center",
        )

        # Save / Cancel buttons
        self.percal_save_button = tk.Button(
            self.percal_below_res_sep, text="💾 SAVE GRADE",
            font=("Titillium Web", 12, "bold"),
            bg="#fff2bb", fg="black",
            activebackground="#887b40", activeforeground="black",
            command=self.percal_save_result,
        )
        self.percal_save_button.place(relx=0.05, rely=0.86, relwidth=0.42, height=60)

        self.percal_cancel_button = tk.Button(
            self.percal_below_res_sep, text="✖ CANCEL",
            font=("Titillium Web", 12, "bold"),
            bg="#fff2bb", fg="black",
            activebackground="#887b40", activeforeground="black",
            command=self.percal_cancel,
        )
        self.percal_cancel_button.place(relx=0.53, rely=0.86, relwidth=0.42, height=60)

        self.percal_update_save_target()
        self.bind("<Configure>", self.percal_update_popup_position)
        self.refresh_section_labels()
        self.percal_place_result_panel()

    # ------------------------------------------------------------------
    # Small helpers
    # ------------------------------------------------------------------
    def _caption(self, text, relx, rely):
        label = tk.Label(
            self.percal_calculator_frame, text=text,
            bg="#fff2bb", fg="black", font=("Arial", 10, "bold"),
        )
        label.place(relx=relx, rely=rely, anchor="nw")
        return label

    def percal_place_result_panel(self):
        self.percal_result_frame.place(
            relx=0.6, rely=0, x=7, y=15,
            relwidth=0.4, relheight=1, width=-22, height=-30,
        )
        self.percal_result_frame.lift()

    def percal_update_popup_position(self, event=None):
        if event is not None and event.widget is not self:
            return
        self.percal_place_result_panel()

    def percal_update_save_target(self, event=None):
        self.percal_save_target.config(
            text=f"Saving to: {self.percal_period_dropdown.get()} - "
                 f"{self.percal_subject_dropdown.get() or 'no subject'}"
        )

    def percal_clear_entries(self):
        for entry in (
            self.percal_written_works,
            self.percal_quiz_ptask,
            self.percal_exam,
        ):
            entry.delete(0, tk.END)
        for max_entry in self.percal_max_entries.values():
            max_entry.delete(0, tk.END)
            max_entry.insert(0, "100")

    def percal_reset(self):
        """Empty the entries and the results panel."""
        theme = self.current_theme
        self.percal_clear_entries()
        self.percal_current_result = None
        self.percal_score_value.config(text="--")
        self.percal_status_result.config(
            text="", bg=theme["window"], fg=theme["text"]
        )
        self.percal_update_save_target()

    # ------------------------------------------------------------------
    # Year level -> section -> student
    # ------------------------------------------------------------------
    def update_subjects(self):
        key = (self.year_dropdown.get(), self.semester_dropdown.get())
        self.percal_subject_dropdown["values"] = TERM_SUBJECTS.get(key, [])
        self.percal_subject_dropdown.set("")
        self.percal_reset()

    def on_year_change(self, event=None):
        """A new year level means a new set of sections and students."""
        self.update_subjects()
        self.section_dropdown.set("")
        self.section_info.config(text="")
        self.reset_students()
        self.refresh_section_labels()

    def on_semester_change(self, event=None):
        self.update_subjects()

    def on_subject_change(self, event=None):
        self.percal_reset()

    def on_period_change(self, event=None):
        self.percal_reset()

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
        self.percal_reset()

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
        """Call when the page is opened: reload the section's students."""
        self.refresh_section_labels()
        if self.get_section_number() is not None:
            self.load_section_students(keep_selection=True)

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
            if self.selected_student_number is not None:
                self.percal_reset()
            self.selected_student_number = None
            self.student_hint.config(text="Student not found" if typed else "")
            return

        self.student_hint.config(text="")
        if number != self.selected_student_number:
            self.selected_student_number = number
            self.percal_reset()

    # ------------------------------------------------------------------
    # Calculate
    # ------------------------------------------------------------------
    def percal_click_calculate_button(self):
        if not self.selected_student_number:
            self.percal_show_result_error("Please select a student first.")
            return
        if not self.percal_subject_dropdown.get():
            self.percal_show_result_error("Please select a subject first.")
            return

        # Nothing typed: try the student's saved scores
        if not (
            self.percal_written_works.get().strip()
            or self.percal_quiz_ptask.get().strip()
            or self.percal_exam.get().strip()
        ):
            if not self.percal_load_scores():
                return

        result = per_calculate_grade(self)

        if result.get("error"):
            self.percal_current_result = None
            self.percal_score_value.config(text="--")
            self.percal_show_result_error(result["error"])
            return

        try:
            total_score = float(result["total"])

            if not 0 <= total_score <= 100:
                raise ValueError(
                    "The calculated result must be between 0 and 100."
                )

            if total_score >= PASSING_MARK:
                status, status_bg, status_fg = "PASSED", "#91ff00", "black"
            else:
                status, status_bg, status_fg = "FAILED", "#ff3333", "white"

            self.percal_score_value.config(text=f"{total_score:.2f}")
            self.percal_update_save_target()
            self.percal_status_result.config(
                text=f"● {status}", bg=status_bg, fg=status_fg,
            )

            year = self.year_dropdown.get()
            semester = self.semester_dropdown.get()
            self.percal_current_result = {
                "student_no": self.selected_student_number,
                "block_section": str(self.get_section_number() or ""),
                "term": TERM_KEY.get((year, semester), f"{year} - {semester}"),
                "year_level": year,
                "semester": semester,
                "period": self.percal_period_dropdown.get(),
                "subject": self.percal_subject_dropdown.get(),
                "written": float(result["written"]),
                "quiz": float(result["quiz"]),
                "exam": float(result["exam"]),
                "result": total_score,
                "status": status,
            }

        except (KeyError, TypeError, ValueError) as error:
            self.percal_current_result = None
            self.percal_score_value.config(text="--")
            self.percal_show_result_error(str(error))

        self.percal_place_result_panel()

    def percal_show_result_error(self, error):
        theme = self.current_theme
        if theme["window"] == "#1e1e1e":
            error_bg, error_fg = "#5b2020", "#ffdada"
        else:
            error_bg, error_fg = "#ffcccc", "#990000"

        self.percal_score_value.config(text="--")
        self.percal_status_result.config(
            text=f"ERROR: {error}", bg=error_bg, fg=error_fg,
        )
        self.percal_place_result_panel()

    # ------------------------------------------------------------------
    # Save / Cancel
    # ------------------------------------------------------------------
    def percal_save_result(self):
        if self.percal_current_result is None:
            messagebox.showwarning(
                "No Result", "Please calculate a grade first.", parent=self,
            )
            return

        saved = self.percal_current_result.copy()

        try:
            save_period_result(
                saved["student_no"],
                saved["year_level"],
                saved["semester"],
                saved["subject"],
                saved["period"],
                saved["written"],
                saved["quiz"],
                saved["exam"],
                saved["result"],
            )
        except Exception as e:
            messagebox.showerror(
                "Database Error", f"Failed to save grade: {e}", parent=self,
            )
            return

        # Replace an older save of the same subject and period
        self.percal_saved_results = [
            r for r in self.percal_saved_results
            if (r["subject"], r["period"]) != (saved["subject"], saved["period"])
        ]
        self.percal_saved_results.append(saved)

        if self.on_save:
            self.on_save(saved)

        shared_results.publish_save(saved)

        messagebox.showinfo(
            "Saved",
            f'{saved["period"]} grade of {saved["result"]:.2f} saved for '
            f'{self.student_dropdown.get().strip()}\n{saved["subject"]}.',
            parent=self,
        )

    def percal_cancel(self):
        """Discard what was typed and calculated (nothing is saved or deleted)."""
        self.percal_reset()

    # ------------------------------------------------------------------
    # Load saved scores
    # ------------------------------------------------------------------
    def percal_load_scores(self):
        """Fill Written / Quiz / Exam from the student's saved records.
        Anything that is not saved stays empty."""
        self.percal_reset()

        if not self.selected_student_number:
            self.percal_show_result_error("Please select a student first.")
            return False
        subject = self.percal_subject_dropdown.get()
        if not subject:
            self.percal_show_result_error("Please select a subject first.")
            return False

        period = self.percal_period_dropdown.get()
        try:
            data = get_period_components(
                self.selected_student_number,
                self.year_dropdown.get(),
                self.semester_dropdown.get(),
                subject,
                period,
            )
        except Exception as e:
            self.percal_show_result_error(f"Database error: {e}")
            return False

        if data is None:
            self.percal_show_result_error(
                "No record for this student in that subject and term."
            )
            return False

        missing = []
        for label, key, entry in (
            ("Written", "written", self.percal_written_works),
            ("Quiz/PTask", "quiz", self.percal_quiz_ptask),
            ("Exam", "exam", self.percal_exam),
        ):
            if data[key] is None:
                missing.append(label)
            else:
                entry.insert(0, f"{data[key]:.2f}")

        if missing:
            self.percal_show_result_error(
                f"Nothing saved in {period} for: " + ", ".join(missing) + "."
            )
            return False
        return True

    # ------------------------------------------------------------------
    # Light / Dark mode
    # ------------------------------------------------------------------
    def apply_theme(self, theme, ribbon_photo=None, ribbon_photo_white=None):
        self.current_theme = theme
        dark = theme["window"] == "#1e1e1e"
        window_bg = theme["window"]
        table_bg = theme["table"]
        list_bg = theme["list"]
        text_fg = theme["text"]
        sidebar_bg = theme["sidebar"]

        self.configure(bg=window_bg)

        # Left panel
        self.percal_calculator_frame.configure(bg=table_bg)
        self.percal_below_sep.configure(bg=window_bg)
        self.percal_below_sep3.configure(bg=window_bg)

        for label in (
            self.percal_subject_label, self.year_caption, self.section_caption,
            self.section_info, self.student_caption, self.semester_caption,
            self.subject_caption, self.period_caption,
        ):
            label.configure(bg=table_bg, fg=text_fg)
        self.student_hint.configure(
            bg=table_bg, fg="#ff9999" if dark else "#990000"
        )

        for label in (
            [self.percal_enter_grades_label]
            + self.percal_captions
            + self.percal_max_labels
        ):
            label.configure(bg=window_bg, fg=text_fg)

        for entry in (
            self.percal_written_works, self.percal_quiz_ptask, self.percal_exam,
            *self.percal_max_entries.values(),
        ):
            entry.configure(
                bg=list_bg, fg=text_fg, insertbackground=text_fg,
            )

        for separator in (
            self.percal_separator, self.percal_separator3,
            self.percal_res_separator,
        ):
            separator.configure(bg=text_fg)

        for button in (
            self.percal_load_button, self.percal_calculator_button,
            self.percal_save_button, self.percal_cancel_button,
        ):
            button.configure(
                bg=table_bg, fg=text_fg,
                activebackground=sidebar_bg, activeforeground=text_fg,
            )

        # Dropdowns
        style = ttk.Style(self)
        style.configure(
            "Period.TCombobox",
            fieldbackground=list_bg, background=table_bg,
            foreground=text_fg, arrowcolor=text_fg,
        )
        style.map(
            "Period.TCombobox",
            fieldbackground=[("readonly", list_bg), ("disabled", table_bg)],
            foreground=[("readonly", text_fg), ("disabled", text_fg)],
            selectbackground=[("readonly", list_bg)],
            selectforeground=[("readonly", text_fg)],
        )
        for dropdown in (
            self.year_dropdown, self.section_dropdown, self.student_dropdown,
            self.semester_dropdown, self.percal_subject_dropdown,
            self.percal_period_dropdown,
        ):
            dropdown.configure(style="Period.TCombobox")

        # Results panel
        self.percal_result_frame.configure(bg=table_bg)
        self.percal_result_text.configure(bg=table_bg, fg=text_fg)
        self.percal_save_target.configure(bg=table_bg, fg=text_fg)
        self.percal_below_res_sep.configure(bg=window_bg)
        self.percal_score_heading.configure(bg=window_bg, fg=text_fg)
        self.percal_score_value.configure(bg=window_bg, fg=text_fg)

        # Keep the PASSED / FAILED / ERROR colors meaningful
        status_text = self.percal_status_result.cget("text")
        if status_text.startswith("ERROR:"):
            self.percal_status_result.configure(
                bg="#5b2020" if dark else "#ffcccc",
                fg="#ffdada" if dark else "#990000",
            )
        elif self.percal_current_result is not None:
            if self.percal_current_result["status"] == "PASSED":
                self.percal_status_result.configure(bg="#91ff00", fg="black")
            else:
                self.percal_status_result.configure(bg="#ff3333", fg="white")
        else:
            self.percal_status_result.configure(bg=window_bg, fg=text_fg)