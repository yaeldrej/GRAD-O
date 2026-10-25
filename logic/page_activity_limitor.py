#page_activity_limitor.py
import re

def validate_score(new_value):
        if new_value == "":
            return True
        if not re.fullmatch(r"(0|[1-9]\d{0,2})(\.\d{0,2})?", new_value):
            return False
        return float(new_value) <= 100