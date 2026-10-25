# page_home_admin.py
import tkinter as tk
from core.config import LIGHT_MODE

# (button label, page key used by AdminPage.admin_show_page, description)
PAGE_GUIDE = (
    (
        "HOME PAGE", "home",
        "Gives an overview of GRAD-O and explains what each page is for.",
    ),
    (
        "GRADE CALCULATOR", "calculator",
        "Computes a grade for a subject from Written Works (30%), "
        "Performance Tasks (40%), and Quarterly Assessment (30%) scores.",
    ),
    (
        "ACTIVITY CALCULATOR", "activity",
        "Computes the percentage of a single activity from the score "
        "and the total items, so each task can be checked on its own.",
    ),
    (
        "PERIOD CALCULATOR", "period",
        "Computes the grade for a whole grading period so you can see "
        "where a student currently stands.",
    ),
    (
        "GRADE HISTORY", "history",
        "Lists previously saved grades so you can search, review and "
        "compare them across terms.",
    ),
)


class HomePage(tk.Frame):

    def __init__(self, parent, ribbon_photo=None, on_navigate=None):
        super().__init__(parent, bg=LIGHT_MODE["window"])
        self.on_navigate = on_navigate
        self.current_theme = LIGHT_MODE

        self.container = tk.Frame(
            self, bg=LIGHT_MODE["window"], relief="solid", bd=5
        )
        self.container.place(
            relx=0.5, rely=0.5, anchor="center", relwidth=0.9, relheight=0.95
        )

        self.title = tk.Label(
            self.container,
            text="HOW TO USE GRAD-O",
            font=("Titillium Web", 20, "bold"),
            bg=LIGHT_MODE["window"],
            fg=LIGHT_MODE["text"],
            pady=20,
        )
        self.title.pack()

        # The table itself
        self.table_frame = tk.Frame(self.container, bg=LIGHT_MODE["window"])
        self.table_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))
        self.table_frame.columnconfigure(0, weight=1, uniform="cols")
        self.table_frame.columnconfigure(1, weight=3, uniform="cols")

        self.table_frame.rowconfigure(0, weight=0)
        for row in range(1, len(PAGE_GUIDE) + 1):
            self.table_frame.rowconfigure(row, weight=1, uniform="rows")

        self.header_cells = []
        self.name_cells = []
        self.desc_cells = []

        for column, text in enumerate(("PAGE", "WHAT IT DOES")):
            cell = tk.Label(
                self.table_frame,
                text=text,
                font=("Titillium Web", 13, "bold"),
                bg=LIGHT_MODE["sidebar"],
                fg=LIGHT_MODE["text"],
                relief="solid",
                bd=1,
                pady=10,
            )
            cell.grid(row=0, column=column, sticky="nsew")
            self.header_cells.append(cell)

        for row, (name, page_key, description) in enumerate(PAGE_GUIDE, start=1):
            name_cell = tk.Label(
                self.table_frame,
                text=name,
                font=("Titillium Web", 12, "bold underline"),
                bg=LIGHT_MODE["table"],
                fg=LIGHT_MODE["text"],
                relief="solid",
                bd=1,
                padx=12,
                pady=0,
                cursor="hand2",
            )
            name_cell.grid(row=row, column=0, sticky="nsew")
            name_cell.bind("<Button-1>", lambda e, key=page_key: self.go_to(key))
            name_cell.bind("<Enter>", lambda e, c=name_cell: c.configure(bg=self.current_theme["sidebar"]))
            name_cell.bind("<Leave>", lambda e, c=name_cell: c.configure(bg=self.current_theme["table"]))
            self.name_cells.append(name_cell)

            desc_cell = tk.Label(
                self.table_frame,
                text=description,
                font=("Titillium Web", 14),
                bg=LIGHT_MODE["table"],
                fg=LIGHT_MODE["text"],
                relief="solid",
                bd=1,
                padx=12,
                pady=0,
                anchor="w",
                justify=tk.LEFT,
            )
            desc_cell.grid(row=row, column=1, sticky="nsew")
            self.desc_cells.append(desc_cell)

        # Re-wrap the descriptions whenever the table is resized
        self.table_frame.bind("<Configure>", self.update_wraplength)

    def update_wraplength(self, event):
        # Column 1 gets 3/4 of the width; subtract padding and borders
        wrap = int(event.width * 0.75) - 40
        for cell in self.desc_cells:
            cell.configure(wraplength=max(wrap, 100))

    def go_to(self, page_key):
        if self.on_navigate:
            self.on_navigate(page_key)

    def apply_theme(self, theme, ribbon_photo=None, ribbon_photo_white=None):
        self.current_theme = theme  # keeps the hover colors in sync

        self.configure(bg=theme["window"])
        self.container.configure(bg=theme["window"])
        self.table_frame.configure(bg=theme["window"])
        self.title.configure(bg=theme["window"], fg=theme["text"])

        for cell in self.header_cells:
            cell.configure(bg=theme["sidebar"], fg=theme["text"])

        for cell in self.name_cells + self.desc_cells:
            cell.configure(bg=theme["table"], fg=theme["text"])