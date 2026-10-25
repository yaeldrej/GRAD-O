#admin_py
from fractions import Fraction
from pathlib import Path
import sys
import tkinter as tk
import subprocess
from tkinter import ttk
from tkinter import messagebox 
from core.config import DARK_MODE, LIGHT_MODE
from pages.admin.page_activity_admin import ActivityPage
from pages.admin.page_average_admin import AveragePage
from pages.admin.page_calculator_admin import CalculatorPage
from pages.admin.page_history_admin import HistoryPage
from pages.admin.page_home_admin import HomePage
from pages.admin.page_period_calcu import PeriodCalculatorPage
from core.database import get_teacher_profile, update_teacher_profile
 
def admin_match_width(photo, target_width):
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
 
class AdminPage:
 
 
    def __init__(self, window_admin, admin_number=None):
        self.window_admin = window_admin
        self.admin_number = admin_number
        self.admin_settings_popup = None
        self.admin_profile_data = self.admin_load_profile_data()
        self.window_admin.geometry("1400x1000")
        self.window_admin.minsize(1400, 1000)
        self.window_admin.title("GRAD-O ADMIN PORTAL")
        self.window_admin.configure(bg=LIGHT_MODE["window"])
 
        self.admin_theme = LIGHT_MODE
 
        # Load Icons and Images
        self.admin_icon = tk.PhotoImage(file="Assets\\icon.png")
        self.window_admin.iconphoto(True, self.admin_icon)
 
        # Raw Full-Size Logos
        self.admin_logo = tk.PhotoImage(file="Assets\\logo.png")
        self.admin_logo_white = tk.PhotoImage(file="Assets\\white_logo.png")
 
        # Scaled Logos for Header Ribbon
        self.admin_ribbon_photo1 = self.admin_logo.subsample(2, 2)
        self.admin_ribbon_photo_white1 = admin_match_width(
            self.admin_logo_white, self.admin_ribbon_photo1.width()
        )
        
        # Scaled Logos for Page Background Center
        self.admin_bg_photo = self.admin_logo.subsample(1, 1)
        self.admin_bg_photo_white = admin_match_width(
            self.admin_logo_white, self.admin_bg_photo.width()
        )
 
        # Header Ribbon
        self.admin_header_label = tk.Label(
            window_admin,
            text="Fair Calculation, Goal-Oriented Do it With GRAD-O",
            font=("Arial", 15, "bold"),
            padx=20,
            fg=LIGHT_MODE["text"],
            bg=LIGHT_MODE["ribbon"],
            relief=tk.SOLID,
            bd=1,
            anchor="w",
            image=self.admin_ribbon_photo1,
            compound="left",
        )
        self.admin_header_label.pack(side=tk.TOP, fill=tk.X)
 
        self.admin_setup_sidebar()
 
        # Content Frame
        self.admin_content_frame = tk.Frame(window_admin, bg=LIGHT_MODE["window"])
        self.admin_content_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
 
        # Instantiate Pages with scaled background photos
        self.admin_pages = {
            "home": HomePage(self.admin_content_frame, self.admin_bg_photo),
            "calculator": CalculatorPage(self.admin_content_frame, self.admin_bg_photo),
            "activity": ActivityPage(
                self.admin_content_frame, self.window_admin, self.admin_bg_photo
            ),
            "period": PeriodCalculatorPage(self.admin_content_frame, self.admin_bg_photo, on_save=None, on_delete=None),
            "history": HistoryPage(self.admin_content_frame, self.admin_bg_photo, allow_search=True),
        }
 
        self.admin_pages["profile"] = self.admin_create_profile_page()
 
        for page in self.admin_pages.values():
            page.place(x=0, y=0, relwidth=1, relheight=1)
 
        self.admin_setup_styles()
        self.admin_show_page("home")
 
    def admin_load_profile_data(self):
        """Read the logged-in teacher's details from the database."""
        data = {
            "first_name": "",
            "middle_name": "",
            "last_name": "",
            "phinmaed_email": "",
            "employee_number": str(self.admin_number or ""),
        }
        if self.admin_number:
            try:
                profile = get_teacher_profile(self.admin_number)
            except Exception as error:
                print(f"[DEBUG] Could not load profile: {error}")
                profile = None
            if profile:
                data.update({k: (v or "") for k, v in profile.items()})
        return data
 
    def admin_setup_sidebar(self):
        self.admin_sidebar = tk.Frame(
            self.window_admin,
            height=300,
            width=200,
            bg=LIGHT_MODE["sidebar"],
            relief=tk.SOLID,
            bd=1,
        )
        self.admin_sidebar.pack(side="left", fill="y")
        self.admin_sidebar.pack_propagate(False)
 
        self.admin_button1 = tk.Button(
            self.admin_sidebar,
            text="HOME\nPAGE",
            font=("Titillium Web", 15, "bold"),
            bg=LIGHT_MODE["button"],
            fg=LIGHT_MODE["text"],
            relief="ridge",
            bd=5,
            command=lambda: self.admin_show_page("home"),
        )
        self.admin_button1.pack(side=tk.TOP, fill="x", padx=5, pady=10)
 
        self.admin_button2 = tk.Button(
            self.admin_sidebar,
            text="GRADE\nCALCULATOR",
            font=("Titillium Web", 15, "bold"),
            bg=LIGHT_MODE["button"],
            fg=LIGHT_MODE["text"],
            relief="ridge",
            bd=5,
            command=lambda: self.admin_show_page("calculator"),
        )
        self.admin_button2.pack(side="top", fill="x", padx=5, pady=10)
 
        self.admin_button3 = tk.Button(
            self.admin_sidebar,
            text="ACTIVITY\nCALCULATOR",
            font=("Titillium Web", 15, "bold"),
            bg=LIGHT_MODE["button"],
            fg=LIGHT_MODE["text"],
            relief="ridge",
            bd=5,
            command=lambda: self.admin_show_page("activity"),
        )
        self.admin_button3.pack(side="top", fill="x", padx=5, pady=10)
 
        self.admin_button4 = tk.Button(
            self.admin_sidebar,
            text="PERIOD\nCALCULATOR",
            font=("Titillium Web", 15, "bold"),
            bg=LIGHT_MODE["button"],
            fg=LIGHT_MODE["text"],
            relief="ridge",
            bd=5,
            command=lambda: self.admin_show_page("period"),
        )
        self.admin_button4.pack(side="top", fill="x", padx=5, pady=10)
 
        self.admin_button5 = tk.Button(
            self.admin_sidebar,
            text="GRADE\nHISTORY",
            font=("Titillium Web", 15, "bold"),
            bg=LIGHT_MODE["button"],
            fg=LIGHT_MODE["text"],
            relief="ridge",
            bd=5,
            command=lambda: self.admin_show_page("history"),
        )
        self.admin_button5.pack(side="top", fill="x", padx=5, pady=10)
 
        self.admin_bottom_frame = tk.Frame(self.admin_sidebar, bg=LIGHT_MODE["sidebar"])
        self.admin_bottom_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=10)
 
        self.admin_button6 = tk.Button(
            self.admin_bottom_frame,
            text="⚙️",
            font=("Arial", 10),
            bg=LIGHT_MODE["button"],
            fg=LIGHT_MODE["text"],
            relief="ridge",
            bd=5,
             command=self.admin_toggle_settings_popup,
        )
        self.admin_button6.pack(side=tk.LEFT)
 
        self.admin_button7 = tk.Button(
            self.admin_bottom_frame,
            text="🌙",
            font=("Arial", 10),
            bg=LIGHT_MODE["sidebar"],
            fg=LIGHT_MODE["text"],
            relief="flat",
            bd=5,
            command=lambda: self.admin_change_theme(DARK_MODE),
        )
        self.admin_button7.pack(side=tk.RIGHT, padx=3)
 
        self.admin_button8 = tk.Button(
            self.admin_bottom_frame,
            text="🔆",
            font=("Arial", 10),
            bg=LIGHT_MODE["sidebar"],
            fg=LIGHT_MODE["text"],
            relief="flat",
            bd=5,
            command=lambda: self.admin_change_theme(LIGHT_MODE),
        )
        self.admin_button8.pack(side=tk.RIGHT, padx=3)
 
    def admin_setup_styles(self):
        self.admin_style = ttk.Style()
        self.admin_style.theme_use("clam")
        self.admin_apply_ttk_theme(LIGHT_MODE)
 
    def admin_apply_ttk_theme(self, theme):
        self.admin_style.configure(
            "TCombobox",
            fieldbackground=theme["list"],
            background=theme["table"],
            foreground=theme["text"],
        )
        self.admin_style.map(
            "TCombobox",
            fieldbackground=[("readonly", theme["list"])],
            foreground=[("readonly", theme["text"])],
            selectbackground=[("readonly", theme["sidebar"])],
            selectforeground=[("readonly", theme["text"])],
        )
 
        self.admin_style.configure(
            "Treeview",
            background=theme["list"],
            foreground=theme["text"],
            fieldbackground=theme["list"],
        )
        self.admin_style.configure(
            "Treeview.Heading",
            background=theme["table"],
            foreground=theme["text"],
        )
        self.admin_style.map(
            "Treeview",
            background=[("selected", theme["sidebar"])],
            foreground=[("selected", theme["text"])],
        )
 
    def admin_change_theme(self, theme):
        self.admin_theme = theme
        self.window_admin.configure(bg=theme["window"])
        self.admin_content_frame.configure(bg=theme["window"])
        self.admin_sidebar.configure(bg=theme["sidebar"])
        self.admin_bottom_frame.configure(bg=theme["sidebar"])
 
        if theme == DARK_MODE:
            self.admin_header_label.configure(
                bg=theme["ribbon"],
                fg=theme["text"],
                image=self.admin_ribbon_photo_white1,
            )
        else:
            self.admin_header_label.configure(
                bg=theme["ribbon"],
                fg=theme["text"],
                image=self.admin_ribbon_photo1,
            )
 
        for btn in (
            self.admin_button1,
            self.admin_button2,
            self.admin_button3,
            self.admin_button4,
            self.admin_button5,
            self.admin_button6,
        ):
            btn.configure(
                bg=theme["button"],
                fg=theme["text"],
                activebackground=theme["button"],
                activeforeground=theme["text"],
            )
 
        self.admin_button7.configure(
            bg=theme["sidebar"],
            fg=theme["text"],
            activebackground=theme["sidebar"],
            activeforeground=theme["text"],
        )
        self.admin_button8.configure(
            bg=theme["sidebar"],
            fg=theme["text"],
            activebackground=theme["sidebar"],
            activeforeground=theme["text"],
        )
 
        self.admin_apply_ttk_theme(theme)
 
        # Pass the scaled bg_photo & bg_photo_white to apply_theme
        for page in self.admin_pages.values():
            if hasattr(page, "apply_theme"):
                page.apply_theme(theme, self.admin_bg_photo, self.admin_bg_photo_white)
 
        self.admin_apply_profile_theme(theme)
        if self.admin_settings_popup is not None and self.admin_settings_popup.winfo_exists():
            self.admin_settings_popup.configure(bg=theme["table"])
            for button in (
                self.admin_settings_logout_button,
                self.admin_settings_profile_button,
            ):
                button.configure(
                    bg=theme["window"],
                    fg=theme["text"],
                    activebackground=theme["sidebar"],
                    activeforeground=theme["text"],
                )
    # SETTINGS POPUP WITH LOG OUT AND EDIT PROFILE
    def admin_toggle_settings_popup(self):
        if self.admin_settings_popup is not None and self.admin_settings_popup.winfo_exists():
            self.admin_settings_popup.destroy()
            self.admin_settings_popup = None
            return
 
        self.admin_settings_popup = tk.Frame(
            self.window_admin, bg=self.admin_theme["table"], relief="solid", bd=2,
        )
 
        # Opens just above the bottom-left Settings icon and overlays the page
        self.admin_settings_popup.place( 
            x=0.5, rely=1.0, y=-120, width=220, height=55,
        )
        self.admin_settings_popup.lift()
 
        self.admin_settings_logout_button = tk.Button(
            self.admin_settings_popup, text="LOG OUT", font=("Arial", 9, "bold"), bg=self.admin_theme["window"],
            fg=self.admin_theme["text"], relief="ridge", bd=2, cursor="hand2",
            command=self.admin_confirm_logout,
        )
        self.admin_settings_logout_button.place(
            relx=0.04, rely=0.15, relwidth=0.45, relheight=0.60,
        )
 
        self.admin_settings_profile_button = tk.Button(
            self.admin_settings_popup, text="EDIT PROFILE", font=("Arial", 7, "bold"), bg=self.admin_theme["window"], fg=self.admin_theme["text"],
            relief="ridge", bd=2, cursor="hand2", command=self.admin_open_profile,
        )
        self.admin_settings_profile_button.place(
            relx=0.52, rely=0.15, relwidth=0.45, relheight=0.60
        )
    
    def admin_close_settings_popup(self):
        if self.admin_settings_popup is not None and self.admin_settings_popup.winfo_exists():
            self.admin_settings_popup.destroy()
        self.admin_settings_popup = None
 
    #DITO LOGOUT CONFIRMATION
 
    def admin_confirm_logout(self):
        self.admin_close_settings_popup()
 
        dialog = tk.Toplevel(self.window_admin)
        dialog.title("Log Out")
        dialog.configure(bg=self.admin_theme["window"])
        dialog.resizable(False, False)
        dialog.transient(self.window_admin)
 
        dialog_width = 380
        dialog_height = 180
        self.window_admin.update_idletasks()
        x = self.window_admin.winfo_rootx() + (self.window_admin.winfo_width() - dialog_width) // 2
        y = self.window_admin.winfo_rooty() + (self.window_admin.winfo_height() - dialog_height) // 2
        dialog.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")
 
        question = tk.Label(
            dialog, text="Do you want to log out?", font=("Arial", 15, "bold"),
            bg=self.admin_theme["window"],
            fg=self.admin_theme["text"],
        )
        question.pack(pady=(35, 25))
 
        button_frame = tk.Frame(dialog, bg=self.admin_theme["window"])
        button_frame.pack()
 
        yes_button = tk.Button(
            button_frame, text="YES", font=("Arial", 11, "bold"), width=10,
            bg="#ffb8b8", fg="black",
            command=lambda: self.admin_logout_to_login(dialog),
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
    
    def admin_logout_to_login(self, dialog):
        login_script = Path(__file__).resolve().parent / "login.py"
        try:
            subprocess.Popen(
                [sys.executable, str(login_script)],
                cwd=str(login_script.parent),
            )
            dialog.destroy()
            self.window_admin.destroy()
        except Exception as error:
            messagebox.showerror(
                "Log Out Error",
                f"Could not open the login page:\n{error}",
                parent=dialog,
            )
 
    #ITO NA YUNG PROFILE PAGE NA PWEDE MAG EDIT
    def admin_open_profile(self):
        self.admin_close_settings_popup()
        self.admin_show_page("profile")
 
    def admin_create_profile_page(self):
        page = tk.Frame(self.admin_content_frame, bg=LIGHT_MODE["window"])
        self.admin_profile_page = page
 
        self.admin_profile_card = tk.Frame(
            page, bg=LIGHT_MODE["table"], relief="solid", bd=2,
        )
        self.admin_profile_card.place(
            relx =0.5, rely=0.5, anchor="center", width = 620, height=610,
        )
 
        self.admin_profile_title = tk.Label(
            self.admin_profile_card, text="EDIT PROFILE", font=("Arial", 24, "bold"),
            bg=LIGHT_MODE["table"],
            fg=LIGHT_MODE["text"]
        )
        self.admin_profile_title.pack(pady=(25, 5))
 
        self.admin_profile_description = tk.Label(
            self.admin_profile_card, text="View or update your profile information", font=("Arial", 11),
            bg=LIGHT_MODE["table"],
            fg=LIGHT_MODE["text"],
        )
        self.admin_profile_description.pack(pady=(0, 18))
 
        # form_frame is now an attribute so admin_apply_profile_theme can recolor it
        self.admin_profile_form_frame = tk.Frame(self.admin_profile_card, bg=LIGHT_MODE["table"])
        self.admin_profile_form_frame.pack(fill= tk.X, padx=65)
        form_frame = self.admin_profile_form_frame
 
        self.admin_profile_field_labels = []
        self.admin_profile_entries = {}
        self.admin_profile_entry_frames = []
 
        profile_fields = (
            ("first_name", "FIRST NAME"),
            ("middle_name", "MIDDLE NAME"),
            ("last_name", "LAST NAME"),
            ("phinmaed_email", "PHINMAED EMAIL"),
            ("employee_number", "EMPLOYEE NUMBER"),
        )
 
        for key, label_text in profile_fields:
            field_label = tk.Label(
                form_frame, text=label_text, font=("Arial", 11, "bold"),
                bg=LIGHT_MODE["table"],
                fg=LIGHT_MODE["text"], anchor="w", 
            )
            field_label.pack(fill=tk.X, pady=(5, 2))
            self.admin_profile_field_labels.append(field_label)
 
            # entry_frame holds the entry and acts as its border
            entry_frame = tk.Frame(
                form_frame,
                bg=self.admin_theme["list"],
                highlightthickness=1,
                highlightbackground=self.admin_theme["sidebar"],
                highlightcolor=self.admin_theme["sidebar"],
            )
            entry_frame.pack(fill=tk.X, pady=(0, 10))
 
            field_entry = tk.Entry(
                entry_frame, font=("Arial", 12), justify="center",
                bg=self.admin_theme["list"], fg=self.admin_theme["text"],
                disabledbackground=self.admin_theme["list"],
                disabledforeground=self.admin_theme["text"],
                insertbackground=self.admin_theme["text"],
                relief="flat", bd=0, highlightthickness=0,
            )
            field_entry.pack(fill=tk.X, ipady=7)
            field_entry.insert(0, self.admin_profile_data.get(key, ""))
            field_entry.configure(state="disabled")
            self.admin_profile_entries[key] = field_entry
            self.admin_profile_entry_frames.append(entry_frame)
 
        self.admin_profile_note = tk.Label(
            self.admin_profile_card,
            text="", font=("Arial", 9), bg=LIGHT_MODE["table"], fg=LIGHT_MODE["text"],
            wraplength=490,
        )
        self.admin_profile_note.pack(pady=(6, 8))
 
        self.admin_profile_button_frame = tk.Frame(
            self.admin_profile_card,
            bg=LIGHT_MODE["table"],
        )
        self.admin_profile_button_frame.pack(pady=10)
 
        self.admin_profile_back_button = tk.Button(
            self.admin_profile_button_frame, text="BACK TO HOME", font=("Arial", 10, "bold"), bg=LIGHT_MODE["window"], fg=LIGHT_MODE["text"],
            relief="ridge", bd=2, cursor="hand2",
            command=lambda: self.admin_show_page("home"),
        )
        self.admin_profile_back_button.pack(side=tk.LEFT, padx=6)
 
        self.admin_profile_edit_button = tk.Button(
            self.admin_profile_button_frame, text="EDIT PROFILE", font=("Arial", 10, "bold"),
            bg=LIGHT_MODE["window"], fg=LIGHT_MODE["text"], relief="ridge", bd=2, cursor="hand2",
            command=self.admin_enable_profile_edit,
        )   
        self.admin_profile_edit_button.pack(side=tk.LEFT, padx=6)
 
        self.admin_profile_save_button = tk.Button(
            self.admin_profile_button_frame, text="SAVE CHANGES", font=("Arial", 10, "bold"),
            bg="#cde8c5", fg="black", relief="ridge", bd=2, cursor="hand2",
            command=self.admin_save_profile_changes,
        )
 
        self.admin_profile_cancel_button = tk.Button(
            self.admin_profile_button_frame,
            text="CANCEL", font=("Titillium Web", 10, "bold"), bg=LIGHT_MODE["window"], fg=LIGHT_MODE["text"],
            relief="ridge", bd=2, cursor="hand2", command=self.admin_cancel_profile_edit,
        )
 
        return page
 
    def admin_enable_profile_edit(self):
        for key, entry in self.admin_profile_entries.items():
            if key == "employee_number":
                continue  # the employee number identifies the account, never editable
            entry.configure(state="normal")
 
        self.admin_profile_back_button.pack_forget()
        self.admin_profile_edit_button.pack_forget()
        self.admin_profile_save_button.pack(side=tk.LEFT, padx=6)
        self.admin_profile_cancel_button.pack(side=tk.LEFT, padx=6)
 
    def admin_cancel_profile_edit(self):
        for key, entry in self.admin_profile_entries.items():
            entry.configure(state="normal")
            entry.delete(0, tk.END)
            entry.insert(0, self.admin_profile_data.get(key, ""))
            entry.configure(state="disabled")
 
        self.admin_profile_save_button.pack_forget()
        self.admin_profile_cancel_button.pack_forget()
        self.admin_profile_back_button.pack(side=tk.LEFT, padx=6)
        self.admin_profile_edit_button.pack(side=tk.LEFT, padx=6)
    
    def admin_save_profile_changes(self):
        updated_profile = {
            key: entry.get().strip()
            for key, entry in self.admin_profile_entries.items()
        }
 
        required = ("first_name", "last_name", "phinmaed_email")
        if any(not updated_profile[key] for key in required):
            messagebox.showwarning(
                "Missing Information",
                "Please fill in your first name, last name, and PHINMAED email.",
                parent=self.window_admin,
            )
            return
 
        email = updated_profile["phinmaed_email"].lower()
        if not email.endswith("@phinmaed.com"):
            messagebox.showwarning(
                "Invalid Email",
                "Please use a valid @phinmaed.com email address.",
                parent=self.window_admin,
            )
            return
        updated_profile["phinmaed_email"] = email
 
        try:
            update_teacher_profile(
                self.admin_number,
                updated_profile["first_name"],
                updated_profile["middle_name"],
                updated_profile["last_name"],
                updated_profile["phinmaed_email"],
            )
        except Exception as error:
            messagebox.showerror(
                "Could Not Save", str(error), parent=self.window_admin
            )
            return
 
        updated_profile["employee_number"] = self.admin_profile_data["employee_number"]
        self.admin_profile_data = updated_profile
 
        # show the cleaned values and lock the fields again
        for key, entry in self.admin_profile_entries.items():
            entry.configure(state="normal")
            entry.delete(0, tk.END)
            entry.insert(0, self.admin_profile_data.get(key, ""))
            entry.configure(state="disabled")
 
        self.admin_profile_save_button.pack_forget()
        self.admin_profile_cancel_button.pack_forget()
        self.admin_profile_back_button.pack(side=tk.LEFT, padx=6)
        self.admin_profile_edit_button.pack(side=tk.LEFT, padx=6)
 
        messagebox.showinfo(
            "Profile Updated",
            "Your profile has been updated.",
            parent=self.window_admin,
        )   
 
    def admin_apply_profile_theme(self, theme):
        if not hasattr(self, "admin_profile_page"):
            return
 
        self.admin_profile_page.configure(bg=theme["window"])
        self.admin_profile_card.configure(bg=theme["table"])
        self.admin_profile_form_frame.configure(bg=theme["table"])
        self.admin_profile_title.configure(bg=theme["table"], fg=theme["text"])
        self.admin_profile_description.configure(bg=theme["table"], fg=theme["text"])
        self.admin_profile_note.configure(bg=theme["table"], fg=theme["text"])
        self.admin_profile_button_frame.configure(bg=theme["table"])
 
        for label in self.admin_profile_field_labels:
            label.configure(bg=theme["table"], fg=theme["text"])
 
        for frame in self.admin_profile_entry_frames:
            frame.configure(
                bg=theme["list"],
                highlightbackground=theme["sidebar"],
                highlightcolor=theme["sidebar"],
            )
 
        for entry in self.admin_profile_entries.values():
            entry.configure(
                bg=theme["list"],
                fg=theme["text"],
                insertbackground=theme["text"],
                disabledbackground=theme["list"],
                disabledforeground=theme["text"],
            )
 
        for button in (
            self.admin_profile_back_button,
            self.admin_profile_edit_button,
            self.admin_profile_cancel_button,
        ):
            button.configure(
                bg=theme["window"],
                fg=theme["text"],
                activebackground=theme["sidebar"],
                activeforeground=theme["text"],
            )
 
        self.admin_profile_save_button.configure(
            bg="#cde8c5",
            fg="black",
        )
 
    def admin_show_page(self, page_key):
        page = self.admin_pages[page_key]
        page.tkraise()
        self.current_admin_page_key = page_key
        self.window_admin.update_idletasks()
 
        if page_key in ("average", "history"):
            page.refresh_terms()
if __name__ == "__main__":
    admin_number = sys.argv[1] if len(sys.argv) > 1 else None
 
    admin_root = tk.Tk()
    admin_app = AdminPage(admin_root, admin_number)
    admin_root.mainloop()