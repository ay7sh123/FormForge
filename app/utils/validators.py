import math
import re
import uuid
from datetime import date

QUESTION_TYPES = {
    "short_answer": "Short answer",
    "paragraph": "Paragraph",
    "email": "Email",
    "number": "Number",
    "date": "Date",
}

MAX_QUESTIONS = 50
ID_RE = re.compile(r"^[a-f0-9]{6,32}$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]{2,}$")
TEXT_LIMITS = {"short_answer": 500, "paragraph": 5000}


def clean_form_payload(data):
    """Validate and normalise the JSON sent by the form builder."""
    if not isinstance(data, dict):
        return None, ["Invalid request."]

    errors = []
    title = str(data.get("title") or "").strip()
    description = str(data.get("description") or "").strip()

    if not title:
        errors.append("Give your form a title.")
    elif len(title) > 150:
        errors.append("The title must be 150 characters or fewer.")
    if len(description) > 1000:
        errors.append("The description must be 1000 characters or fewer.")

    raw_questions = data.get("questions")
    if not isinstance(raw_questions, list) or not raw_questions:
        errors.append("Add at least one question.")
        raw_questions = []
    elif len(raw_questions) > MAX_QUESTIONS:
        errors.append(f"A form can have at most {MAX_QUESTIONS} questions.")
        raw_questions = []

    questions, seen = [], set()
    for number, raw in enumerate(raw_questions, start=1):
        if not isinstance(raw, dict):
            errors.append(f"Question {number} is invalid.")
            continue
        label = str(raw.get("label") or "").strip()
        qtype = raw.get("type")
        if not label:
            errors.append(f"Question {number} needs some text.")
        elif len(label) > 300:
            errors.append(f"Question {number} is longer than 300 characters.")
        if not (isinstance(qtype, str) and qtype in QUESTION_TYPES):
            errors.append(f"Question {number} has an unknown answer type.")

        qid = str(raw.get("id") or "")
        if not ID_RE.match(qid) or qid in seen:
            qid = uuid.uuid4().hex[:12]
        seen.add(qid)
        questions.append(
            {"id": qid, "label": label, "type": qtype, "required": raw.get("required") is True}
        )

    if errors:
        return None, errors
    return {"title": title, "description": description, "questions": questions}, []


def clean_answers(form, source):
    """Validate a submitted public form. Returns (answers, errors) keyed by question id."""
    answers, errors = {}, {}
    for q in form["questions"]:
        qid, qtype = q["id"], q["type"]
        value = (source.get(f"q_{qid}") or "").strip()

        if not value:
            if q["required"]:
                errors[qid] = "This question is required."
            else:
                answers[qid] = ""
            continue

        if qtype == "email":
            if len(value) > 254 or not EMAIL_RE.match(value):
                errors[qid] = "Enter a valid email address, like name@example.com."
                continue
            answers[qid] = value
        elif qtype == "number":
            try:
                num = float(value)
            except ValueError:
                errors[qid] = "Enter a valid number."
                continue
            if not math.isfinite(num) or abs(num) > 1e15:
                errors[qid] = "Enter a number between -1,000,000,000,000,000 and 1,000,000,000,000,000."
                continue
            answers[qid] = int(num) if num.is_integer() else num
        elif qtype == "date":
            try:
                if len(value) != 10:
                    raise ValueError
                answers[qid] = date.fromisoformat(value).isoformat()
            except ValueError:
                errors[qid] = "Enter a valid date."
                continue
        else:
            limit = TEXT_LIMITS.get(qtype, 500)
            if len(value) > limit:
                errors[qid] = f"Keep this answer under {limit} characters."
                continue
            answers[qid] = value
    return answers, errors
