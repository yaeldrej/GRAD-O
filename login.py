import subprocess
import sys
import tkinter as tk
from tkinter import PhotoImage, messagebox, ttk
from pathlib import Path
from core.config import SUBJECT_GROUPS
from core.database import (
    add_person,
    check_person,
    get_student_number_by_username,
    get_employee_number_by_username,
    get_section_counts,
    set_student_section,
    SECTION_COUNT,
    SECTION_CAPACITY,
)
from auth.resetpassword import PasswordReset


BASE_DIR = Path(__file__).resolve().parent

# ---------------- THEME ----------------
BG = "#f5f5dc"          # page background
CARD_BG = "#fffdf0"     # card background
BORDER = "#cfc79a"
NAVY = "#1b365d"
NAVY_HOVER = "#2c5282"
GOLD = "#d9a521"
CHIP_BG = "#fff2bb"
CHIP_HOVER = "#ffe58a"
TEXT = "#1f1f1f"
MUTED = "#6b6a55"
HEAD_FONT = "Titillium Web"
BODY_FONT = "Arial"

YEARS = list(dict.fromkeys(y for _, y, _ in SUBJECT_GROUPS.values()))


# ---------------- WINDOW ----------------
window = tk.Tk()
window.title("GRAD-O")
window.geometry("1080x720")
window.configure(bg=BG)
window.minsize(1000, 700)

# ----ICON----
try:
    icon = PhotoImage(file=str(BASE_DIR / "Assets" / "icon.png"))
    window.iconphoto(True, icon)
except Exception:
    pass  # run without an icon if the file is missing


def load_logo():
    """Load Assets/logo.png scaled to roughly 280px wide (None if missing)."""
    try:
        img = PhotoImage(file=str(BASE_DIR / "Assets" / "logo.png"))
        factor = max(1, round(img.width() / 280))
        return img.subsample(factor, factor) if factor > 1 else img
    except Exception:
        return None


LOGO = load_logo()

# ttk look for the year / section dropdowns
style = ttk.Style(window)
style.theme_use("clam")
style.configure(
    "Grad.TCombobox",
    fieldbackground="white",
    background="white",
    foreground=TEXT,
    bordercolor=BORDER,
    lightcolor="white",
    darkcolor="white",
    arrowcolor=NAVY,
    padding=8,
)
style.map(
    "Grad.TCombobox",
    fieldbackground=[("readonly", "white"), ("disabled", "#ececdf")],
    foreground=[("readonly", TEXT), ("disabled", "#9a9a88")],
    selectbackground=[("readonly", "white")],
    selectforeground=[("readonly", TEXT)],
    bordercolor=[("focus", NAVY)],
)
window.option_add("*TCombobox*Listbox.font", (BODY_FONT, 11))

selected_role = ""


def clear_window():
    for widget in window.winfo_children():
        widget.destroy()


# ---------------- SMALL UI HELPERS ----------------
def add_back_button(command):
    back_button = tk.Button(
        window,
        text="←  Back",
        font=(BODY_FONT, 12, "bold"),
        bg=BG,
        fg=NAVY,
        activebackground=BG,
        activeforeground=NAVY_HOVER,
        relief="flat",
        bd=0,
        cursor="hand2",
        command=command,
    )
    back_button.place(x=24, y=20)


def make_button(parent, text, command, primary=True, width=None, size=12):
    bg = NAVY if primary else CHIP_BG
    fg = "white" if primary else NAVY
    hover = NAVY_HOVER if primary else CHIP_HOVER
    button = tk.Button(
        parent,
        text=text,
        command=command,
        font=(BODY_FONT, size, "bold"),
        bg=bg,
        fg=fg,
        activebackground=hover,
        activeforeground=fg,
        relief="flat",
        bd=0,
        cursor="hand2",
        padx=18,
        pady=9,
        width=width,
    )
    button.bind("<Enter>", lambda e: button.config(bg=hover))
    button.bind("<Leave>", lambda e: button.config(bg=bg))
    return button


def make_link(parent, text, command, fg=NAVY, size=10):
    return tk.Button(
        parent,
        text=text,
        command=command,
        font=(BODY_FONT, size, "underline"),
        bg=CARD_BG,
        fg=fg,
        activebackground=CARD_BG,
        activeforeground=NAVY_HOVER,
        relief="flat",
        bd=0,
        cursor="hand2",
    )


def make_card():
    """A centered card with a gold top stripe. Returns the frame to fill."""
    card = tk.Frame(
        window, bg=CARD_BG, highlightthickness=1, highlightbackground=BORDER
    )
    card.place(relx=0.5, rely=0.5, anchor="center")
    tk.Frame(card, bg=GOLD, height=6).pack(fill="x")
    body = tk.Frame(card, bg=CARD_BG)
    body.pack(padx=50, pady=(22, 28))
    return body


def add_heading(parent, text, size=24, pady=(0, 6)):
    tk.Label(
        parent, text=text, font=(HEAD_FONT, size, "bold"), bg=CARD_BG, fg=NAVY
    ).pack(pady=pady)


def add_chip(parent, text, pady=(0, 8)):
    tk.Label(
        parent,
        text=text,
        font=(BODY_FONT, 9, "bold"),
        bg=CHIP_BG,
        fg=NAVY,
        padx=14,
        pady=4,
    ).pack(pady=pady)


def add_logo(parent):
    if LOGO:
        tk.Label(parent, image=LOGO, bg=CARD_BG).pack(pady=(0, 10))


def toggle_password(entry, button):
    if entry.cget("show") == "*":
        entry.config(show="")
        button.config(text="🙈")
    else:
        entry.config(show="*")
        button.config(text="👁️")


def build_entry(parent, show_char=None, width=24):
    """A white text box with a border that turns navy when focused.
    Returns (outer_frame, entry); the caller packs/grids the frame."""
    box = tk.Frame(
        parent, bg="white", highlightthickness=1, highlightbackground=BORDER
    )
    entry = tk.Entry(
        box,
        font=(BODY_FONT, 12),
        relief="flat",
        bd=0,
        bg="white",
        fg=TEXT,
        insertbackground=TEXT,
        width=width,
    )
    if show_char:
        entry.config(show=show_char)
        eye = tk.Button(
            box,
            text="👁️",
            font=(BODY_FONT, 9),
            bg="white",
            activebackground="white",
            relief="flat",
            bd=0,
            cursor="hand2",
        )
        eye.config(command=lambda e=entry, b=eye: toggle_password(e, b))
        eye.pack(side="right", padx=6)
    entry.pack(side="left", fill="x", expand=True, padx=(10, 4), ipady=7)

    entry.bind("<FocusIn>", lambda e: box.config(highlightbackground=NAVY))
    entry.bind("<FocusOut>", lambda e: box.config(highlightbackground=BORDER))
    return box, entry


def create_input_field(parent, label_text, show_char=None):
    """Labelled, centered input. Also used by the password-reset pages."""
    bg = parent.cget("bg")
    tk.Label(
        parent, text=label_text, font=(BODY_FONT, 10, "bold"), bg=bg, fg=MUTED
    ).pack(pady=(6, 2))
    box, entry = build_entry(parent, show_char, width=30)
    box.pack(pady=(0, 6))
    return entry


def add_labeled_entry(parent, label_text, show_char=None):
    """Left-aligned label + entry stacked inside `parent` (fills its width)."""
    tk.Label(
        parent,
        text=label_text,
        font=(BODY_FONT, 9, "bold"),
        bg=CARD_BG,
        fg=MUTED,
        anchor="w",
    ).pack(fill="x", pady=(0, 3))
    box, entry = build_entry(parent, show_char, width=24)
    box.pack(fill="x")
    return entry


def choose_role(role):
    global selected_role
    selected_role = role
    show_login()


# ---------------- START PAGE ----------------
def start_page():
    clear_window()
    body = make_card()

    add_logo(body)
    add_heading(body, "Welcome to GRAD-O", size=26, pady=(0, 4))
    tk.Label(
        body,
        text="Choose your account type to continue",
        font=(BODY_FONT, 11),
        bg=CARD_BG,
        fg=MUTED,
    ).pack(pady=(0, 18))

    make_button(
        body, "🎓   STUDENT", lambda: choose_role("student"), width=24, size=13
    ).pack(pady=6)
    make_button(
        body, "📚   TEACHER", lambda: choose_role("teacher"), width=24, size=13
    ).pack(pady=6)


# ---------------- LOGIN ----------------
def show_login():
    clear_window()
    add_back_button(start_page)
    body = make_card()

    add_logo(body)
    add_heading(body, "Welcome back")
    add_chip(body, f"{selected_role.upper()} LOGIN", pady=(0, 14))

    form = tk.Frame(body, bg=CARD_BG)
    form.pack(fill="x")

    username_entry = add_labeled_entry(form, "USERNAME")
    tk.Frame(form, bg=CARD_BG, height=10).pack()
    password_entry = add_labeled_entry(form, "PASSWORD", show_char="*")

    def do_login(event=None):
        login(username_entry, password_entry)

    username_entry.bind("<Return>", lambda e: password_entry.focus_set())
    password_entry.bind("<Return>", do_login)

    make_button(body, "LOGIN", do_login).pack(fill="x", pady=(20, 8))

    make_link(
        body, "Forgot password?", reset_flow.show_forgot_password, fg="#b00020"
    ).pack(pady=2)

    tk.Frame(body, bg=BORDER, height=1).pack(fill="x", pady=(14, 10))

    row = tk.Frame(body, bg=CARD_BG)
    row.pack()
    tk.Label(
        row,
        text="Don't have an account?",
        font=(BODY_FONT, 10),
        bg=CARD_BG,
        fg=MUTED,
    ).pack(side="left")
    make_link(row, "Create one", show_register).pack(side="left", padx=4)

    username_entry.focus_set()


def login(username_entry, password_entry):
    username = username_entry.get().strip().lower()
    password = password_entry.get().strip()

    if not username or not password:
        messagebox.showwarning(
            "Missing Input", "Please enter both username and password."
        )
        return

    try:
        # Pass role to check credentials in the correct table (person vs teacher)
        is_authenticated = check_person(
            username=username, password=password, role=selected_role
        )
    except Exception as e:
        messagebox.showerror(
            "Database Error", f"Unable to verify credentials: {e}"
        )
        return

    if is_authenticated:
        messagebox.showinfo("Login Successful", "Welcome to GRAD-O!")
        if selected_role == "student":
            try:
                student_number = get_student_number_by_username(username)
            except Exception as e:
                messagebox.showerror(
                    "Database Error", f"Could not load your account: {e}"
                )
                return

            if not student_number:
                messagebox.showerror(
                    "Account Error",
                    "No student number is linked to this account.",
                )
                return

            open_main(student_number)
        elif selected_role == "teacher":
            try:
                employee_number = get_employee_number_by_username(username)
            except Exception as e:
                messagebox.showerror(
                    "Database Error", f"Could not load your account: {e}"
                )
                return

            if not employee_number:
                messagebox.showerror(
                    "Account Error",
                    "No employee number is linked to this account.",
                )
                return

            open_admin(employee_number)
    else:
        messagebox.showerror(
            "Login Failed", f"Invalid credentials for {selected_role} role."
        )


# ---------------- REGISTER ----------------
def section_label(number, used):
    status = "FULL" if used >= SECTION_CAPACITY else f"{used}/{SECTION_CAPACITY}"
    return f"Section {number}   ({status})"


def show_register():
    clear_window()
    add_back_button(show_login)
    body = make_card()

    is_student = selected_role == "student"

    add_heading(body, "Create your account")
    add_chip(body, f"{selected_role.upper()} ACCOUNT", pady=(0, 12))

    form = tk.Frame(body, bg=CARD_BG)
    form.pack()
    form.columnconfigure(0, weight=1, uniform="col")
    form.columnconfigure(1, weight=1, uniform="col")

    entries = {}

    def add_cell(key, label_text, row, col, show_char=None):
        cell = tk.Frame(form, bg=CARD_BG)
        cell.grid(row=row, column=col, sticky="ew", padx=8, pady=6)
        entries[key] = add_labeled_entry(cell, label_text, show_char)

    number_label = "STUDENT NUMBER" if is_student else "EMPLOYEE NUMBER"
    add_cell("std_num", number_label, 0, 0)
    add_cell("email", "PHINMAED EMAIL", 0, 1)
    add_cell("f_name", "FIRST NAME", 1, 0)
    add_cell("m_name", "MIDDLE NAME (OPTIONAL)", 1, 1)
    add_cell("l_name", "LAST NAME", 2, 0)
    add_cell("username", "USERNAME", 2, 1)
    add_cell("password", "PASSWORD", 3, 0, show_char="*")
    add_cell("confirm", "CONFIRM PASSWORD", 3, 1, show_char="*")

    year_combo = None
    section_combo = None

    if is_student:
        year_cell = tk.Frame(form, bg=CARD_BG)
        year_cell.grid(row=4, column=0, sticky="ew", padx=8, pady=6)
        tk.Label(
            year_cell,
            text="YEAR LEVEL",
            font=(BODY_FONT, 9, "bold"),
            bg=CARD_BG,
            fg=MUTED,
            anchor="w",
        ).pack(fill="x", pady=(0, 3))
        year_combo = ttk.Combobox(
            year_cell,
            values=YEARS,
            state="readonly",
            font=(BODY_FONT, 11),
            style="Grad.TCombobox",
        )
        year_combo.pack(fill="x")

        section_cell = tk.Frame(form, bg=CARD_BG)
        section_cell.grid(row=4, column=1, sticky="ew", padx=8, pady=6)
        tk.Label(
            section_cell,
            text=f"SECTION  (MAX {SECTION_CAPACITY} STUDENTS)",
            font=(BODY_FONT, 9, "bold"),
            bg=CARD_BG,
            fg=MUTED,
            anchor="w",
        ).pack(fill="x", pady=(0, 3))
        section_combo = ttk.Combobox(
            section_cell,
            values=[],
            state="disabled",
            font=(BODY_FONT, 11),
            style="Grad.TCombobox",
            postcommand=lambda: refresh_sections(),
        )
        section_combo.pack(fill="x")

        def refresh_sections():
            """Reload 'Section N (used/30)' for the chosen year."""
            year = year_combo.get()
            if not year:
                return
            try:
                counts = get_section_counts(year)
            except Exception:
                counts = {}
            section_combo["values"] = [
                section_label(n, counts.get(n, 0))
                for n in range(1, SECTION_COUNT + 1)
            ]

        def on_year_selected(event=None):
            section_combo.set("")
            section_combo.config(state="readonly")
            refresh_sections()

        def on_section_selected(event=None):
            if "FULL" in section_combo.get():
                messagebox.showwarning(
                    "Section Full",
                    f"That section already has {SECTION_CAPACITY} students. "
                    "Please choose another section.",
                )
                section_combo.set("")
                refresh_sections()

        year_combo.bind("<<ComboboxSelected>>", on_year_selected)
        section_combo.bind("<<ComboboxSelected>>", on_section_selected)

    make_button(
        body,
        "CREATE ACCOUNT",
        lambda: register(entries, year_combo, section_combo),
    ).pack(fill="x", pady=(18, 8), padx=8)

    row = tk.Frame(body, bg=CARD_BG)
    row.pack()
    tk.Label(
        row,
        text="Already have an account?",
        font=(BODY_FONT, 10),
        bg=CARD_BG,
        fg=MUTED,
    ).pack(side="left")
    make_link(row, "Log in", show_login).pack(side="left", padx=4)

    entries["std_num"].focus_set()


def register(entries, year_combo=None, section_combo=None):
    data = {k: v.get().strip() for k, v in entries.items()}

    required_fields = [
        "std_num", "f_name", "l_name", "email", "username", "password"
    ]
    if any(not data[f] for f in required_fields):
        messagebox.showwarning(
            "Missing Information", "Please fill in all required fields."
        )
        return

    if data["password"] != data["confirm"]:
        messagebox.showerror("Registration Failed", "Passwords do not match.")
        return

    if not data["email"].lower().endswith("@phinmaed.com"):
        messagebox.showwarning(
            "Invalid Email", "Please use a valid @phinmaed.com email address."
        )
        return

    # Students must pick a year level and a section that still has room
    year_level = None
    section_number = None
    if selected_role == "student":
        year_level = year_combo.get()
        section_text = section_combo.get()
        if not year_level or not section_text:
            messagebox.showwarning(
                "Missing Information",
                "Please select your year level and section.",
            )
            return

        section_number = int(section_text.split()[1])
        try:
            counts = get_section_counts(year_level)
        except Exception as e:
            messagebox.showerror(
                "Database Error", f"Could not check the section: {e}"
            )
            return

        if counts.get(section_number, 0) >= SECTION_CAPACITY:
            messagebox.showwarning(
                "Section Full",
                f"Section {section_number} already has {SECTION_CAPACITY} "
                "students. Please choose another section.",
            )
            section_combo.set("")
            return

    try:
        registration_success = add_person(
            student_number=data["std_num"],
            first_name=data["f_name"],
            middle_name=data["m_name"],
            last_name=data["l_name"],
            phinmaed_email=data["email"].lower(),
            username=data["username"].lower(),
            password=data["password"],
            role=selected_role,
        )
    except Exception as e:
        messagebox.showerror(
            "Database Error", f"Failed to connect or register: {e}"
        )
        return

    if not registration_success:
        messagebox.showerror(
            "Registration Failed",
            "That student/employee number, username or email "
            "already exists in the database.",
        )
        return

    # Save the section (the database re-checks the 30-student limit)
    if selected_role == "student":
        try:
            set_student_section(data["std_num"], year_level, section_number)
        except ValueError:
            messagebox.showwarning(
                "Account Created",
                "Your account was created, but that section just filled up. "
                "Please ask your teacher to assign your section.",
            )
            show_login()
            return
        except Exception as e:
            messagebox.showwarning(
                "Account Created",
                f"Your account was created, but your section could not be "
                f"saved ({e}). Please ask your teacher to assign it.",
            )
            show_login()
            return

    messagebox.showinfo(
        "Account Created", "Your account has been successfully created!"
    )
    show_login()


# ---------------- LAUNCHERS ----------------
def open_main(student_number):
    main_script = BASE_DIR / "main.py"
    try:
        subprocess.Popen(
            [sys.executable, str(main_script), str(student_number)],
            cwd=str(BASE_DIR),
        )
        window.destroy()
    except Exception as e:
        messagebox.showerror(
            "Launch Error", f"Could not open student portal: {e}"
        )


def open_admin(employee_number):
    admin_script = BASE_DIR / "admin.py"
    try:
        subprocess.Popen(
            [sys.executable, str(admin_script), str(employee_number)],
            cwd=str(BASE_DIR),
        )
        window.destroy()
    except Exception as e:
        messagebox.showerror(
            "Launch Error", f"Could not open teacher portal: {e}"
        )


reset_flow = PasswordReset(
    window=window,
    get_role=lambda: selected_role,
    show_login=show_login,
    clear_window=clear_window,
    add_back_button=add_back_button,
    create_input_field=create_input_field,
)

start_page()
window.mainloop()