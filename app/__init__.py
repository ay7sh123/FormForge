import secrets

from flask import Flask, abort, jsonify, render_template, request, session

from config import Config, DEFAULT_SECRET

from .database import init_db
from .utils.security import current_user, generate_csrf_token

# Endpoints that anonymous visitors use; they carry no login session to protect.
CSRF_EXEMPT = {"public.submit"}


def create_app(config_object=Config):
    app = Flask(__name__)
    app.config.from_object(config_object)

    if app.config["SECRET_KEY"] == DEFAULT_SECRET:
        print("WARNING: using the default SECRET_KEY. Set SECRET_KEY in .env before deploying.")

    init_db(app)

    from .routes.auth import bp as auth_bp
    from .routes.forms import bp as forms_bp
    from .routes.public import bp as public_bp

    app.register_blueprint(public_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(forms_bp)

    # ---------- CSRF protection for logged-in actions ----------
    @app.before_request
    def csrf_protect():
        if request.method not in ("POST", "PUT", "PATCH", "DELETE"):
            return None
        if request.endpoint in CSRF_EXEMPT:
            return None
        expected = session.get("csrf_token")
        sent = request.headers.get("X-CSRF-Token") or request.form.get("csrf_token")
        if not expected or not sent or not secrets.compare_digest(expected, sent):
            if request.path.startswith("/api/"):
                return jsonify(error="Your session expired. Refresh the page and try again."), 400
            abort(400)
        return None

    @app.after_request
    def security_headers(resp):
        resp.headers.setdefault("X-Content-Type-Options", "nosniff")
        resp.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        return resp

    @app.context_processor
    def inject_globals():
        return {"csrf_token": generate_csrf_token, "current_user": current_user()}

    # ---------- Template filters ----------
    @app.template_filter("iso")
    def iso(value):
        return value.strftime("%Y-%m-%dT%H:%M:%SZ") if value else ""

    @app.template_filter("datefmt")
    def datefmt(value):
        return value.strftime("%d %b %Y") if value else ""

    @app.template_filter("datetimefmt")
    def datetimefmt(value):
        return value.strftime("%d %b %Y, %H:%M UTC") if value else ""

    # ---------- Error pages ----------
    messages = {
        400: ("Request rejected", "The request could not be verified. Go back, refresh the page and try again."),
        404: ("Page not found", "That page doesn't exist, or you don't have access to it."),
        413: ("Request too large", "That submission is too big to process."),
        500: ("Something went wrong", "An unexpected error happened on our side. Please try again."),
    }

    def make_handler(code):
        def handler(_err):
            title, text = messages[code]
            if request.path.startswith("/api/"):
                return jsonify(error=text), code
            return render_template("error.html", code=code, title=title, text=text), code
        return handler

    for code in messages:
        app.register_error_handler(code, make_handler(code))

    return app
