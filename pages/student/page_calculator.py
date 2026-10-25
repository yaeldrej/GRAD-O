# page_calculator.py
import tkinter as tk
from tkinter import ttk
from core.config import SUBJECT_GROUPS, LIGHT_MODE, GLOBAL_EQUIVALENCY_DATA
from logic.entrylimitor import validate_input
from logic.calculator_logic import calculate_grades
from core.database import get_subject_period_grades

# Subjects per (year, semester), e.g. ("3rd Year", "1st Semester") -> [...]
TERM_SUBJECTS = {}
for _subjects, _year, _semester in SUBJECT_GROUPS.values():
    TERM_SUBJECTS[(_year, _semester)] = _subjects

YEARS = list(dict.fromkeys(y for _, y, _ in SUBJECT_GROUPS.values()))
SEMESTERS = list(dict.fromkeys(s for _, _, s in SUBJECT_GROUPS.values()))


class CalculatorPage(tk.Frame):

    def __init__(self, parent, ribbon_photo, on_save=None, on_delete=None, student_number=None):
        super().__init__(parent, bg=LIGHT_MODE["window"])

        # Kept so main.py's existing call signature still works
        self.on_save = on_save
        self.on_delete = on_delete
        self.student_number = student_number

        vcmd = (self.register(validate_input), "%P")


        # Calculator Box
        self.calculator_frame = tk.Frame(
            self,
            bg="#fff2bb",
            relief="solid",
            bd=2,
        )
        self.calculator_frame.place(relx=0, rely=0, x=15, y=15, relwidth=0.6, relheight=1, height=-30, width=-22)

                # Bigger text in the dropdown lists
        self.option_add("*TCombobox*Listbox.font", ("Arial", 13))

        self.subject_label = tk.Label(
            self.calculator_frame,
            text="Select Subject",
            bg="#fff2bb",
            font=("Arial", 20, "bold"),
        )
        self.subject_label.place(relx=0.04, rely=0.015, anchor="nw")

        # Small captions above each dropdown
        self.year_caption = tk.Label(
            self.calculator_frame, text="YEAR LEVEL",
            bg="#fff2bb", fg="black", font=("Arial", 10, "bold"),
        )
        self.year_caption.place(relx=0.04, rely=0.085, anchor="nw")

        self.semester_caption = tk.Label(
            self.calculator_frame, text="SEMESTER",
            bg="#fff2bb", fg="black", font=("Arial", 10, "bold"),
        )
        self.semester_caption.place(relx=0.38, rely=0.085, anchor="nw")

        self.subject_caption = tk.Label(
            self.calculator_frame, text="SUBJECT",
            bg="#fff2bb", fg="black", font=("Arial", 10, "bold"),
        )
        self.subject_caption.place(relx=0.72, rely=0.085, anchor="nw")

        self.year_dropdown = ttk.Combobox(
            self.calculator_frame,
            values=YEARS,
            state="readonly",
            font=("Arial", 13),
        )
        self.year_dropdown.set(YEARS[0])
        self.year_dropdown.place(relx=0.04, rely=0.125, relwidth=0.26, height=34)
        self.year_dropdown.bind("<<ComboboxSelected>>", self.on_term_change)

        self.semester_dropdown = ttk.Combobox(
            self.calculator_frame,
            values=SEMESTERS,
            state="readonly",
            font=("Arial", 13),
        )
        self.semester_dropdown.set(SEMESTERS[0])
        self.semester_dropdown.place(relx=0.38, rely=0.125, relwidth=0.26, height=34)
        self.semester_dropdown.bind("<<ComboboxSelected>>", self.on_term_change)

        self.subject_dropdown = ttk.Combobox(
            self.calculator_frame,
            values=TERM_SUBJECTS.get((YEARS[0], SEMESTERS[0]), []),
            state="readonly",
            font=("Arial", 13),
        )
        self.subject_dropdown.place(relx=0.72, rely=0.125, relwidth=0.26, height=34)
        self.subject_dropdown.bind("<<ComboboxSelected>>", self.load_subject_grades)
        self.separator = tk.Frame(
            self.calculator_frame, height=2, bg="#000000"
        )
        self.separator.place(relx=0.001, rely=0.2, relwidth=1)

        self.below_sep = tk.Frame(self.calculator_frame, bg="#f5f5dc")
        self.below_sep.place(relx=0, rely=0.203, relwidth=1, relheight=0.797)

        self.enter_grades_label = tk.Label(
            self.below_sep,
            text="Enter Grades",
            bg="#f5f5dc",
            font=("Arial", 20, "bold"),
        )
        self.enter_grades_label.place(relx=0.05, rely=0.05, anchor="nw")

        # Period Grades
        self.period1 = tk.Entry(
            self.below_sep,
            width=10,
            font=("Arial", 15),
            validate="key",
            validatecommand=vcmd,
            justify="center",
        )
        self.period1.place(relx=0.04, rely=0.300, relwidth=0.26, height=50)

        self.period2 = tk.Entry(
            self.below_sep,
            width=10,
            font=("Arial", 15),
            validate="key",
            validatecommand=vcmd,
            justify="center",
        )
        self.period2.place(relx=0.38, rely=0.300, relwidth=0.26, height=50)

        self.period3 = tk.Entry(
            self.below_sep,
            width=10,
            font=("Arial", 15),
            validate="key",
            validatecommand=vcmd,
            justify="center",
        )
        self.period3.place(relx=0.72, rely=0.300, relwidth=0.26, height=50)

        self.period1_text = tk.Label(
            self.below_sep,
            text="PERIOD 1",
            bg="#f5f5dc",
            font=("Arial", 15, "bold"),
        )
        self.period1_text.place(relx=0.04, rely=0.195)

        self.period2_text = tk.Label(
            self.below_sep,
            text="PERIOD 2",
            bg="#f5f5dc",
            font=("Arial", 15, "bold"),
        )
        self.period2_text.place(relx=0.38, rely=0.195)

        self.period3_text = tk.Label(
            self.below_sep,
            text="PERIOD 3",
            bg="#f5f5dc",
            font=("Arial", 15, "bold"),
        )
        self.period3_text.place(relx=0.72, rely=0.195)

        self.equiv_title = tk.Label(
            self.below_sep,
            text="GRADE EQUIVALENCY",
            font=("Titillium Web", 14, "bold"),
            bg="#f5f5dc",
            fg="black",
        )
        self.equiv_title.place(relx=0.04, rely=0.44, anchor="nw")

        self.equiv_frame = tk.Frame(self.below_sep, bg="#f5f5dc")
        self.equiv_frame.place(relx=0.04, rely=0.51, relwidth=0.92, relheight=0.34)
        for col in range(3):
            self.equiv_frame.columnconfigure(col, weight=1, uniform="eq")

        self.equiv_cells = []
        for r, row_data in enumerate(GLOBAL_EQUIVALENCY_DATA):
            self.equiv_frame.rowconfigure(r, weight=1, uniform="eqrows")
            for c, text in enumerate(row_data):
                cell = tk.Label(
                    self.equiv_frame,
                    text=text,
                    font=("Titillium Web", 10, "bold" if r == 0 else "normal"),
                    bg="#fff2bb",
                    fg="black",
                    relief="solid",
                    bd=1,
                )
                cell.grid(row=r, column=c, sticky="nsew")
                self.equiv_cells.append(cell)
                
        # Calculate Button Separator
        self.separator3 = tk.Frame(
            self.calculator_frame,
            height=2,
            bg="#000000",
        )
        self.separator3.place(relx=0.05, rely=0.90, relwidth=0.9)

        self.below_sep3 = tk.Frame(
            self.calculator_frame,
            bg="#f5f5dc",
        )
        self.below_sep3.place(
            relx=0, rely=0.903,
            relwidth=1, relheight=0.097,
        )

        # Results Panel
        self.result_frame = tk.Frame(
            self,
            bg="#fff2bb",
            borderwidth=2,
            relief="solid",
        )

        self.result_text = tk.Label(
            self.result_frame,
            text="RESULTS",
            bg="#fff2bb",
            fg="black",
            font=("Titillium Web", 15, "bold"),
        )
        self.result_text.pack(fill="x", pady=20, padx=10, anchor="nw")

        self.res_separator = tk.Frame(
            self.result_frame,
            height=2,
            bg="#000000",
        )
        self.res_separator.place(relx=0.001, rely=0.2, relwidth=1)

        self.below_res_sep = tk.Frame(
            self.result_frame,
            bg="#f5f5dc",
        )
        self.below_res_sep.place(
            relx=0, rely=0.203,
            relwidth=1, relheight=0.797,
        )

        self.final_grade_heading = tk.Label(
            self.below_res_sep,
            text="FINAL GRADE",
            font=("Titillium Web", 11, "bold"),
            bg="#f5f5dc",
            fg="black",
        )
        self.final_grade_heading.place(relx=0.03, rely=0.03, relwidth=0.45)

        self.grade_point_heading = tk.Label(
            self.below_res_sep,
            text="GRADE POINT",
            font=("Titillium Web", 11, "bold"),
            bg="#f5f5dc",
            fg="black",
        )
        self.grade_point_heading.place(relx=0.52, rely=0.03, relwidth=0.45)

        self.result_vertical_separator = tk.Frame(
            self.below_res_sep,
            width=2,
            bg="#000000",
        )
        self.result_vertical_separator.place(
            relx=0.5, rely=0.02, relheight=0.35
        )

        self.final_grade_value = tk.Label(
            self.below_res_sep,
            text="--",
            font=("Titillium Web", 22, "bold"),
            bg="#f5f5dc",
            fg="black",
        )
        self.final_grade_value.place(relx=0.03, rely=0.20, relwidth=0.45)

        self.grade_point_value = tk.Label(
            self.below_res_sep,
            text="--",
            font=("Titillium Web", 22, "bold"),
            bg="#f5f5dc",
            fg="black",
        )
        self.grade_point_value.place(relx=0.52, rely=0.20, relwidth=0.45)

        self.status_result = tk.Label(
            self.below_res_sep,
            text="",
            font=("Titillium Web", 12, "bold"),
            bg="#f5f5dc",
            fg="black",
            anchor="center",
            justify="center",
            padx=10,
        )
        self.status_result.place(
            relx=0.5, rely=0.6,
            relwidth=0.88, height=60,
            anchor="center",
        )

        # Store Result Information
        self.current_result = None
        self.saved_results = []

        # Calculate Button
        self.calculator_button = tk.Button(
            self.below_sep3,
            text="🖩 CALCULATE",
            bg="#fff2bb",
            fg="black",
            activebackground="#887b40",
            activeforeground="black",
            command=self.click_calculate_button,
        )
        self.calculator_button.place(relx=0.05, rely=0.1, relwidth=0.9, relheight=0.8)
        self.bind("<Configure>", self.update_popup_position)
        for entry in (self.period1, self.period2, self.period3):
            entry.config(readonlybackground="white")
        self.clear_period_entries()
        self.place_result_panel()

    def on_term_change(self, event=None):
        key = (self.year_dropdown.get(), self.semester_dropdown.get())
        self.subject_dropdown["values"] = TERM_SUBJECTS.get(key, [])
        self.subject_dropdown.set("")
        self.clear_period_entries()

    def update_popup_position(self, event=None):
        if event is not None and event.widget is not self:
            return
        if self.result_frame.winfo_ismapped():
            self.place_result_panel()

    # Position the Results Panel on the Right
    def place_result_panel(self):
        self.result_frame.place(
            relx=0.6, rely=0, x=7, y=15,
            relwidth=0.4, relheight=1,
            width=-22, height=-30,
        )
        self.result_frame.lift()

    # Convert Final Grade to Grade Point
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

        # Make Sure a Subject Is Selected
        if not self.subject_dropdown.get():
            self.show_result_error("Please select a subject first.")
            return
        
        if not any(
            e.get().strip() for e in (self.period1, self.period2, self.period3)
        ):
            self.current_result = None
            self.final_grade_value.config(text="--")
            self.grade_point_value.config(text="--")
            self.show_result_error("No grades recorded for this subject yet.")
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
                raise ValueError(
                    "The final grade must be between 0 and 100."
                )

            if result.get("grade_point") is not None:
                grade_point = float(result["grade_point"])
            else:
                grade_point = self.get_grade_point(final_grade)

            # Determine Passing Status
            if grade_point <= 3.0:
                status = "PASSED"
                status_bg = "#91ff00"
                status_fg = "black"
            else:
                status = "FAILED"
                status_bg = "#ff3333"
                status_fg = "white"

            # Format Grade Point to Match the Equivalency Table
            point_display = {
                1.0: "1.0",
                1.25: "1.25",
                1.5: "1.50",
                1.75: "1.75",
                2.0: "2.0",
                2.25: "2.25",
                2.5: "2.50",
                2.75: "2.75",
                3.0: "3.0",
                3.25: "3.25",
            }

            # Update the Results Labels
            self.final_grade_value.config(text=f"{final_grade:.2f}")
            self.grade_point_value.config(
                text=point_display.get(grade_point, f"{grade_point:.2f}")
            )
            self.status_result.config(
                text=f"● {status}",
                bg=status_bg,
                fg=status_fg,
            )

            # Store the Current Result
            self.current_result = {
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

        # Show the Results Panel
        self.place_result_panel()

    # Display an Error in the Results Panel
    
    def show_result_error(self, error):
        theme = getattr(self, "current_theme", LIGHT_MODE)

        if theme["window"] == "#1e1e1e":
            error_bg = "#5b2020"
            error_fg = "#ffdada"
        else:
            error_bg = "#ffcccc"
            error_fg = "#990000"

    # Keep the entire results panel consistent with the active theme.
        self.result_frame.configure(bg=theme["table"])
        self.result_text.configure(
            text="RESULTS",
            bg=theme["table"],
            fg=theme["text"],
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
            text=f"ERROR: {error}",
            bg=error_bg,
            fg=error_fg,
            wraplength=400,
    )
        self.place_result_panel()

    # Apply Light / Dark Mode
    def apply_theme(self, theme, ribbon_photo=None, ribbon_photo_white=None):

        self.current_theme = theme

        self.equiv_title.configure(bg=theme["window"], fg=theme["text"])
        self.equiv_frame.configure(bg=theme["window"])
        for cell in self.equiv_cells:
            cell.configure(bg=theme["table"], fg=theme["text"])

        self.configure(bg=theme["window"])

        # Calculator Frames
        self.calculator_frame.configure(bg=theme["table"])
        self.below_sep.configure(bg=theme["window"])
        self.below_sep3.configure(bg=theme["window"])

        # Subject Label
        self.subject_label.configure(
            bg=theme["table"], fg=theme["text"]
        )
        
        # Captions above the dropdowns
        for label in (
            self.year_caption,
            self.semester_caption,
            self.subject_caption,
        ):
            label.configure(bg=theme["table"], fg=theme["text"])

        # Enter Grades Label
        self.enter_grades_label.configure(
            bg=theme["table"], fg=theme["text"]
        )

        # Period Labels
        for label in (
            self.enter_grades_label,
            self.period1_text,
            self.period2_text,
            self.period3_text,
        ):
            label.configure(bg=theme["window"], fg=theme["text"])

        # Grade Entry fields
        for entry in (
            self.period1,
            self.period2,
            self.period3,
        ):
            entry.configure(
                bg=theme["table"],
                fg=theme["text"],
                insertbackground=theme["text"],
                readonlybackground=theme["table"],
            )

        # Separators
        for separator in (
            self.separator,
            self.separator3,
            self.res_separator,
            self.result_vertical_separator,
        ):
            separator.configure(
                bg=theme["text"]
            )

        # Calculate Button
        self.calculator_button.configure(
            bg=theme["table"], fg=theme["text"], activebackground=theme["sidebar"], activeforeground=theme["text"]
        )

        # Result Frame or the Panel
        self.result_frame.configure(bg=theme["table"])
        self.below_res_sep.configure(bg=theme["window"])

        self.result_text.configure(
            bg=theme["table"], fg=theme["text"]
        )

        # Result Headings
        for label in (
            self.final_grade_heading,
            self.grade_point_heading,
            self.final_grade_value,
            self.grade_point_value,
        ):
            label.configure(
               bg=theme["window"], fg=theme["text"]
            )

        # Preserve the current result status or error message
        status_text = self.status_result.cget("text")

        if status_text.startswith("ERROR:"):
            if theme["window"] == "#1e1e1e":
                error_bg = "#5b2020"
                error_fg = "#ffdada"
            else:
                error_bg = "#ffcccc"
                error_fg = "#990000"

            self.status_result.configure(
                bg=error_bg,
                fg=error_fg
            )
        elif self.current_result is not None and self.current_result.get("status"):
            if self.current_result["status"] == "PASSED":
                self.status_result.configure(
                    bg="#91ff00",
                    fg="black"
                )

            else:
                self.status_result.configure(
                    bg="#ff3333",
                    fg="white"
                )
        else:
            self.status_result.configure(
                bg=theme["window"],
                fg=theme["text"]
            )

        # The panel stays anchored to the right edge on its own, so a theme
        # change only needs to recolor it. Just keep it above the logo.
        if self.result_frame.winfo_ismapped():
            self.result_frame.lift()
            
    

    def _set_entry(self, entry, value):
        """Fill an entry from the database, then lock it for a logged-in student."""
        entry.config(state="normal", validate="none")
        entry.delete(0, tk.END)
        if value and value > 0:
            entry.insert(0, f"{value:.2f}")
        entry.config(validate="key")
        if self.student_number:
            entry.config(state="readonly")

    def clear_period_entries(self):
        for entry in (self.period1, self.period2, self.period3):
            self._set_entry(entry, 0)

    def load_subject_grades(self, event=None):
        subject = self.subject_dropdown.get()
        if not subject:
            return

        if not self.student_number:
            self.clear_period_entries()
            return

        try:
            grades = get_subject_period_grades(
                self.student_number,
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
        
    
