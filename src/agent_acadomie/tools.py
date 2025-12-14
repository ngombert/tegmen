"""Tools for Agent Acadomie."""

import json
from datetime import datetime, timedelta


def get_school_calendar(student_name: str) -> str:
    """Retrieves the school calendar for a student.

    Args:
        student_name: The name of the student.

    Returns:
        A formatted string containing upcoming school events.
    """
    # Mock data
    today = datetime.now()
    events = [
        {
            "date": (today + timedelta(days=2)).strftime("%Y-%m-%d"),
            "event": "Examen de Mathématiques",
        },
        {
            "date": (today + timedelta(days=5)).strftime("%Y-%m-%d"),
            "event": "Sortie scolaire au musée",
        },
        {
            "date": (today + timedelta(days=10)).strftime("%Y-%m-%d"),
            "event": "Début des vacances d'hiver",
        },
    ]
    return json.dumps(
        {"student": student_name, "upcoming_events": events}, ensure_ascii=False
    )


def get_student_grades(student_name: str, subject: str = None) -> str:
    """Retrieves grades for a student, optionally filtered by subject.

    Args:
        student_name: The name of the student.
        subject: Optional subject to filter grades (e.g., 'Math', 'Français').

    Returns:
        A formatted string containing the student's grades.
    """
    # Mock data
    grades = {
        "Mathématiques": [15, 14, 18],
        "Français": [12, 16],
        "Histoire": [14, 15],
        "Anglais": [17],
    }

    data = {"student": student_name}
    if subject:
        # Simple fuzzy match
        found_subject = None
        for key in grades:
            if subject.lower() in key.lower():
                found_subject = key
                break

        if found_subject:
            data["grades"] = {found_subject: grades[found_subject]}
        else:
            return f"Aucune note trouvée pour la matière '{subject}'."
    else:
        data["grades"] = grades

    return json.dumps(data, ensure_ascii=False)


def get_homework(student_name: str) -> str:
    """Retrieves the list of homework assignments for a student.

    Args:
        student_name: The name of the student.

    Returns:
        A formatted string containing homework assignments.
    """
    # Mock data
    homework = [
        {
            "subject": "Mathématiques",
            "task": "Exercices page 42, n° 3 et 4",
            "due_date": "Demain",
        },
        {
            "subject": "Français",
            "task": "Lire le chapitre 3 de Molière",
            "due_date": "Lundi prochain",
        },
    ]
    return json.dumps(
        {"student": student_name, "homework": homework}, ensure_ascii=False
    )
