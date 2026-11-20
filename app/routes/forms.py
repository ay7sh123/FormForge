import csv
import io
import re

from flask import (
    Blueprint,
    Response,
    abort,
    jsonify,
    render_template,
    request,
)

from ..models import form as form_model
from ..utils.security import current_user, login_required
from ..utils.validators import QUESTION_TYPES, clean_form_payload

bp = Blueprint("forms", __name__)


def _owned_or_404(form_id):
    form = form_model.get_owned_form(current_user()["_id"], form_id)
    if form is None:
        abort(404)
    return form


# ------------------------------------------------------------ pages
@bp.get("/dashboard")
@login_required
def dashboard():
    forms = form_model.list_forms(current_user()["_id"])
    return render_template("dashboard.html", forms=forms, page_title="Your forms")


@bp.get("/forms/new")
@login_required
def new_form():
    blank = {
        "id": None, "public_id": None, "title": "", "description": "",
        "questions": [], "is_open": True,
    }
    return render_template("builder.html", form=blank, page_title="New form")


@bp.get("/forms/<form_id>/edit")
@login_required
def edit_form(form_id):
    form = _owned_or_404(form_id)
    return render_template(
        "builder.html", form=form_model.to_dict(form), page_title=f"Edit {form['title']}"
    )


@bp.get("/forms/<form_id>/responses")
@login_required
def responses(form_id):
    form = _owned_or_404(form_id)
    rows = form_model.list_responses(form["_id"])
    return render_template(
        "responses.html",
        form=form,
        responses=rows,
        types=QUESTION_TYPES,
        page_title=f"Responses to {form['title']}",
    )


def _csv_safe(value, qtype):
    """Stop spreadsheet apps from running text such as =SUM() as a formula."""
    text = "" if value is None else str(value)
    if qtype != "number" and text[:1] in ("=", "+", "-", "@", "\t", "\r"):
        return "'" + text
    return text


@bp.get("/forms/<form_id>/responses/export.csv")
@login_required
def export_csv(form_id):
    form = _owned_or_404(form_id)
    rows = form_model.list_responses(form["_id"])

    buffer = io.StringIO()
    buffer.write("\ufeff")  # BOM so Excel reads UTF-8 correctly
    writer = csv.writer(buffer)
    writer.writerow(["Submitted (UTC)"] + [q["label"] for q in form["questions"]])
    for r in rows:
        writer.writerow(
            [r["submitted_at"].strftime("%Y-%m-%d %H:%M:%S")]
            + [_csv_safe(r["answers"].get(q["id"], ""), q["type"]) for q in form["questions"]]
        )

    slug = re.sub(r"[^A-Za-z0-9]+", "-", form["title"]).strip("-").lower() or "form"
    return Response(
        buffer.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{slug}-responses.csv"'},
    )


# -------------------------------------------------------------- API
@bp.post("/api/forms")
@login_required
def api_create():
    data, errors = clean_form_payload(request.get_json(silent=True))
    if errors:
        return jsonify(error=errors[0], errors=errors), 422
    form = form_model.create_form(current_user()["_id"], data)
    return jsonify(form=form_model.to_dict(form)), 201


@bp.put("/api/forms/<form_id>")
@login_required
def api_update(form_id):
    data, errors = clean_form_payload(request.get_json(silent=True))
    if errors:
        return jsonify(error=errors[0], errors=errors), 422
    form = form_model.update_form(current_user()["_id"], form_id, data)
    if form is None:
        abort(404)
    return jsonify(form=form_model.to_dict(form))


@bp.post("/api/forms/<form_id>/toggle")
@login_required
def api_toggle(form_id):
    form = _owned_or_404(form_id)
    new_state = not form.get("is_open", True)
    form_model.set_open(current_user()["_id"], form_id, new_state)
    return jsonify(is_open=new_state)


@bp.delete("/api/forms/<form_id>")
@login_required
def api_delete(form_id):
    if not form_model.delete_form(current_user()["_id"], form_id):
        abort(404)
    return jsonify(ok=True)


@bp.delete("/api/forms/<form_id>/responses/<response_id>")
@login_required
def api_delete_response(form_id, response_id):
    form = _owned_or_404(form_id)
    if not form_model.delete_response(form["_id"], response_id):
        abort(404)
    return jsonify(ok=True, count=form_model.count_responses(form["_id"]))
