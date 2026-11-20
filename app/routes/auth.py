import re

from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from ..models import user as user_model
from ..utils.security import (
    DUMMY_HASH,
    current_user,
    hash_password,
    login_user,
    safe_next_url,
    verify_password,
)

bp = Blueprint("auth", __name__)

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]{2,}$")


@bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user():
        return redirect(url_for("forms.dashboard"))

    values, errors = {}, {}
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")
        values = {"name": name, "email": email}

        if not name:
            errors["name"] = "Enter your name."
        elif len(name) > 80:
            errors["name"] = "Keep your name under 80 characters."
        if not EMAIL_RE.match(email) or len(email) > 254:
            errors["email"] = "Enter a valid email address."
        if len(password) < 8:
            errors["password"] = "Use at least 8 characters."
        elif len(password) > 128:
            errors["password"] = "Use 128 characters or fewer."
        elif password != confirm:
            errors["confirm_password"] = "The passwords don't match."

        if not errors:
            user = user_model.create_user(name, email, hash_password(password))
            if user is None:
                errors["email"] = "An account with this email already exists. Log in instead."
            else:
                login_user(user)
                flash(f"Welcome, {name}. Your account is ready.", "success")
                return redirect(url_for("forms.dashboard"))

    return render_template(
        "register.html", values=values, errors=errors, page_title="Create your account"
    ), (422 if errors else 200)


@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user():
        return redirect(url_for("forms.dashboard"))

    next_url = safe_next_url(request.args.get("next") or request.form.get("next"))
    error, email = None, ""
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = user_model.find_by_email(email)

        # Always run a hash check so response time doesn't reveal which emails exist.
        valid = verify_password(user["password_hash"] if user else DUMMY_HASH, password)
        if user and valid:
            login_user(user)
            return redirect(next_url or url_for("forms.dashboard"))
        error = "That email and password don't match."

    return render_template(
        "login.html", error=error, email=email, next_url=next_url, page_title="Log in"
    ), (401 if error else 200)


@bp.post("/logout")
def logout():
    session.clear()
    flash("You're logged out.", "success")
    return redirect(url_for("public.index"))
