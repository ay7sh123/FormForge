from datetime import datetime, timezone

from bson import ObjectId
from bson.errors import InvalidId
from pymongo.errors import DuplicateKeyError

from ..database import get_db


def _users():
    return get_db()["users"]


def create_user(name, email, password_hash):
    """Insert a user. Returns the document, or None if the email is taken."""
    doc = {
        "name": name,
        "email": email,
        "password_hash": password_hash,
        "created_at": datetime.now(timezone.utc),
    }
    try:
        result = _users().insert_one(doc)
    except DuplicateKeyError:
        return None
    doc["_id"] = result.inserted_id
    return doc


def find_by_email(email):
    return _users().find_one({"email": email})


def find_by_id(user_id):
    try:
        return _users().find_one({"_id": ObjectId(user_id)})
    except (InvalidId, TypeError):
        return None
