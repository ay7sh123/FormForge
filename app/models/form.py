import secrets
from datetime import datetime, timezone

from bson import ObjectId
from bson.errors import InvalidId

from ..database import get_db


def _forms():
    return get_db()["forms"]


def _responses():
    return get_db()["responses"]


def _now():
    return datetime.now(timezone.utc)


def _oid(value):
    try:
        return ObjectId(value)
    except (InvalidId, TypeError):
        return None


def to_dict(form):
    """JSON-safe version of a form document (used by the builder)."""
    return {
        "id": str(form["_id"]),
        "public_id": form["public_id"],
        "title": form["title"],
        "description": form.get("description", ""),
        "questions": form["questions"],
        "is_open": form.get("is_open", True),
    }


# ---------------------------------------------------------------- forms
def create_form(owner_id, data):
    now = _now()
    doc = {
        "owner_id": owner_id,
        "public_id": secrets.token_urlsafe(8),
        "title": data["title"],
        "description": data["description"],
        "questions": data["questions"],
        "is_open": True,
        "created_at": now,
        "updated_at": now,
    }
    doc["_id"] = _forms().insert_one(doc).inserted_id
    return doc


def get_owned_form(owner_id, form_id):
    oid = _oid(form_id)
    if oid is None:
        return None
    return _forms().find_one({"_id": oid, "owner_id": owner_id})


def get_public_form(public_id):
    return _forms().find_one({"public_id": public_id})


def list_forms(owner_id):
    """All forms of a user (newest first) with a `response_count` on each."""
    forms = list(_forms().find({"owner_id": owner_id}).sort("created_at", -1))
    if forms:
        pipeline = [
            {"$match": {"form_id": {"$in": [f["_id"] for f in forms]}}},
            {"$group": {"_id": "$form_id", "n": {"$sum": 1}}},
        ]
        counts = {row["_id"]: row["n"] for row in _responses().aggregate(pipeline)}
        for f in forms:
            f["response_count"] = counts.get(f["_id"], 0)
    return forms


def update_form(owner_id, form_id, data):
    oid = _oid(form_id)
    if oid is None:
        return None
    result = _forms().update_one(
        {"_id": oid, "owner_id": owner_id},
        {"$set": {
            "title": data["title"],
            "description": data["description"],
            "questions": data["questions"],
            "updated_at": _now(),
        }},
    )
    if result.matched_count != 1:
        return None
    return _forms().find_one({"_id": oid})


def set_open(owner_id, form_id, is_open):
    oid = _oid(form_id)
    if oid is None:
        return False
    result = _forms().update_one(
        {"_id": oid, "owner_id": owner_id}, {"$set": {"is_open": bool(is_open)}}
    )
    return result.matched_count == 1


def delete_form(owner_id, form_id):
    """Delete a form and every response collected for it."""
    oid = _oid(form_id)
    if oid is None:
        return False
    result = _forms().delete_one({"_id": oid, "owner_id": owner_id})
    if result.deleted_count != 1:
        return False
    _responses().delete_many({"form_id": oid})
    return True


# ------------------------------------------------------------ responses
def add_response(form_id, answers):
    doc = {"form_id": form_id, "answers": answers, "submitted_at": _now()}
    _responses().insert_one(doc)
    return doc


def list_responses(form_id):
    return list(_responses().find({"form_id": form_id}).sort("submitted_at", -1))


def count_responses(form_id):
    return _responses().count_documents({"form_id": form_id})


def delete_response(form_id, response_id):
    rid = _oid(response_id)
    if rid is None:
        return False
    result = _responses().delete_one({"_id": rid, "form_id": form_id})
    return result.deleted_count == 1
