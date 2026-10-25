# page_history.py
import tkinter as tk
from tkinter import ttk

from core.config import LIGHT_MODE,  SUBJECT_GROUPS
from core.database import (
    get_history_grades,
    get_student_grades_by_category,
    get_db_connection,
    get_current_term_index,
)


class HistoryPage(tk.Frame):

    def __init__(self, parent, ribbon_photo=None, student_number=None):
        super().__init__(parent, bg=LIGHT_MODE["window"])

        self.student_number = student_number

        # Bigger text in the dropdown list
        self.option_add("*TCombobox*Listbox.font", ("Arial", 13))

        # ---------------- Left panel: the history table ----------------
        self.history_main_frame = tk.Frame(
            self, bg="#fff2bb", relief="solid", bd=2
        )
        self.history_main_frame.place(
            relx=0, rely=0, x=15, y=15,
            relwidth=0.6, relheight=1, height=-30, width=-22,
        )

        self.history_section_title = tk.Label(
            self.history_main_frame,
            text="Grade History",
            font=("Arial", 20, "bold"),
            bg="#fff2bb",
            fg="black",
        )
        self.history_section_title.place(relx=0.04, rely=0.015, anchor="nw")

        self.category_label = tk.Label(
            self.history_main_frame,
            text="TERM",
            font=("Arial", 10, "bold"),
            bg="#fff2bb",
            fg="black",
        )
        self.category_label.place(relx=0.04, rely=0.085, anchor="nw")

        self.term_dropdown = ttk.Combobox(
            self.history_main_frame,
            values=list(SUBJECT_GROUPS.keys()),
            state="readonly",
            font=("Arial", 13),
        )
        self.term_dropdown.place(relx=0.04, rely=0.125, relwidth=0.40, height=34)
        self.term_dropdown.set("1st Year - 1st Sem")
        self.term_dropdown.bind("<<ComboboxSelected>>", self.on_term_changed)

        self.history_separator = tk.Frame(
            self.history_main_frame, height=2, bg="#000000"
        )
        self.history_separator.place(relx=0.001, rely=0.2, relwidth=1)

        self.history_below = tk.Frame(self.history_main_frame, bg="#f5f5dc")
        self.history_below.place(relx=0, rely=0.203, relwidth=1, relheight=0.797)

        self.history_subtitle = tk.Label(
            self.history_below,
            text="GLOBAL SUBJECTS",
            font=("Arial", 16, "bold"),
            bg="#f5f5dc",
            fg="black",
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
            self.summary_frame,
            text="TERM SUMMARY",
            bg="#fff2bb",
            fg="black",
            font=("Titillium Web", 15, "bold"),
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
        self.details_frame.place(relx=0.06, rely=0.42, relwidth=0.88, relheight=0.24)
        self.details_frame.columnconfigure(0, weight=1, uniform="dt")
        self.details_frame.columnconfigure(1, weight=2, uniform="dt")

        self.details_cells = []
        self.details_values = {}
        for row, name in enumerate(("TERM", "HIGHEST", "LOWEST")):
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
        
        if self.student_number:
            self.refresh_terms()

    # --- TABLE STYLE ---
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
        # Alternating row colors
        self.tree.tag_configure("odd", background=theme["table"])
        self.tree.tag_configure("even", background=theme["list"])

    # --- UI EVENT HANDLERS ---
    def on_term_changed(self, event):
        selected_option = self.term_dropdown.get()

        if selected_option in SUBJECT_GROUPS:
            group_data = SUBJECT_GROUPS[selected_option]

            subject_list = group_data[0]
            year_level = (
                group_data[1][0]
                if isinstance(group_data[1], tuple)
                else str(group_data[1])
            )
            semester = (
                group_data[2][0]
                if isinstance(group_data[2], tuple)
                else str(group_data[2])
            )

            self.load_history_table(
                subject_list=subject_list,
                year_level=year_level,
                semester=semester,
            )

    # --- SUMMARY PANEL ---
    def reset_summary(self):
        self.avg_value.config(text="--")
        self.count_value.config(text="--")
        self.details_values["TERM"].config(text=self.term_dropdown.get() or "--")
        self.details_values["HIGHEST"].config(text="--")
        self.details_values["LOWEST"].config(text="--")

    def update_summary(self, graded, total):
        """graded is a list of (subject code, overall grade as a number)."""
        self.details_values["TERM"].config(text=self.term_dropdown.get())
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

    # --- DATABASE AND TABLE POPULATION ---
    def load_history_table(
        self,
        student_no=None,
        subject_list=None,
        year_level="1st Year",
        semester="1st Semester",
    ):
        student_no = student_no or self.student_number

        # Clear previous treeview rows
        for item in self.tree.get_children():
            self.tree.delete(item)

        if not subject_list or not student_no:
            self.reset_summary()
            return

        # Fetch records from database
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

        # Populate rows
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

    # THEME PROPAGATION
    def apply_theme(self, theme, ribbon_photo=None, ribbon_photo_white=None):
        window_bg = theme["window"]
        table_bg = theme["table"]
        list_bg = theme["list"]
        text_fg = theme["text"]
        sidebar_bg = theme["sidebar"]

        self.configure(bg=window_bg)

        # Left panel
        self.history_main_frame.configure(bg=table_bg)
        for label in (self.history_section_title, self.category_label):
            label.configure(bg=table_bg, fg=text_fg)

        self.history_below.configure(bg=window_bg)
        self.history_subtitle.configure(bg=window_bg, fg=text_fg)
        self.history_table_frame.configure(bg=list_bg)
        self.history_scrollbar.configure(
            bg=table_bg, troughcolor=list_bg, activebackground=sidebar_bg
        )
        self._style_tree(theme)

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

    def set_student(self, student_number):
        """Call after login so the page knows whose grades to show."""
        self.student_number = student_number
        self.refresh_terms()

    def refresh(self):
        """Call every time the History page is opened."""
        self.refresh_terms()

    def refresh_terms(self):
        terms = list(SUBJECT_GROUPS.keys())
        self.term_dropdown["values"] = terms
        if self.term_dropdown.get() not in terms:
            self.term_dropdown.set(terms[0])
        self.on_term_changed(None)