#page_activity
import re
import tkinter as tk
from tkinter import ttk
from core.config import SUBJECT_GROUPS, LIGHT_MODE
from logic.page_activity_logic import calculate_overall_final_grade

CATEGORIES = ("Activity", "Quiz/PTask", "Exam", "Attendance")
TITLES = {
    "Activity": " Activities ",
    "Quiz/PTask": " Quizzes ",
    "Exam": " Exams ",
    "Attendance": " Attendance Records ",
}

# What a typed number may look like, checked on every keystroke.
NUMBER_RE = re.compile(
    r"""
    (?:
        0               # a lone zero, so "0" is fine but "007" is not
        |
        [1-9]\d{0,2}    # or 1 to 3 digits that don't start with 0 (max 999)
    )
    (?:
        \.              # optional decimal point
        \d{0,2}         # followed by up to 2 digits ("5." is allowed while typing)
    )?
    """,
    re.VERBOSE,
)


def validate_number(proposed):
    """Used by the 'out of' box. An empty box is allowed so it can be retyped."""
    if proposed == "":
        return True
    return NUMBER_RE.fullmatch(proposed) is not None


class ActivityPage(tk.Frame):

    COLS = 3

    def __init__(self, parent, main_window, ribbon_photo, student_number=None):
        super().__init__(parent, bg=LIGHT_MODE["window"])
        self.student_number = student_number
        self.main_window = main_window
        self.current_theme = LIGHT_MODE
        self.cards = []

        # Average (0-100) of each category, and which ones were calculated
        self.category_scores = {name: 0.0 for name in CATEGORIES}
        self.recorded = set()

        self.number_vcmd = (self.register(validate_number), "%P")

        # Bigger text in the dropdown lists
        self.option_add("*TCombobox*Listbox.font", ("Arial", 13))

        # ---------------- Left panel ----------------
        self.progressgrade_frame = tk.Frame(
            self, bg="#fff2bb", relief="solid", bd=2
        )
        self.progressgrade_frame.place(
            relx=0, rely=0, x=15, y=15,
            relwidth=0.6, relheight=1, height=-30, width=-22,
        )

        self.subject_selection = tk.Label(
            self.progressgrade_frame, text="Select Subject",
            bg="#fff2bb", font=("Arial", 20, "bold"),
        )
        self.subject_selection.place(relx=0.04, rely=0.015, anchor="nw")

        self.term_caption = self._caption("TERM", 0.04)
        self.subject_caption = self._caption("SUBJECT", 0.38)
        self.type_caption = self._caption("CATEGORY", 0.72)

        self.term_dropdown = ttk.Combobox(
            self.progressgrade_frame,
            values=list(SUBJECT_GROUPS.keys()),
            state="readonly", font=("Arial", 13),
        )
        self.term_dropdown.set("1st Year - 1st Sem")
        self.term_dropdown.place(relx=0.04, rely=0.125, relwidth=0.26, height=34)
        self.term_dropdown.bind("<<ComboboxSelected>>", self.on_term_changed)

        self.psubject_dropdown = ttk.Combobox(
            self.progressgrade_frame,
            values=SUBJECT_GROUPS["1st Year - 1st Sem"][0],
            state="readonly", font=("Arial", 13),
        )
        self.psubject_dropdown.place(relx=0.38, rely=0.125, relwidth=0.26, height=34)

        self.type_dropdown = ttk.Combobox(
            self.progressgrade_frame,
            values=list(CATEGORIES),
            state="readonly", font=("Arial", 13, "bold"),
        )
        self.type_dropdown.set("Activity")
        self.type_dropdown.place(relx=0.72, rely=0.125, relwidth=0.26, height=34)
        self.type_dropdown.bind("<<ComboboxSelected>>", self.on_type_change)

        self.pseparator = tk.Frame(self.progressgrade_frame, height=2, bg="#000000")
        self.pseparator.place(relx=0.001, rely=0.2, relwidth=1)

        self.pbelow_sep = tk.Frame(self.progressgrade_frame, bg="#f5f5dc")
        self.pbelow_sep.place(relx=0, rely=0.203, relwidth=1, relheight=0.797)

        self.enter_score_label = tk.Label(
            self.pbelow_sep, text="Enter Scores",
            bg="#f5f5dc", font=("Arial", 20, "bold"),
        )
        self.enter_score_label.place(relx=0.04, rely=0.02, anchor="nw")

        self.hint_label = tk.Label(
            self.pbelow_sep,
            text="Change \"OUT OF\" if an item isn't graded out of 100.",
            bg="#f5f5dc", fg="black", font=("Arial", 11),
        )
        self.hint_label.place(relx=0.04, rely=0.075, anchor="nw")

        self.padd_btn = tk.Button(
            self.pbelow_sep, text="+  ADD", font=("Arial", 12, "bold"),
            bg="white", fg="black", command=self.add_activity,
        )
        self.padd_btn.place(relx=0.96, rely=0.03, anchor="ne", width=110, height=40)

        # Scrollable area for the cards
        self.list_frame = tk.Frame(self.pbelow_sep, bg="#f5f5dc")
        self.list_frame.place(relx=0.04, rely=0.13, relwidth=0.92, relheight=0.80)

        self.scrollbar = tk.Scrollbar(self.list_frame, orient="vertical")
        self.scrollbar.pack(side="right", fill="y")

        self.canvas = tk.Canvas(
            self.list_frame, highlightthickness=1,
            yscrollcommand=self.scrollbar.set,
        )
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.config(command=self.canvas.yview)

        self.pbox = tk.LabelFrame(self.canvas, text=TITLES["Activity"])
        self.canvas_window = self.canvas.create_window(
            (0, 0), window=self.pbox, anchor="nw"
        )
        for col in range(self.COLS):
            self.pbox.columnconfigure(col, weight=1, uniform="cards")

        # Keep the card area as wide as the canvas
        self.canvas.bind("<Configure>", self._resize_cards_area)

        # Calculate button
        self.pseparator3 = tk.Frame(self.progressgrade_frame, height=2, bg="#000000")
        self.pseparator3.place(relx=0.05, rely=0.90, relwidth=0.9)

        self.pbelow_sep3 = tk.Frame(self.progressgrade_frame, bg="#f5f5dc")
        self.pbelow_sep3.place(relx=0, rely=0.903, relwidth=1, relheight=0.097)

        self.pcalculator_button = tk.Button(
            self.pbelow_sep3, text="🖩 CALCULATE",
            font=("Titillium Web", 16, "bold"),
            bg="#fff2bb", activebackground="#887b40",
            command=self.pclick_calculate_button,
        )
        self.pcalculator_button.place(relx=0.05, rely=0.1, relwidth=0.9, relheight=0.8)

        # ---------------- Results panel ----------------
        self.result_frame = tk.Frame(
            self, bg="#fff2bb", borderwidth=2, relief="solid"
        )

        self.result_text = tk.Label(
            self.result_frame, text="RESULTS",
            bg="#fff2bb", fg="black", font=("Titillium Web", 15, "bold"),
        )
        self.result_text.pack(fill="x", pady=20, padx=10, anchor="nw")

        self.res_separator = tk.Frame(self.result_frame, height=2, bg="#000000")
        self.res_separator.place(relx=0.001, rely=0.2, relwidth=1)

        self.below_res_sep = tk.Frame(self.result_frame, bg="#f5f5dc")
        self.below_res_sep.place(relx=0, rely=0.203, relwidth=1, relheight=0.797)

        self.cat_heading = tk.Label(
            self.below_res_sep, text="CATEGORY AVERAGE",
            font=("Titillium Web", 11, "bold"), bg="#f5f5dc", fg="black",
        )
        self.cat_heading.place(relx=0.03, rely=0.03, relwidth=0.45)

        self.overall_heading = tk.Label(
            self.below_res_sep, text="OVERALL GRADE",
            font=("Titillium Web", 11, "bold"), bg="#f5f5dc", fg="black",
        )
        self.overall_heading.place(relx=0.52, rely=0.03, relwidth=0.45)

        self.result_vertical_separator = tk.Frame(
            self.below_res_sep, width=2, bg="#000000"
        )
        self.result_vertical_separator.place(relx=0.5, rely=0.02, relheight=0.30)

        self.cat_value = tk.Label(
            self.below_res_sep, text="--",
            font=("Titillium Web", 28, "bold"), bg="#f5f5dc", fg="black",
        )
        self.cat_value.place(relx=0.03, rely=0.12, relwidth=0.45)

        self.overall_value = tk.Label(
            self.below_res_sep, text="--",
            font=("Titillium Web", 28, "bold"), bg="#f5f5dc", fg="black",
        )
        self.overall_value.place(relx=0.52, rely=0.12, relwidth=0.45)

        self.breakdown_title = tk.Label(
            self.below_res_sep, text="CATEGORY BREAKDOWN",
            font=("Titillium Web", 14, "bold"), bg="#f5f5dc", fg="black",
        )
        self.breakdown_title.place(relx=0.06, rely=0.36, anchor="nw")

        self.breakdown_frame = tk.Frame(self.below_res_sep, bg="#f5f5dc")
        self.breakdown_frame.place(relx=0.06, rely=0.42, relwidth=0.88, relheight=0.30)
        self.breakdown_frame.columnconfigure(0, weight=2, uniform="bd")
        self.breakdown_frame.columnconfigure(1, weight=1, uniform="bd")

        self.breakdown_cells = []
        self.breakdown_values = {}
        for row, name in enumerate(CATEGORIES):
            self.breakdown_frame.rowconfigure(row, weight=1, uniform="bdrows")
            name_cell = tk.Label(
                self.breakdown_frame, text=name.upper(),
                font=("Titillium Web", 12, "bold"),
                bg="#fff2bb", fg="black", relief="solid", bd=1,
            )
            name_cell.grid(row=row, column=0, sticky="nsew")
            value_cell = tk.Label(
                self.breakdown_frame, text="--",
                font=("Titillium Web", 12),
                bg="#fff2bb", fg="black", relief="solid", bd=1,
            )
            value_cell.grid(row=row, column=1, sticky="nsew")
            self.breakdown_cells += [name_cell, value_cell]
            self.breakdown_values[name] = value_cell

        self.status_result = tk.Label(
            self.below_res_sep, text="",
            font=("Titillium Web", 12, "bold"),
            bg="#f5f5dc", fg="black",
            anchor="center", justify="center", padx=10, wraplength=400,
        )
        self.status_result.place(
            relx=0.5, rely=0.85, relwidth=0.88, height=60, anchor="center"
        )

        self.bind("<Configure>", self.update_popup_position)

        # Two starting cards, then show the results panel
        self.add_activity()
        self.add_activity()
        self.place_result_panel()

    # ------------------------------------------------------------------
    # Small helpers
    # ------------------------------------------------------------------
    def _caption(self, text, relx):
        label = tk.Label(
            self.progressgrade_frame, text=text,
            bg="#fff2bb", fg="black", font=("Arial", 10, "bold"),
        )
        label.place(relx=relx, rely=0.085, anchor="nw")
        return label

    def _resize_cards_area(self, event):
        self.canvas.itemconfigure(self.canvas_window, width=event.width)

    def _update_scrollregion(self):
        self.pbox.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def update_popup_position(self, event=None):
        if event is not None and event.widget is not self:
            return
        self.place_result_panel()

    def place_result_panel(self):
        self.result_frame.place(
            relx=0.6, rely=0, x=7, y=15,
            relwidth=0.4, relheight=1, width=-22, height=-30,
        )
        self.result_frame.lift()

    # ------------------------------------------------------------------
    # Dropdown handlers
    # ------------------------------------------------------------------
    def on_term_changed(self, event=None):
        subjects, _year, _semester = SUBJECT_GROUPS[self.term_dropdown.get()]
        self.psubject_dropdown["values"] = subjects
        self.psubject_dropdown.set("")

    def on_type_change(self, event=None):
        """Clear the cards and switch to the chosen category."""
        for card in self.cards:
            card["frame"].destroy()
        self.cards.clear()

        category = self.type_dropdown.get()
        self.pbox.config(text=TITLES.get(category, f" {category}s "))

        self.add_activity()
        self.add_activity()

    # ------------------------------------------------------------------
    # Cards: add / remove
    # ------------------------------------------------------------------
    def make_score_validator(self, card):
        """Same rules as the old limiter, but the cap is the card's 'out of'."""
        def check(proposed):
            if proposed == "":
                return True
            if not NUMBER_RE.fullmatch(proposed):
                return False
            try:
                limit = float(card["max"].get())
            except ValueError:
                limit = 100.0  # 'out of' is empty while being retyped
            if limit <= 0:
                limit = 100.0
            return float(proposed) <= limit
        return check

    def add_activity(self):
        theme = self.current_theme
        frame = tk.Frame(self.pbox, highlightthickness=1)

        header = tk.Frame(frame)
        header.pack(fill="x", padx=6, pady=(6, 0))

        title = tk.Label(header, font=("Arial", 11, "bold"))
        title.pack(side="left")

        card = {"frame": frame, "header": header, "title": title}

        remove_btn = tk.Button(
            header, text="✕", font=("Arial", 9, "bold"),
            relief="flat", bd=0, cursor="hand2", width=2,
            command=lambda c=card: self.remove_activity(c),
        )
        remove_btn.pack(side="right")

        # The score is capped by this card's "out of" value (100 by default)
        score_entry = tk.Entry(
            frame, width=6, font=("Arial", 20), justify="center",
            validate="key",
            validatecommand=(self.register(self.make_score_validator(card)), "%P"),
            relief="solid",
        )
        score_entry.pack(fill="x", padx=14, pady=(6, 4), ipady=4)

        out_row = tk.Frame(frame)
        out_row.pack(pady=(0, 10))

        out_label = tk.Label(out_row, text="OUT OF", font=("Arial", 9, "bold"))
        out_label.pack(side="left", padx=(0, 6))

        max_entry = tk.Entry(
            out_row, width=5, font=("Arial", 13), justify="center",
            validate="key", validatecommand=self.number_vcmd, relief="solid",
        )
        max_entry.insert(0, "100")
        max_entry.pack(side="left")

        card.update({
            "remove": remove_btn, "score": score_entry,
            "out_row": out_row, "out_label": out_label, "max": max_entry,
        })
        self.cards.append(card)
        self.style_card(card, theme)
        self.relayout_cards()

    def remove_activity(self, card):
        # Always keep one card on screen; just clear it instead
        if len(self.cards) <= 1:
            card["score"].delete(0, tk.END)
            card["max"].delete(0, tk.END)
            card["max"].insert(0, "100")
            return

        self.cards.remove(card)
        card["frame"].destroy()
        self.relayout_cards()

    def relayout_cards(self):
        category = self.type_dropdown.get()
        for index, card in enumerate(self.cards):
            card["title"].config(text=f"{category} {index + 1}")
            card["frame"].grid(
                row=index // self.COLS, column=index % self.COLS,
                padx=14, pady=14, sticky="nsew",
            )
        self._update_scrollregion()

    def style_card(self, card, theme):
        list_bg, table_bg = theme["list"], theme["table"]
        text_fg, sidebar_bg = theme["text"], theme["sidebar"]

        card["frame"].configure(
            bg=list_bg, highlightbackground=sidebar_bg, highlightcolor=sidebar_bg
        )
        for key in ("header", "out_row"):
            card[key].configure(bg=list_bg)
        for key in ("title", "out_label"):
            card[key].configure(bg=list_bg, fg=text_fg)
        card["remove"].configure(
            bg=list_bg, fg=text_fg,
            activebackground=sidebar_bg, activeforeground=text_fg,
        )
        for key in ("score", "max"):
            card[key].configure(
                bg=table_bg, fg=text_fg, insertbackground=text_fg,
                selectbackground=sidebar_bg, selectforeground=text_fg,
            )

    # ------------------------------------------------------------------
    # Calculation
    # ------------------------------------------------------------------
    def pclick_calculate_button(self):
        category = self.type_dropdown.get()
        percents = []

        for index, card in enumerate(self.cards, start=1):
            score_text = card["score"].get().strip()
            if not score_text:
                continue  # skip empty cards

            label = f"{category} {index}"
            try:
                score = float(score_text)
            except ValueError:
                self.show_result_error(f"{label}: enter a valid score.")
                return
            try:
                maximum = float(card["max"].get().strip())
            except ValueError:
                self.show_result_error(f"{label}: enter a valid \"out of\" value.")
                return

            if maximum <= 0:
                self.show_result_error(f"{label}: \"out of\" must be more than 0.")
                return
            if score > maximum:
                self.show_result_error(
                    f"{label}: score is higher than {maximum:g}."
                )
                return

            percents.append(score / maximum * 100)

        if not percents:
            self.show_result_error("Enter at least one score first.")
            return

        average = sum(percents) / len(percents)
        self.category_scores[category] = average
        self.recorded.add(category)

        overall = calculate_overall_final_grade(self.category_scores)

        self.cat_value.config(text=f"{average:.2f}")
        self.overall_value.config(text=f"{overall:.2f}")
        for name, cell in self.breakdown_values.items():
            if name in self.recorded:
                cell.config(text=f"{self.category_scores[name]:.2f}")
            else:
                cell.config(text="--")

        self.status_result.config(text="", bg=self.current_theme["window"])
        self.place_result_panel()

    def show_result_error(self, error):
        theme = self.current_theme
        if theme["window"] == "#1e1e1e":
            error_bg, error_fg = "#5b2020", "#ffdada"
        else:
            error_bg, error_fg = "#ffcccc", "#990000"

        self.cat_value.config(text="--")
        self.status_result.config(
            text=f"ERROR: {error}", bg=error_bg, fg=error_fg
        )
        self.place_result_panel()

    # ------------------------------------------------------------------
    # Theme
    # ------------------------------------------------------------------
    def apply_theme(self, theme, ribbon_photo=None, ribbon_photo_white=None):
        self.current_theme = theme
        window_bg = theme["window"]
        table_bg = theme["table"]
        list_bg = theme["list"]
        text_fg = theme["text"]
        sidebar_bg = theme["sidebar"]

        self.configure(bg=window_bg)

        # Left panel
        self.progressgrade_frame.configure(bg=table_bg)
        for label in (
            self.subject_selection, self.term_caption,
            self.subject_caption, self.type_caption,
        ):
            label.configure(bg=table_bg, fg=text_fg)

        self.pbelow_sep.configure(bg=window_bg)
        self.pbelow_sep3.configure(bg=window_bg)
        for label in (self.enter_score_label, self.hint_label):
            label.configure(bg=window_bg, fg=text_fg)

        self.list_frame.configure(bg=window_bg)
        self.canvas.configure(
            bg=list_bg, highlightbackground=text_fg, highlightcolor=text_fg
        )
        self.pbox.configure(bg=list_bg, fg=text_fg)
        self.scrollbar.configure(
            bg=table_bg, troughcolor=list_bg, activebackground=sidebar_bg
        )
        for card in self.cards:
            self.style_card(card, theme)

        for button in (self.padd_btn, self.pcalculator_button):
            button.configure(
                bg=table_bg, fg=text_fg,
                activebackground=sidebar_bg, activeforeground=text_fg,
            )

        for separator in (
            self.pseparator, self.pseparator3,
            self.res_separator, self.result_vertical_separator,
        ):
            separator.configure(bg=text_fg)

        # Dropdowns
        style = ttk.Style(self)
        style.configure(
            "Activity.TCombobox",
            fieldbackground=list_bg, background=table_bg,
            foreground=text_fg, arrowcolor=text_fg,
        )
        style.map(
            "Activity.TCombobox",
            fieldbackground=[("readonly", list_bg), ("disabled", table_bg)],
            foreground=[("readonly", text_fg), ("disabled", text_fg)],
            selectbackground=[("readonly", list_bg)],
            selectforeground=[("readonly", text_fg)],
        )
        for dropdown in (
            self.term_dropdown, self.psubject_dropdown, self.type_dropdown
        ):
            dropdown.configure(style="Activity.TCombobox")

        # Results panel
        self.result_frame.configure(bg=table_bg)
        self.result_text.configure(bg=table_bg, fg=text_fg)
        self.below_res_sep.configure(bg=window_bg)
        for label in (
            self.cat_heading, self.overall_heading,
            self.cat_value, self.overall_value, self.breakdown_title,
        ):
            label.configure(bg=window_bg, fg=text_fg)
        self.breakdown_frame.configure(bg=window_bg)
        for cell in self.breakdown_cells:
            cell.configure(bg=table_bg, fg=text_fg)

        # Keep the error colors if an error is showing
        if self.status_result.cget("text").startswith("ERROR:"):
            if window_bg == "#1e1e1e":
                self.status_result.configure(bg="#5b2020", fg="#ffdada")
            else:
                self.status_result.configure(bg="#ffcccc", fg="#990000")
        else:
            self.status_result.configure(bg=window_bg, fg=text_fg)