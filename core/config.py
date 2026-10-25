
LIGHT_MODE = {
    "window": "#f5f5dc",
    "sidebar": "#b9c5cc",
    "ribbon": "#fff2bb",
    "text": "black",
    "button": "#f5f5dc",
    "table": "#fff2bb",
    "list": "#f5f5dc",
}

DARK_MODE = {
    "window": "#1e1e1e",  # Outer window background
    "sidebar": "#121212",  # Left navigation sidebar
    "ribbon": "#0a0a0a",  # Header banner
    "button": "#2d2d2d",  # Sidebar buttons
    "table": "#2d2d2d",  # Inner card/panel backgrounds
    "list": "#3c3f41",  # Entry fields & dropdown list items
    "text": "#ffffff",  # All text labels
}

FIRST_SEM_FIRST_YEAR = [
    "GEN 001",
    "GEN 002",
    "GEN 006",
    "NST 015",
    "MAT 152",
    "PED 030",
]

SECOND_SEM_FIRST_YEAR = [
    "ART 002",
    "GEN 005",
    "GEN 008",
    "NST 016",
    "PED 031",
]

FIRST_SEM_SECOND_YEAR = [
    "ENG 216",
    "GEN 003",
    "HIS 007",
    "PED 032",
    "SSP 005",
]

SECOND_SEM_SECOND_YEAR = [
    "GEN 004",
    "GEN 009",
    "GEN 013",
    "PED 033",
    "SSP 006",
]

FIRST_SEM_THIRD_YEAR = [
    "BAM 285",
    "SSP 007",
]

SECOND_SEM_THIRD_YEAR = [
    "SSP 008",
]

FIRST_SEM_FOURTH_YEAR = [
    "BAM 286",
]

SUBJECT_GROUPS = {
    "1st Year - 1st Sem": (FIRST_SEM_FIRST_YEAR, "1st Year", "1st Semester"),
    "1st Year - 2nd Sem": (
        SECOND_SEM_FIRST_YEAR,
        "1st Year",
        "2nd Semester",
    ),
    "2nd Year - 1st Sem": (
        FIRST_SEM_SECOND_YEAR,
        "2nd Year",
        "1st Semester",
    ),
    "2nd Year - 2nd Sem": (
        SECOND_SEM_SECOND_YEAR,
        "2nd Year",
        "2nd Semester",
    ),
    "3rd Year - 1st Sem": (
        FIRST_SEM_THIRD_YEAR,
        "3rd Year",
        "1st Semester",
    ),
    "3rd Year - 2nd Sem": (
        SECOND_SEM_THIRD_YEAR,
        "3rd Year",
        "2nd Semester",
    ),
    "4th Year - 1st Sem": (
        FIRST_SEM_FOURTH_YEAR,
        "4th Year",
        "1st Semester",
    ),
}


GLOBAL_SUBJECTS = [
    "GEN 001",
    "GEN 002",
    "GEN 003",
    "GEN 004",
    "GEN 005",
    "GEN 006",
    "GEN 008",
    "GEN 009",
    "GEN 013",
    "GEN 014",
    "GEN 015",
    "GEN 016",
    "GEN 017",
    "GEN 018",
]

NON_GLOBAL_SUBJECTS = [
    "ITE 366",
    "ITE 260",
    "ITE 048",
    "ITE 186",
    "ITE 399",
    "ITE 393",
    "ITE 400",
    "ITE 314",
    "ITE 315",
    "ITE 316",
    "ITE 317",
    "ITE 318",
    "ITE 319",
    "ITE 320",
    "ITE 321",
    "ITE 322",
    "ITE 323",
    "ITE 324",
]

GLOBAL_EQUIVALENCY_DATA = [
    ("Grade", "Grade Point", "Remarks"),
    ("98.00-100.00", "1.0", ""),
    ("96.00-97.99", "1.25", ""),
    ("94.00-95.99", "1.50", ""),
    ("92.00-93.99", "1.75", ""),
    ("90.00-91.99", "2.0", ""),
    ("88.00-87.99", "2.25", ""),
    ("86.00-87.99", "2.50", ""),
    ("84.00-85.99", "2.75", ""),
    ("80.00-83.99", "3.0", "Passing Grade"),
    ("0.00-79.99", "3.25", "Failing Grade"),
]

NON_GLOBAL_EQUIVALENCY_DATA = [
    ("GRADE", "GRADE POINT", "REMARKS"),
    ("94.80-100.00", "1.0", ""),
    ("89.20-94.70", "1.25", ""),
    ("83.60-89.10", "1.50", ""),
    ("78.00-83.50", "1.75", ""),
    ("72.40-77.90", "2.0", ""),
    ("66.80-72.30", "2.25", ""),
    ("61.20-66.70", "2.50", ""),
    ("55.60-61.10", "2.75", ""),
    ("50.00-55.50", "3.0", "Passing Grade"),
    ("0.00-49.90", "3.25", "Failing Grade"),
]