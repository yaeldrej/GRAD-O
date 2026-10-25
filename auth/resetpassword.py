"""
reset_password.py

Forgot-password flow for GRAD-O:
    username -> 6-digit code sent by email -> verify -> set new password

Used by login.py like this:

    reset_flow = PasswordReset(
        window=window,
        get_role=lambda: selected_role,
        show_login=show_login,
        clear_window=clear_window,
        add_back_button=add_back_button,
        create_input_field=create_input_field,
    )
    # then: command=reset_flow.show_forgot_password
"""

import os
import time
import hmac
import hashlib
import secrets
import smtplib
import threading
import tkinter as tk
from email.message import EmailMessage
from tkinter import messagebox

from core.database import get_email_by_username, update_password

# database.py already loads database.env, so these are available here.
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

OTP_LIFETIME_SECONDS = 10 * 60
OTP_MAX_ATTEMPTS = 5
OTP_RESEND_COOLDOWN = 60
MIN_PASSWORD_LENGTH = 8

BG = "#f5f5dc"


def _hash_otp(otp):
    return hashlib.sha256(otp.encode()).hexdigest()


def send_otp_email(to_email, otp):
    msg = EmailMessage()
    msg["Subject"] = "GRAD-O Password Reset Code"
    msg["From"] = SMTP_USER
    msg["To"] = to_email
    msg.set_content(
        f"Your GRAD-O password reset code is: {otp}\n\n"
        f"It expires in {OTP_LIFETIME_SECONDS // 60} minutes.\n"
        "If you did not request this, you can ignore this email."
    )
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as server:
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(msg)


class PasswordReset:
    def __init__(
        self,
        window,
        get_role,
        show_login,
        clear_window,
        add_back_button,
        create_input_field,
    ):
        self.window = window
        self.get_role = get_role  # callable returning "student" or "teacher"
        self.show_login = show_login
        self.clear_window = clear_window
        self.add_back_button = add_back_button
        self.create_input_field = create_input_field
        self.state = {}
        self.clear_state()

    # ---------- state ----------
    def clear_state(self):
        self.state = {
            "username": "",
            "role": "",
            "otp_hash": None,
            "expires_at": 0,
            "attempts": 0,
            "last_sent": 0,
            "verified": False,
        }

    # ---------- screen 1: request + verify code ----------
    def show_forgot_password(self, username_prefill=""):
        self.clear_window()

        tk.Label(
            self.window,
            text="FORGOT PASSWORD",
            font=("Arial", 25, "bold"),
            bg=BG,
        ).pack(pady=(65, 10))

        tk.Label(
            self.window,
            text="Enter your username, then request a 6-digit code.\n"
            "The code will be sent to your registered PHINMAED email.",
            font=("Arial", 12),
            bg=BG,
        ).pack(pady=5)

        username_entry = self.create_input_field(self.window, "Username")
        if username_prefill:
            username_entry.insert(0, username_prefill)

        send_button = tk.Button(
            self.window,
            text="SEND CODE",
            font=("Arial", 11, "bold"),
            width=22,
        )
        send_button.config(
            command=lambda: self.send_code(username_entry, send_button)
        )
        send_button.pack(pady=(15, 5))

        code_entry = self.create_input_field(self.window, "6-digit code")

        tk.Button(
            self.window,
            text="VERIFY CODE",
            font=("Arial", 11, "bold"),
            width=22,
            command=lambda: self.verify_code(username_entry, code_entry),
        ).pack(pady=5)

        self.add_back_button(self.show_login)

    def send_code(self, username_entry, send_button):
        role = self.get_role()
        username = username_entry.get().strip().lower()

        if not username:
            messagebox.showwarning(
                "Missing Username", "Please enter your username first."
            )
            return

        if not SMTP_USER or not SMTP_PASSWORD:
            messagebox.showerror(
                "Email Not Configured",
                "SMTP_USER and SMTP_PASSWORD are missing from database.env.",
            )
            return

        wait = OTP_RESEND_COOLDOWN - (time.time() - self.state["last_sent"])
        if wait > 0:
            messagebox.showwarning(
                "Please Wait",
                f"You can request a new code in {int(wait)} seconds.",
            )
            return

        try:
            email = get_email_by_username(username, role)
        except Exception as e:
            messagebox.showerror(
                "Database Error", f"Could not look up account: {e}"
            )
            return

        generic_msg = (
            "If that account exists, a 6-digit code has been sent "
            "to its registered email."
        )

        # Same message whether or not the account exists, so nobody can
        # use this screen to discover valid usernames.
        if not email:
            messagebox.showerror("Not Found", "No account with that username.")
            return

        otp = f"{secrets.randbelow(1_000_000):06d}"
        self.state.update(
            username=username,
            role=role,
            otp_hash=_hash_otp(otp),
            expires_at=time.time() + OTP_LIFETIME_SECONDS,
            attempts=0,
            last_sent=time.time(),
            verified=False,
        )

        send_button.config(state="disabled", text="SENDING...")

        def worker():
            error = None
            try:
                send_otp_email(email, otp)
            except Exception as e:
                error = e
            try:
                self.window.after(0, lambda: on_done(error))
            except Exception:
                pass

        def on_done(error):
            if send_button.winfo_exists():
                send_button.config(state="normal", text="SEND CODE")
            if error:
                self.clear_state()
                messagebox.showerror(
                    "Email Error", f"Could not send the email: {error}"
                )
            else:
                messagebox.showinfo("Code Sent", generic_msg)

        threading.Thread(target=worker, daemon=True).start()

    def verify_code(self, username_entry, code_entry):
        role = self.get_role()
        username = username_entry.get().strip().lower()
        code = code_entry.get().strip()

        if not username or not code:
            messagebox.showwarning(
                "Missing Information",
                "Please enter your username and the code.",
            )
            return

        if not (code.isdigit() and len(code) == 6):
            messagebox.showwarning(
                "Invalid Code", "The code must be 6 digits."
            )
            return

        if (
            not self.state["otp_hash"]
            or self.state["username"] != username
            or self.state["role"] != role
        ):
            messagebox.showerror(
                "No Code", "Please request a code for this account first."
            )
            return

        if time.time() > self.state["expires_at"]:
            self.clear_state()
            messagebox.showerror(
                "Code Expired",
                "This code has expired. Please request a new one.",
            )
            return

        self.state["attempts"] += 1

        if not hmac.compare_digest(_hash_otp(code), self.state["otp_hash"]):
            left = OTP_MAX_ATTEMPTS - self.state["attempts"]
            if left <= 0:
                self.clear_state()
                messagebox.showerror(
                    "Too Many Attempts", "Please request a new code."
                )
            else:
                messagebox.showerror(
                    "Incorrect Code",
                    f"That code is wrong. {left} attempt(s) left.",
                )
            return

        self.state["verified"] = True
        self.state["otp_hash"] = None  # single use
        self.show_reset_password(username)

    # ---------- screen 2: new password ----------
    def show_reset_password(self, username):
        self.clear_window()

        tk.Label(
            self.window,
            text="SET NEW PASSWORD",
            font=("Arial", 25, "bold"),
            bg=BG,
        ).pack(pady=(75, 10))

        tk.Label(
            self.window,
            text=f"Username: {username}",
            font=("Arial", 12),
            bg=BG,
        ).pack(pady=5)

        new_password_entry = self.create_input_field(
            self.window, "New password", show_char="*"
        )
        confirm_password_entry = self.create_input_field(
            self.window, "Verify New password", show_char="*"
        )

        tk.Button(
            self.window,
            text="RESET PASSWORD",
            font=("Arial", 11, "bold"),
            width=22,
            command=lambda: self.reset_password(
                username, new_password_entry, confirm_password_entry
            ),
        ).pack(pady=15)

        def cancel():
            self.clear_state()
            self.show_login()

        self.add_back_button(cancel)

    def reset_password(
        self, username, new_password_entry, confirm_password_entry
    ):
        role = self.get_role()
        new_password = new_password_entry.get()
        confirm_password = confirm_password_entry.get()

        if (
            not self.state["verified"]
            or self.state["username"] != username
            or self.state["role"] != role
        ):
            messagebox.showerror(
                "Verification Required",
                "Please verify your code before resetting the password.",
            )
            return

        if not new_password or not confirm_password:
            messagebox.showwarning(
                "Missing Information", "Please fill in both password fields."
            )
            return

        if new_password != confirm_password:
            messagebox.showerror(
                "Password Mismatch",
                "The new passwords do not match. Please try again.",
            )
            return

        if len(new_password) < MIN_PASSWORD_LENGTH:
            messagebox.showwarning(
                "Weak Password",
                f"Use at least {MIN_PASSWORD_LENGTH} characters.",
            )
            return

        try:
            update_password(username, new_password, role)
        except Exception as e:
            messagebox.showerror(
                "Database Error", f"Could not update password: {e}"
            )
            return

        self.clear_state()
        messagebox.showinfo(
            "Success", "Your password has been reset. Please log in."
        )
        self.show_login()

        
