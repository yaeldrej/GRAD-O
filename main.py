# main.py
from fractions import Fraction
from pathlib import Path
import sys
import tkinter as tk
import subprocess
from tkinter import ttk
from tkinter import messagebox 
from core.config import DARK_MODE, LIGHT_MODE
from pages.student.page_activity import ActivityPage
from pages.student.page_average import AveragePage
from pages.student.page_calculator import CalculatorPage
from pages.student.page_history import HistoryPage
from pages.student.page_home import HomePage
from core.database import get_student_profile, update_student_profile
 
def match_width(photo, target_width):
    """
    Return `photo` scaled so its width is as close as possible to
    `target_width`. Uses zoom + subsample, so it works with any source size
    (not only whole-number ratios) and needs no extra libraries.
    """
    ratio = Fraction(target_width, photo.width()).limit_denominator(8)
    if ratio.numerator > 1:
        photo = photo.zoom(ratio.numerator)
    if ratio.denominator > 1:
        photo = photo.subsample(ratio.denominator)
    return photo
 
class GradOApp:
 
    def __init__(self, window, student_number=None):
        self.window = window
        self.student_number = student_number
        self.settings_popup = None
        self.profile_data = self.load_profile_data()
        self.window.geometry("1400x1000")
        self.window.minsize(1400, 1000)
        self.window.title("GRAD-O")
        self.window.configure(bg=LIGHT_MODE["window"])
 
        self.current_theme = LIGHT_MODE
 
        # Load Icons and Images
        self.icon = tk.PhotoImage(file="Assets\\icon.png")
        self.window.iconphoto(True, self.icon)
 
        # Raw Full-Size Logos
        self.ribbon_photo = tk.PhotoImage(file="Assets\\logo.png")
        self.ribbon_photo_white = tk.PhotoImage(file="Assets\\white_logo.png")
 
        # Scaled Logos for Header Ribbon
        self.ribbon_photo1 = self.ribbon_photo.subsample(2, 2)
        self.ribbon_photo_white1 = match_width(
            self.ribbon_photo_white, self.ribbon_photo1.width()
        )
        
        # Scaled Logos for Page Background Center
        self.bg_photo = self.ribbon_photo.subsample(1, 1)
        self.bg_photo_white = match_width(
            self.ribbon_photo_white, self.bg_photo.width()
        )
 
        # Header Ribbon
        self.text_label = tk.Label(
            window,
            text="Fair Calculation, Goal-Oriented Do it With GRAD-O",
            font=("Arial", 15, "bold"),
            padx=20,
            fg=LIGHT_MODE["text"],
            bg=LIGHT_MODE["ribbon"],
            relief=tk.SOLID,
            bd=1,
            anchor="w",
            image=self.ribbon_photo1,
            compound="left",
        )
        self.text_label.pack(side=tk.TOP, fill=tk.X)
 
        self.setup_sidebar()
 
        # Content Frame
        self.content_frame = tk.Frame(window, bg=LIGHT_MODE["window"])
        self.content_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
 
        # Instantiate Pages with scaled background photos
        self.pages = {
            "home": HomePage(self.content_frame, self.bg_photo, on_navigate=self.show_page),
            "calculator": CalculatorPage(self.content_frame, self.bg_photo, student_number=self.student_number),
            "activity": ActivityPage(
                self.content_frame, self.window, self.bg_photo, self.student_number
            ),
            "average": AveragePage(self.content_frame, self.student_number),
            "history": HistoryPage(self.content_frame, self.bg_photo, student_number=self.student_number),
        }
 
        self.pages["profile"] = self.create_profile_page()
 
        for page in self.pages.values():
            page.place(x=0, y=0, relwidth=1, relheight=1)
 
        self.setup_styles()
        self.show_page("home")
 
    def setup_sidebar(self):
        self.sidebar = tk.Frame(
            self.window,
            height=300,
            width=200,
            bg=LIGHT_MODE["sidebar"],
            relief=tk.SOLID,
            bd=1,
        )
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
 
        self.button1 = tk.Button(
            self.sidebar,
            text="HOME\nPAGE",
            font=("Titillium Web", 15, "bold"),
            bg=LIGHT_MODE["button"],
            fg=LIGHT_MODE["text"],
            relief="ridge",
            bd=5,
            command=lambda: self.show_page("home"),
        )
        self.button1.pack(side=tk.TOP, fill="x", padx=5, pady=10)
 
        self.button2 = tk.Button(
            self.sidebar,
            text="GRADE\nCALCULATOR",
            font=("Titillium Web", 15, "bold"),
            bg=LIGHT_MODE["button"],
            fg=LIGHT_MODE["text"],
            relief="ridge",
            bd=5,
            command=lambda: self.show_page("calculator"),
        )
        self.button2.pack(side="top", fill="x", padx=5, pady=10)
 
        self.button3 = tk.Button(
            self.sidebar,
            text="ACTIVITY\nCALCULATOR",
            font=("Titillium Web", 15, "bold"),
            bg=LIGHT_MODE["button"],
            fg=LIGHT_MODE["text"],
            relief="ridge",
            bd=5,
            command=lambda: self.show_page("activity"),
        )
        self.button3.pack(side="top", fill="x", padx=5, pady=10)
 
        self.button4 = tk.Button(
            self.sidebar,
            text="GRADE\nAVERAGE",
            font=("Titillium Web", 15, "bold"),
            bg=LIGHT_MODE["button"],
            fg=LIGHT_MODE["text"],
            relief="ridge",
            bd=5,
            command=lambda: self.show_page("average"),
        )
        self.button4.pack(side="top", fill="x", padx=5, pady=10)
 
        self.button5 = tk.Button(
            self.sidebar,
            text="GRADE\nHISTORY",
            font=("Titillium Web", 15, "bold"),
            bg=LIGHT_MODE["button"],
            fg=LIGHT_MODE["text"],
            relief="ridge",
            bd=5,
            command=lambda: self.show_page("history"),
        )
        self.button5.pack(side="top", fill="x", padx=5, pady=10)
 
        self.bottom_frame = tk.Frame(self.sidebar, bg=LIGHT_MODE["sidebar"])
        self.bottom_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=10)
 
        self.button6 = tk.Button(
            self.bottom_frame,
            text="⚙️",
            font=("Arial", 10),
            bg=LIGHT_MODE["button"],
            fg=LIGHT_MODE["text"],
            relief="ridge",
            bd=5,
             command=self.toggle_settings_popup,
        )
        self.button6.pack(side=tk.LEFT)
 
        self.button7 = tk.Button(
            self.bottom_frame,
            text="🌙",
            font=("Arial", 10),
            bg=LIGHT_MODE["sidebar"],
            fg=LIGHT_MODE["text"],
            relief="flat",
            bd=5,
            command=lambda: self.change_theme(DARK_MODE),
        )
        self.button7.pack(side=tk.RIGHT, padx=3)
 
        self.button8 = tk.Button(
            self.bottom_frame,
            text="🔆",
            font=("Arial", 10),
            bg=LIGHT_MODE["sidebar"],
            fg=LIGHT_MODE["text"],
            relief="flat",
            bd=5,
            command=lambda: self.change_theme(LIGHT_MODE),
        )
        self.button8.pack(side=tk.RIGHT, padx=3)
 
    def setup_styles(self):
        self.style = ttk.Style()
        self.style.theme_use("clam")
        self.apply_ttk_theme(LIGHT_MODE)
 
    def apply_ttk_theme(self, theme):
        self.style.configure(
            "TCombobox",
            fieldbackground=theme["list"],
            background=theme["table"],
            foreground=theme["text"],
        )
        self.style.map(
            "TCombobox",
            fieldbackground=[("readonly", theme["list"])],
            foreground=[("readonly", theme["text"])],
            selectbackground=[("readonly", theme["sidebar"])],
            selectforeground=[("readonly", theme["text"])],
        )
 
        self.style.configure(
            "Treeview",
            background=theme["list"],
            foreground=theme["text"],
            fieldbackground=theme["list"],
        )
        self.style.configure(
            "Treeview.Heading",
            background=theme["table"],
            foreground=theme["text"],
        )
        self.style.map(
            "Treeview",
            background=[("selected", theme["sidebar"])],
            foreground=[("selected", theme["text"])],
        )
 
   
    def change_theme(self, theme):
        self.current_theme = theme
        is_dark = theme == DARK_MODE
 
        # Main window and layout
        self.window.configure(bg=theme["window"])
        self.content_frame.configure(bg=theme["window"])
        self.sidebar.configure(bg=theme["sidebar"])
        self.bottom_frame.configure(bg=theme["sidebar"])
 
        # Header logo
        self.text_label.configure(
            bg=theme["ribbon"],
            fg=theme["text"],
            image=self.ribbon_photo_white1 if is_dark else self.ribbon_photo1,
        )
 
        # Sidebar buttons
        for button in (
            self.button1, self.button2, self.button3,
            self.button4, self.button5, self.button6,
        ):
            button.configure(
                bg=theme["button"],
                fg=theme["text"],
                activebackground=theme["sidebar"],
                activeforeground=theme["text"],
            )
 
        for button in (self.button7, self.button8):
            button.configure(
                bg=theme["sidebar"],
                fg=theme["text"],
                activebackground=theme["sidebar"],
                activeforeground=theme["text"],
            )
 
        # Dropdowns and tables
        self.apply_ttk_theme(theme)
 
        # Apply theme to every page
        for page in self.pages.values():
            if hasattr(page, "apply_theme"):
                page.apply_theme(
                    theme,
                    self.bg_photo,
                    self.bg_photo_white,
                )
 
        # Profile page
        self.apply_profile_theme(theme)
 
        # Settings popup (only if it exists)
        if (
            self.settings_popup is not None
            and self.settings_popup.winfo_exists()
        ):
            self.settings_popup.configure(bg=theme["table"])
 
            for button in (
                self.settings_logout_button,
                self.settings_profile_button,
            ):
                button.configure(
                    bg=theme["window"],
                    fg=theme["text"],
                    activebackground=theme["sidebar"],
                    activeforeground=theme["text"],
                )
 
    # SETTINGS POPUP WITH LOG OUT AND EDIT PROFILE
    def toggle_settings_popup(self):
        if self.settings_popup is not None and self.settings_popup.winfo_exists():
            self.settings_popup.destroy()
            self.settings_popup = None
            return
 
        self.settings_popup = tk.Frame(
            self.window, bg=self.current_theme["table"], relief="solid", bd=2,
        )
 
        # Opens just above the bottom-left Settings icon and overlays the page
        self.settings_popup.place( 
            x=0.5, rely=1.0, y=-120, width=220, height=55,
        )
        self.settings_popup.lift()
 
        self.settings_logout_button = tk.Button(
            self.settings_popup, text="LOG OUT", font=("Arial", 9, "bold"), bg=self.current_theme["window"],
            fg=self.current_theme["text"], relief="ridge", bd=2, cursor="hand2",
            command=self.confirm_logout,
        )
        self.settings_logout_button.place(
            relx=0.04, rely=0.15, relwidth=0.45, relheight=0.60,
        )
 
        self.settings_profile_button = tk.Button(
            self.settings_popup, text="EDIT PROFILE", font=("Arial", 7, "bold"), bg=self.current_theme["window"], fg=self.current_theme["text"],
            relief="ridge", bd=2, cursor="hand2", command=self.open_profile,
        )
        self.settings_profile_button.place(
            relx=0.52, rely=0.15, relwidth=0.45, relheight=0.60
        )
    
    def close_settings_popup(self):
        if self.settings_popup is not None and self.settings_popup.winfo_exists():
            self.settings_popup.destroy()
        self.settings_popup = None
 
    #DITO LOGOUT CONFIRMATION
 
    def confirm_logout(self):
        self.close_settings_popup()
 
        dialog = tk.Toplevel(self.window)
        dialog.title("Log Out")
        dialog.configure(bg=self.current_theme["window"])
        dialog.resizable(False, False)
        dialog.transient(self.window)
 
        dialog_width = 380
        dialog_height = 180
        self.window.update_idletasks()
        x = self.window.winfo_rootx() + (self.window.winfo_width() - dialog_width) // 2
        y = self.window.winfo_rooty() + (self.window.winfo_height() - dialog_height) // 2
        dialog.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")
 
        question = tk.Label(
            dialog, text="Do you want to log out?", font=("Arial", 15, "bold"),
            bg=self.current_theme["window"],
            fg=self.current_theme["text"],
        )
        question.pack(pady=(35, 25))
 
        button_frame = tk.Frame(dialog, bg=self.current_theme["window"])
        button_frame.pack()
 
        yes_button = tk.Button(
            button_frame, text="YES", font=("Arial", 11, "bold"), width=10,
            bg="#ffb8b8", fg="black",
            command=lambda: self.logout_to_login(dialog),
        )
        yes_button.pack(side=tk.LEFT, padx=10)
 
        no_button = tk.Button(
                    button_frame, text="NO", font=("Arial", 11, "bold"), width=10,
                    bg="#ffb8b8", fg="black",
                    command=lambda: dialog.destroy()
                )
        no_button.pack(side=tk.LEFT, padx=10)
 
        dialog.grab_set()
        dialog.focus_set()
    
    def logout_to_login(self, dialog):
        login_script = Path(__file__).resolve().parent / "login.py"
        try:
            subprocess.Popen(
                [sys.executable, str(login_script)],
                cwd=str(login_script.parent),
            )
            dialog.destroy()
            self.window.destroy()
        except Exception as error:
            messagebox.showerror(
                "Log Out Error",
                f"Could not open the login page:\n{error}",
                parent=dialog,
            )
 
    #ITO NA YUNG PROFILE PAGE NA PWEDE MAG EDIT
    def open_profile(self):
        self.close_settings_popup()
        self.show_page("profile")
 
    def create_profile_page(self):
        page = tk.Frame(self.content_frame, bg=LIGHT_MODE["window"])
        self.profile_page = page
 
        self.profile_card = tk.Frame(
            page, bg=LIGHT_MODE["table"], relief="solid", bd=2,
        )
        self.profile_card.place(
            relx =0.5, rely=0.5, anchor="center", width = 620, height=610,
        )
 
        self.profile_title = tk.Label(
            self.profile_card, text="EDIT PROFILE", font=("Arial", 24, "bold"),
            bg=LIGHT_MODE["table"],
            fg=LIGHT_MODE["text"]
        )
        self.profile_title.pack(pady=(25, 5))
 
        self.profile_description = tk.Label(
            self.profile_card, text="View or update your profile information", font=("Arial", 11),
            bg=LIGHT_MODE["table"],
            fg=LIGHT_MODE["text"],
        )
        self.profile_description.pack(pady=(0, 18))
 
        # form_frame is now an attribute so apply_profile_theme can recolor it
        self.profile_form_frame = tk.Frame(self.profile_card, bg=LIGHT_MODE["table"])
        self.profile_form_frame.pack(fill= tk.X, padx=65)
        form_frame = self.profile_form_frame
 
        self.profile_field_labels = []
        self.profile_entries = {}
        self.profile_entry_frames = []
 
        profile_fields = (
            ("first_name", "FIRST NAME"),
            ("middle_name", "MIDDLE NAME"),
            ("last_name", "LAST NAME"),
            ("phinmaed_email", "PHINMAED EMAIL"),
            ("student_number", "STUDENT NUMBER"),
        )
 
        for key, label_text in profile_fields:
            field_label = tk.Label(
                form_frame, text=label_text, font=("Arial", 11, "bold"),
                bg=LIGHT_MODE["table"],
                fg=LIGHT_MODE["text"], anchor="w", 
            )
            field_label.pack(fill=tk.X, pady=(5, 2))
            self.profile_field_labels.append(field_label)
 
            # entry_frame now holds the entry and acts as its border
            entry_frame = tk.Frame(
                form_frame,
                bg=self.current_theme["list"],
                highlightthickness=1,
                highlightbackground=self.current_theme["sidebar"],
                highlightcolor=self.current_theme["sidebar"],
            )
            entry_frame.pack(fill=tk.X, pady=(0, 10))
 
            field_entry = tk.Entry(
                entry_frame,  # was form_frame
                font=("Arial", 12), justify="center",
                bg=self.current_theme["list"], fg=self.current_theme["text"],
                disabledbackground=self.current_theme["list"],
                disabledforeground=self.current_theme["text"],
                insertbackground=self.current_theme["text"],
                relief="flat", bd=0, highlightthickness=0,
            )
            field_entry.pack(fill=tk.X, ipady=7)
            field_entry.insert(0, self.profile_data.get(key, ""))
            field_entry.configure(state="disabled")
            self.profile_entries[key] = field_entry
            self.profile_entry_frames.append(entry_frame)
 
        self.profile_note = tk.Label(
            self.profile_card,
            text="", font=("Arial", 9), bg=LIGHT_MODE["table"], fg=LIGHT_MODE["text"],
            wraplength=490,
        )
        self.profile_note.pack(pady=(6, 8))
 
        self.profile_button_frame = tk.Frame(
            self.profile_card,
            bg=LIGHT_MODE["table"],
        )
        self.profile_button_frame.pack(pady=10)
 
        self.profile_back_button = tk.Button(
            self.profile_button_frame, text="BACK TO HOME", font=("Arial", 10, "bold"), bg=LIGHT_MODE["window"], fg=LIGHT_MODE["text"],
            relief="ridge", bd=2, cursor="hand2",
            command=lambda: self.show_page("home"),
        )
        self.profile_back_button.pack(side=tk.LEFT, padx=6)
 
        self.profile_edit_button = tk.Button(
            self.profile_button_frame, text="EDIT PROFILE", font=("Arial", 10, "bold"),
            bg=LIGHT_MODE["window"], fg=LIGHT_MODE["text"], relief="ridge", bd=2, cursor="hand2",
            command=self.enable_profile_edit,
        )   
        self.profile_edit_button.pack(side=tk.LEFT, padx=6)
 
        self.profile_save_button = tk.Button(
            self.profile_button_frame, text="SAVE CHANGES", font=("Arial", 10, "bold"),
            bg="#cde8c5", fg="black", relief="ridge", bd=2, cursor="hand2",
            command=self.save_profile_changes,
        )
 
        self.profile_cancel_button = tk.Button(
            self.profile_button_frame,
            text="CANCEL", font=("Titillium Web", 10, "bold"), bg=LIGHT_MODE["window"], fg=LIGHT_MODE["text"],
            relief="ridge", bd=2, cursor="hand2", command=self.cancel_profile_edit,
        )
 
        return page
 
    def enable_profile_edit(self):
        for key, entry in self.profile_entries.items():
            if key == "student_number":
                continue  # the student number links to the grades, never editable
            entry.configure(state="normal")
 
        self.profile_back_button.pack_forget()
        self.profile_edit_button.pack_forget()
        self.profile_save_button.pack(side=tk.LEFT, padx=6)
        self.profile_cancel_button.pack(side=tk.LEFT, padx=6)
 
    def cancel_profile_edit(self):
        for key, entry in self.profile_entries.items():
            entry.configure(state="normal")
            entry.delete(0, tk.END)
            entry.insert(0, self.profile_data.get(key, ""))
            entry.configure(state="disabled")
 
        self.profile_save_button.pack_forget()
        self.profile_cancel_button.pack_forget()
        self.profile_back_button.pack(side=tk.LEFT, padx=6)
        self.profile_edit_button.pack(side=tk.LEFT, padx=6)
    
    def save_profile_changes(self):
        updated_profile = {
            key: entry.get().strip()
            for key, entry in self.profile_entries.items()
        }
 
        required = ("first_name", "last_name", "phinmaed_email")
        if any(not updated_profile[key] for key in required):
            messagebox.showwarning(
                "Missing Information",
                "Please fill in your first name, last name, and PHINMAED email.",
                parent=self.window,
            )
            return
 
        email = updated_profile["phinmaed_email"].lower()
        if not email.endswith("@phinmaed.com"):
            messagebox.showwarning(
                "Invalid Email",
                "Please use a valid @phinmaed.com email address.",
                parent=self.window,
            )
            return
        updated_profile["phinmaed_email"] = email
 
        try:
            update_student_profile(
                self.student_number,
                updated_profile["first_name"],
                updated_profile["middle_name"],
                updated_profile["last_name"],
                updated_profile["phinmaed_email"],
            )
        except Exception as error:
            messagebox.showerror(
                "Could Not Save", str(error), parent=self.window
            )
            return
 
        updated_profile["student_number"] = self.profile_data["student_number"]
        self.profile_data = updated_profile
 
        # show the cleaned values and lock the fields again
        for key, entry in self.profile_entries.items():
            entry.configure(state="normal")
            entry.delete(0, tk.END)
            entry.insert(0, self.profile_data.get(key, ""))
            entry.configure(state="disabled")
 
        self.profile_save_button.pack_forget()
        self.profile_cancel_button.pack_forget()
        self.profile_back_button.pack(side=tk.LEFT, padx=6)
        self.profile_edit_button.pack(side=tk.LEFT, padx=6)
 
        messagebox.showinfo(
            "Profile Updated",
            "Your profile has been updated.",
            parent=self.window,
        )
 
    def apply_profile_theme(self, theme):
        self.profile_page.configure(bg=theme["window"])
        self.profile_card.configure(bg=theme["table"])
        self.profile_form_frame.configure(bg=theme["table"])
 
        for label in (
            self.profile_title,
            self.profile_description,
            self.profile_note,
        ):
            label.configure(
                bg=theme["table"],
                fg=theme["text"],
            )
 
        self.profile_button_frame.configure(bg=theme["table"])
 
        for label in self.profile_field_labels:
            label.configure(
                bg=theme["table"],
                fg=theme["text"],
            )
 
        for frame in self.profile_entry_frames:
            frame.configure(
                bg=theme["list"],
                highlightbackground=theme["sidebar"],
                highlightcolor=theme["sidebar"],
            )
 
        for entry in self.profile_entries.values():
            entry.configure(
                bg=theme["list"],
                fg=theme["text"],
                insertbackground=theme["text"],
                disabledbackground=theme["list"],
                disabledforeground=theme["text"],
                highlightbackground=theme["table"],
                highlightcolor=theme["sidebar"],
            )
 
        for button in (
            self.profile_back_button,
            self.profile_edit_button,
            self.profile_cancel_button,
        ):
            button.configure(
                bg=theme["window"],
                fg=theme["text"],
                activebackground=theme["sidebar"],
                activeforeground=theme["text"],
            )
 
        self.profile_save_button.configure(
            bg="#2e7d32" if theme == DARK_MODE else "#cde8c5",
            fg="white" if theme == DARK_MODE else "black",
        )
 
    def show_page(self, page_key):
        page = self.pages[page_key]
        page.tkraise()
        self.current_page_key = page_key
        self.window.update_idletasks()
 
        if page_key in ("average", "history"):
            page.refresh_terms()
 
    def load_profile_data(self):
        """Read the logged-in student's details from the database."""
        data = {
            "first_name": "",
            "middle_name": "",
            "last_name": "",
            "phinmaed_email": "",
            "student_number": str(self.student_number or ""),
        }
        if self.student_number:
            try:
                profile = get_student_profile(self.student_number)
            except Exception as error:
                print(f"[DEBUG] Could not load profile: {error}")
                profile = None
            if profile:
                data.update({k: (v or "") for k, v in profile.items()})
        return data
if __name__ == "__main__":
    student_number = sys.argv[1] if len(sys.argv) > 1 else None
 
    root = tk.Tk()
    app = GradOApp(root, student_number)
    root.mainloop()