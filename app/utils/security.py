import secrets
from functools import wraps

from flask import g, jsonify, redirect, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from ..models import user as user_model


def hash_password(password: str) -> str:
    """Salted PBKDF2-SHA256 hash (portable across Python builds)."""
    return generate_password_hash(password, method="pbkdf2:sha256", salt_length=16)


def verify_password(stored_hash: str, password: str) -> bool:
    return check_password_hash(stored_hash, password)


# Used to keep login timing similar whether or not the email exists.
DUMMY_HASH = hash_password("formforge-dummy-password")


def current_user():
    """Return the logged-in user document (cached per request) or None."""
    if "user" in g.__dict__:
        return g.user
    user = None
    user_id = session.get("user_id")
    if user_id:
        user = user_model.find_by_id(user_id)
        if user is None:
            session.pop("user_id", None)
    g.user = user
    return user


def login_user(user):
    session.clear()
    session["user_id"] = str(user["_id"])
    session.permanent = True


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if current_user() is None:
            if request.path.startswith("/api/"):
                return jsonify(error="Please log in to continue."), 401
            return redirect(url_for("auth.login", next=request.full_path.rstrip("?")))
        return view(*args, **kwargs)

    return wrapped


def generate_csrf_token():
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_urlsafe(32)
    return session["csrf_token"]


def safe_next_url(target):
    """Only allow same-site relative redirects."""
    if target and target.startswith("/") and not target.startswith("//") and "\\" not in target:
        return target
    return None
