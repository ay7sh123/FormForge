from flask import Blueprint, abort, redirect, render_template, request, url_for

from ..models import form as form_model
from ..utils.security import current_user
from ..utils.validators import clean_answers

bp = Blueprint("public", __name__)


@bp.get("/")
def index():
    if current_user():
        return redirect(url_for("forms.dashboard"))
    return render_template("index.html")


def _get_form_or_404(public_id):
    form = form_model.get_public_form(public_id)
    if form is None:
        abort(404)
    return form


def _closed_page(form):
    return render_template(
        "public_message.html",
        heading="This form is closed",
        message=f"“{form['title']}” isn't accepting responses right now.",
        page_title=form["title"],
    ), 200


@bp.get("/f/<public_id>")
def fill(public_id):
    form = _get_form_or_404(public_id)
    if not form.get("is_open", True):
        return _closed_page(form)
    return render_template(
        "public_form.html", form=form, values={}, errors={}, page_title=form["title"]
    )


@bp.post("/f/<public_id>")
def submit(public_id):
    form = _get_form_or_404(public_id)
    if not form.get("is_open", True):
        return _closed_page(form)

    # Hidden honeypot field: real people leave it empty, simple bots fill it in.
    if request.form.get("website"):
        return redirect(url_for("public.thanks", public_id=public_id))

    answers, errors = clean_answers(form, request.form)
    if errors:
        return render_template(
            "public_form.html",
            form=form,
            values=request.form,
            errors=errors,
            page_title=form["title"],
        ), 422

    form_model.add_response(form["_id"], answers)
    return redirect(url_for("public.thanks", public_id=public_id))


@bp.get("/f/<public_id>/thanks")
def thanks(public_id):
    form = _get_form_or_404(public_id)
    return render_template(
        "public_message.html",
        heading="Response recorded",
        message=f"Thanks. Your answers to “{form['title']}” have been submitted.",
        again_url=url_for("public.fill", public_id=public_id) if form.get("is_open", True) else None,
        page_title=form["title"],
    )
