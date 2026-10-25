from tkinter import messagebox

def validate_input(P):
    if P == "":
        return True

    if len(P) > 1 and P[0] == "0" and P[1] != ".":
        messagebox.showerror(
            "Invalid Input", "Numbers starting with 0 cannot be followed by another number."
        )
        return False

    if P == ".":
        return True

    try:
        value = float(P)

        if 0 <= value <= 100:
            return True
        else:
            messagebox.showerror(
                "Invalid Input", "Please enter a number between 0 and 100."
            )
            return False

    except ValueError:
        return False