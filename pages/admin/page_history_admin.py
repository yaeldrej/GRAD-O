# page_history_admin.py
import tkinter as tk
from tkinter import ttk

from core.config import LIGHT_MODE, SUBJECT_GROUPS
from core.database import (
    get_history_grades,
    get_section_counts,
    get_students_in_section,
    SECTION_COUNT,
    SECTION_CAPACITY,
)

# Subjects per (year, semester)
TERM_SUBJECTS = {}
for _subjects, _year, _semester in SUBJECT_GROUPS.values():
    TERM_SUBJECTS[(_year, _semester)] = _subjects

YEARS = list(dict.fromkeys(y for _, y, _ in SUBJECT_GROUPS.values()))
SEMESTERS = list(dict.fromkeys(s for _, _, s in SUBJECT_GROUPS.values()))

STUDENT_PLACEHOLDER = "Select a section first"


class HistoryPage(tk.Frame):

    def __init__(self, parent, ribbon_photo=None, student_number=None,
                 allow_search=True, **kwargs):
        super().__init__(parent, bg=LIGHT_MODE["window"])

        self.current_theme = LIGHT_MODE

        # Students of the chosen section: display name -> student number
        self.student_map = {}
        self.all_student_names = []
        self.selected_student_number = None

        # Bigger text in the dropdown lists
        self.option_add("*TCombobox*Listbox.font", ("Arial", 13))

        # ---------------- Left panel ----------------
        self.history_main_frame = tk.Frame(
            self, bg="#fff2bb", relief="solid", bd=2
        )
        self.history_main_frame.place(
            relx=0, rely=0, x=15, y=15,
            relwidth=0.6, relheight=1, height=-30, width=-22,
        )

        self.history_section_title = tk.Label(
            self.history_main_frame, text="Grade History",
            font=("Arial", 20, "bold"), bg="#fff2bb", fg="black",
        )
        self.history_section_title.place(relx=0.04, rely=0.012, anchor="nw")

        # ---- Row 1: year level -> section -> student ----
        self.year_caption = self._caption("YEAR LEVEL", 0.04, 0.072)
        self.section_caption = self._caption("SECTION", 0.30, 0.072)
        self.student_caption = self._caption("STUDENT NAME", 0.56, 0.072)

        self.section_info = tk.Label(
            self.history_main_frame, text="",
            bg="#fff2bb", fg="black", font=("Arial", 9, "italic"),
        )
        self.section_info.place(relx=0.39, rely=0.073, anchor="nw")

        self.student_hint = tk.Label(
            self.history_main_frame, text="",
            bg="#fff2bb", fg="#990000", font=("Arial", 9, "italic"),
        )
        self.student_hint.place(relx=0.69, rely=0.073, anchor="nw")

        self.year_dropdown = ttk.Combobox(
            self.history_main_frame, values=YEARS, state="readonly",
            font=("Arial", 13),
        )
        self.year_dropdown.set(YEARS[0])
        self.year_dropdown.place(relx=0.04, rely=0.100, relwidth=0.22, height=34)
        self.year_dropdown.bind("<<ComboboxSelected>>", self.on_year_change)

        self.section_dropdown = ttk.Combobox(
            self.history_main_frame, values=[], state="readonly",
            font=("Arial", 13), postcommand=self.refresh_section_labels,
        )
        self.section_dropdown.place(relx=0.30, rely=0.100, relwidth=0.22, height=34)
        self.section_dropdown.bind("<<ComboboxSelected>>", self.on_section_selected)

        self.student_dropdown = ttk.Combobox(
            self.history_main_frame, values=[], font=("Arial", 13),
        )
        self.student_dropdown.place(relx=0.56, rely=0.100, relwidth=0.42, height=34)
        self.student_dropdown.bind("<KeyRelease>", self.on_student_typed)
        self.student_dropdown.bind("<<ComboboxSelected>>", self.on_student_chosen)
        self.student_dropdown.bind("<Return>", self.on_student_chosen)
        self.student_dropdown.bind("<FocusOut>", self.on_student_chosen)
        self.lock_student_dropdown(STUDENT_PLACEHOLDER)

        # ---- Row 2: semester ----
        self.semester_caption = self._caption("SEMESTER", 0.04, 0.165)

        self.semester_dropdown = ttk.Combobox(
            self.history_main_frame, values=SEMESTERS, state="readonly",
            font=("Arial", 13),
        )
        self.semester_dropdown.set(SEMESTERS[0])
        self.semester_dropdown.place(relx=0.04, rely=0.193, relwidth=0.48, height=34)
        self.semester_dropdown.bind("<<ComboboxSelected>>", self.on_semester_change)

        self.history_separator = tk.Frame(
            self.history_main_frame, height=2, bg="#000000"
        )
        self.history_separator.place(relx=0.001, rely=0.265, relwidth=1)

        self.history_below = tk.Frame(self.history_main_frame, bg="#f5f5dc")
        self.history_below.place(relx=0, rely=0.268, relwidth=1, relheight=0.732)

        self.history_subtitle = tk.Label(
            self.history_below, text="SUBJECTS",
            font=("Arial", 16, "bold"), bg="#f5f5dc", fg="black",
        )
        self.history_subtitle.place(relx=0.04, rely=0.02, anchor="nw")

        # Table + scrollbar
        self.history_table_frame = tk.Frame(
            self.history_below, bg="#fff2bb", relief="solid", bd=1
        )
        self.history_table_frame.place(
            relx=0.04, rely=0.09, relwidth=0.92, relheight=0.87
        )

        self.history_scrollbar = tk.Scrollbar(
            self.history_table_frame, orient=tk.VERTICAL
        )
        self.history_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree = ttk.Treeview(
            self.history_table_frame,
            columns=("Subject", "P1", "P2", "P3", "Overall"),
            show="headings",
            style="History.Treeview",
            yscrollcommand=self.history_scrollbar.set,
        )
        self.tree.heading("Subject", text="SUBJECTS")
        self.tree.heading("P1", text="P₁")
        self.tree.heading("P2", text="P₂")
        self.tree.heading("P3", text="P₃")
        self.tree.heading("Overall", text="OVERALL GRADE")

        self.tree.column("Subject", width=140, anchor="center")
        self.tree.column("P1", width=90, anchor="center")
        self.tree.column("P2", width=90, anchor="center")
        self.tree.column("P3", width=90, anchor="center")
        self.tree.column("Overall", width=130, anchor="center")

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.history_scrollbar.config(command=self.tree.yview)

        # ---------------- Right panel: term summary ----------------
        self.summary_frame = tk.Frame(
            self, bg="#fff2bb", borderwidth=2, relief="solid"
        )
        self.summary_frame.place(
            relx=0.6, rely=0, x=7, y=15,
            relwidth=0.4, relheight=1, width=-22, height=-30,
        )

        self.summary_title = tk.Label(
            self.summary_frame, text="TERM SUMMARY",
            bg="#fff2bb", fg="black", font=("Titillium Web", 15, "bold"),
        )
        self.summary_title.pack(fill="x", pady=20, padx=10, anchor="nw")

        self.summary_separator = tk.Frame(
            self.summary_frame, height=2, bg="#000000"
        )
        self.summary_separator.place(relx=0.001, rely=0.2, relwidth=1)

        self.summary_below = tk.Frame(self.summary_frame, bg="#f5f5dc")
        self.summary_below.place(relx=0, rely=0.203, relwidth=1, relheight=0.797)

        self.avg_heading = tk.Label(
            self.summary_below, text="TERM AVERAGE",
            font=("Titillium Web", 11, "bold"), bg="#f5f5dc", fg="black",
        )
        self.avg_heading.place(relx=0.03, rely=0.03, relwidth=0.45)

        self.count_heading = tk.Label(
            self.summary_below, text="SUBJECTS GRADED",
            font=("Titillium Web", 11, "bold"), bg="#f5f5dc", fg="black",
        )
        self.count_heading.place(relx=0.52, rely=0.03, relwidth=0.45)

        self.summary_vertical_separator = tk.Frame(
            self.summary_below, width=2, bg="#000000"
        )
        self.summary_vertical_separator.place(relx=0.5, rely=0.02, relheight=0.30)

        self.avg_value = tk.Label(
            self.summary_below, text="--",
            font=("Titillium Web", 28, "bold"), bg="#f5f5dc", fg="black",
        )
        self.avg_value.place(relx=0.03, rely=0.12, relwidth=0.45)

        self.count_value = tk.Label(
            self.summary_below, text="--",
            font=("Titillium Web", 28, "bold"), bg="#f5f5dc", fg="black",
        )
        self.count_value.place(relx=0.52, rely=0.12, relwidth=0.45)

        self.details_title = tk.Label(
            self.summary_below, text="DETAILS",
            font=("Titillium Web", 14, "bold"), bg="#f5f5dc", fg="black",
        )
        self.details_title.place(relx=0.06, rely=0.36, anchor="nw")

        self.details_frame = tk.Frame(self.summary_below, bg="#f5f5dc")
        self.details_frame.place(relx=0.06, rely=0.42, relwidth=0.88, relheight=0.32)
        self.details_frame.columnconfigure(0, weight=1, uniform="dt")
        self.details_frame.columnconfigure(1, weight=2, uniform="dt")

        self.details_cells = []
        self.details_values = {}
        for row, name in enumerate(("STUDENT", "TERM", "HIGHEST", "LOWEST")):
            self.details_frame.rowconfigure(row, weight=1, uniform="dtrows")
            name_cell = tk.Label(
                self.details_frame, text=name,
                font=("Titillium Web", 12, "bold"),
                bg="#fff2bb", fg="black", relief="solid", bd=1,
            )
            name_cell.grid(row=row, column=0, sticky="nsew")
            value_cell = tk.Label(
                self.details_frame, text="--",
                font=("Titillium Web", 12),
                bg="#fff2bb", fg="black", relief="solid", bd=1,
            )
            value_cell.grid(row=row, column=1, sticky="nsew")
            self.details_cells += [name_cell, value_cell]
            self.details_values[name] = value_cell

        self._style_tree(LIGHT_MODE)
        self.refresh_section_labels()
        self.reset_summary()

    # ------------------------------------------------------------------
    # Small helpers
    # ------------------------------------------------------------------
    def _caption(self, text, relx, rely):
        label = tk.Label(
            self.history_main_frame, text=text,
            bg="#fff2bb", fg="black", font=("Arial", 10, "bold"),
        )
        label.place(relx=relx, rely=rely, anchor="nw")
        return label

    def _style_tree(self, theme):
        style = ttk.Style(self)
        style.configure(
            "History.Treeview",
            background=theme["list"],
            fieldbackground=theme["list"],
            foreground=theme["text"],
            rowheight=38,
            font=("Arial", 13),
        )
        style.configure(
            "History.Treeview.Heading",
            background=theme["table"],
            foreground=theme["text"],
            font=("Arial", 12, "bold"),
        )
        style.map(
            "History.Treeview",
            background=[("selected", theme["sidebar"])],
            foreground=[("selected", theme["text"])],
        )
        self.tree.tag_configure("odd", background=theme["table"])
        self.tree.tag_configure("even", background=theme["list"])

    def term_text(self):
        return f"{self.year_dropdown.get()} - {self.semester_dropdown.get()}"

    # ------------------------------------------------------------------
    # Year level -> section -> student
    # ------------------------------------------------------------------
    def on_year_change(self, event=None):
        """A new year level means a new set of sections and students."""
        self.section_dropdown.set("")
        self.section_info.config(text="")
        self.reset_students()
        self.refresh_section_labels()

    def on_semester_change(self, event=None):
        self.load_history_table()

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
        self.load_history_table()

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
        if self.selected_student_number:
            self.load_history_table()

    def refresh_terms(self):
        """Kept for the old call: reload the table."""
        self.load_history_table()

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
                self.selected_student_number = None
                self.load_history_table()
            self.student_hint.config(text="Student not found" if typed else "")
            return

        self.student_hint.config(text="")
        if number != self.selected_student_number:
            self.selected_student_number = number
            self.load_history_table()

    # ------------------------------------------------------------------
    # Summary panel
    # ------------------------------------------------------------------
    def reset_summary(self):
        student = (
            self.student_dropdown.get().strip()
            if self.selected_student_number else "--"
        )
        self.avg_value.config(text="--")
        self.count_value.config(text="--")
        self.details_values["STUDENT"].config(text=student)
        self.details_values["TERM"].config(text=self.term_text())
        self.details_values["HIGHEST"].config(text="--")
        self.details_values["LOWEST"].config(text="--")

    def update_summary(self, graded, total):
        """graded is a list of (subject code, overall grade as a number)."""
        self.details_values["STUDENT"].config(
            text=self.student_dropdown.get().strip()
        )
        self.details_values["TERM"].config(text=self.term_text())
        self.count_value.config(text=f"{len(graded)} / {total}")

        if not graded:
            self.avg_value.config(text="--")
            self.details_values["HIGHEST"].config(text="--")
            self.details_values["LOWEST"].config(text="--")
            return

        average = sum(grade for _, grade in graded) / len(graded)
        best = max(graded, key=lambda item: item[1])
        worst = min(graded, key=lambda item: item[1])

        self.avg_value.config(text=f"{average:.2f}")
        self.details_values["HIGHEST"].config(text=f"{best[0]}  -  {best[1]:.2f}")
        self.details_values["LOWEST"].config(text=f"{worst[0]}  -  {worst[1]:.2f}")

    # ------------------------------------------------------------------
    # Table
    # ------------------------------------------------------------------
    def load_history_table(self):
        """Show the chosen student's grades for the chosen year and semester."""
        for item in self.tree.get_children():
            self.tree.delete(item)

        year_level = self.year_dropdown.get()
        semester = self.semester_dropdown.get()
        subject_list = TERM_SUBJECTS.get((year_level, semester), [])
        student_no = self.selected_student_number

        if not subject_list or not student_no:
            self.reset_summary()
            return

        try:
            db_records = get_history_grades(
                student_number=student_no,
                year_level=year_level,
                semester=semester,
            )
        except Exception as e:
            print(f"[DEBUG] Database fetch error: {e}")
            db_records = {}

        def to_number(val):
            try:
                num = float(val)
                return num if num > 0 else None
            except (ValueError, TypeError):
                return None

        def format_val(val):
            num = to_number(val)
            return f"{num:.2f}" if num is not None else "-"

        graded = []
        for index, code in enumerate(subject_list):
            if code in db_records:
                rec = db_records[code]
                p1_str = format_val(rec.get("p1"))
                p2_str = format_val(rec.get("p2"))
                p3_str = format_val(rec.get("p3"))
                overall_str = format_val(rec.get("overall"))

                overall_num = to_number(rec.get("overall"))
                if overall_num is not None:
                    graded.append((code, overall_num))
            else:
                p1_str = p2_str = p3_str = overall_str = "-"

            self.tree.insert(
                "", "end",
                values=(code, p1_str, p2_str, p3_str, overall_str),
                tags=("odd" if index % 2 else "even",),
            )

        self.update_summary(graded, len(subject_list))

    # ------------------------------------------------------------------
    # Theme
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
        self.history_main_frame.configure(bg=table_bg)
        for label in (
            self.history_section_title, self.year_caption, self.section_caption,
            self.section_info, self.student_caption, self.semester_caption,
        ):
            label.configure(bg=table_bg, fg=text_fg)
        self.student_hint.configure(
            bg=table_bg, fg="#ff9999" if dark else "#990000"
        )

        self.history_below.configure(bg=window_bg)
        self.history_subtitle.configure(bg=window_bg, fg=text_fg)
        self.history_table_frame.configure(bg=list_bg)
        self.history_scrollbar.configure(
            bg=table_bg, troughcolor=list_bg, activebackground=sidebar_bg
        )
        self._style_tree(theme)

        # Dropdowns
        style = ttk.Style(self)
        style.configure(
            "History.TCombobox",
            fieldbackground=list_bg, background=table_bg,
            foreground=text_fg, arrowcolor=text_fg,
        )
        style.map(
            "History.TCombobox",
            fieldbackground=[("readonly", list_bg), ("disabled", table_bg)],
            foreground=[("readonly", text_fg), ("disabled", text_fg)],
            selectbackground=[("readonly", list_bg)],
            selectforeground=[("readonly", text_fg)],
        )
        for dropdown in (
            self.year_dropdown, self.section_dropdown,
            self.student_dropdown, self.semester_dropdown,
        ):
            dropdown.configure(style="History.TCombobox")

        # Right panel
        self.summary_frame.configure(bg=table_bg)
        self.summary_title.configure(bg=table_bg, fg=text_fg)
        self.summary_below.configure(bg=window_bg)
        for label in (
            self.avg_heading, self.count_heading,
            self.avg_value, self.count_value, self.details_title,
        ):
            label.configure(bg=window_bg, fg=text_fg)
        self.details_frame.configure(bg=window_bg)
        for cell in self.details_cells:
            cell.configure(bg=table_bg, fg=text_fg)

        for separator in (
            self.history_separator,
            self.summary_separator,
            self.summary_vertical_separator,
        ):
            separator.configure(bg=text_fg)