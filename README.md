# FormForge: Online Form Generation System

A Google Forms-style app. Create an account, build forms with a dynamic builder,
share a public link, collect responses and review them in a table.

**Stack:** HTML / CSS / JavaScript (frontend) · Python Flask (backend) · MongoDB (database) · hashed passwords (PBKDF2-SHA256)

## Features

- Register and log in (passwords are salted and hashed, never stored in plain text)
- Dashboard listing your forms with response counts
- Dynamic form builder: add, edit, duplicate, reorder and delete questions
- Question types: Short answer, Paragraph, Email, Number, Date
- Required questions (checked in the browser and again on the server)
- Public sharing link for every form (`/f/<public-id>`), no login needed to respond
- Open or close a form to stop accepting responses
- View, delete and export (CSV) submitted responses
- Delete forms (their responses are deleted too)

## Folder structure

```
FormForge/
├── run.py                  # starts the dev server
├── config.py               # settings read from .env
├── requirements.txt
├── .env.example            # copy to .env
└── app/
    ├── __init__.py         # app factory, CSRF check, error pages
    ├── database.py         # MongoDB connection + indexes
    ├── models/
    │   ├── user.py         # users collection
    │   └── form.py         # forms + responses collections
    ├── routes/
    │   ├── auth.py         # /register /login /logout
    │   ├── forms.py        # dashboard, builder, responses, JSON API
    │   └── public.py       # landing page, public form, submit
    ├── utils/
    │   ├── security.py     # password hashing, login_required, CSRF token
    │   └── validators.py   # form + answer validation
    ├── templates/          # Jinja HTML pages
    └── static/
        ├── css/style.css
        └── js/             # main.js, builder.js, dashboard.js, responses.js
```

## Setup

### 1. Install Python and configure MongoDB Atlas

- Python 3.9 or newer
- A MongoDB Atlas cluster and a database user with read/write access.
- In Atlas, allow your current IP address under **Network Access**.

### 2. Create a virtual environment and install packages

```bash
cd FormForge

# macOS / Linux
python3 -m venv venv
source venv/bin/activate

# Windows (PowerShell)
python -m venv venv
venv\Scripts\Activate.ps1

pip install -r requirements.txt
```

### 3. Configure Atlas

```bash
cp .env.example .env        # Windows: copy .env.example .env
```

Open `.env` and replace the `MONGO_URI` placeholders with the connection string
from your Atlas cluster (**Connect → Drivers**). Also set `SECRET_KEY` to a
long random string. Generate one with:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

If the database username or password contains characters such as `@`, `:`, `/`,
`#`, or `%`, URL-encode those credentials in the connection string. Keep `.env`
private and do not commit it.

### 4. Run

```bash
python run.py
```

Open http://127.0.0.1:5000, click **Sign up**, then **New form**.
The database and collections are created automatically on first use.

## Using the app

1. **Sign up**, then **New form**.
2. Type a title, write your questions, choose an answer type, and toggle **Required** where needed.
   Use the arrows to reorder. Press **Save form** (or Ctrl/Cmd+S).
3. After saving, copy the **Public link** and share it.
4. Open **Responses** to view answers. Use **Export CSV** to download them.
5. From the dashboard, **More → Stop accepting responses** closes a form, and **Delete form** removes it.

## Routes

| Method | URL | Purpose |
|---|---|---|
| GET | `/` | Landing page |
| GET/POST | `/register`, `/login` | Sign up, log in |
| POST | `/logout` | Log out |
| GET | `/dashboard` | Your forms |
| GET | `/forms/new`, `/forms/<id>/edit` | Builder |
| GET | `/forms/<id>/responses` | Responses table |
| GET | `/forms/<id>/responses/export.csv` | CSV export |
| POST | `/api/forms` | Create form (JSON) |
| PUT | `/api/forms/<id>` | Update form (JSON) |
| POST | `/api/forms/<id>/toggle` | Open / close form |
| DELETE | `/api/forms/<id>` | Delete form and its responses |
| DELETE | `/api/forms/<id>/responses/<rid>` | Delete one response |
| GET/POST | `/f/<public_id>` | Public form and submission |

## Database design

| Collection | Fields |
|---|---|
| `users` | `name`, `email` (unique), `password_hash`, `created_at` |
| `forms` | `owner_id`, `public_id` (unique), `title`, `description`, `questions[]` (`id`, `label`, `type`, `required`), `is_open`, `created_at`, `updated_at` |
| `responses` | `form_id`, `answers` (question id → value), `submitted_at` |

## Security notes

- Passwords: PBKDF2-SHA256 with a random salt (Werkzeug).
- Sessions: signed cookies, HttpOnly, SameSite=Lax. Set `SESSION_COOKIE_SECURE=1` when using HTTPS.
- CSRF token required for every logged-in POST/PUT/DELETE.
- Every query for forms and responses is scoped to the logged-in owner.
- Output is escaped by Jinja, and the CSV export neutralises spreadsheet formulas.
- The public form has a hidden honeypot field to catch simple bots.
- Not included: rate limiting and email verification. Add Flask-Limiter before a public launch.

## Troubleshooting

- **"MONGO_URI is not configured"**: set your Atlas connection string in `.env`.
- **"Could not connect to MongoDB Atlas"**: verify the connection string and
  database user credentials, and check Atlas **Network Access** for your IP.
- **Logged out after every restart**: set a fixed `SECRET_KEY` in `.env`.
- **Fonts look different**: the pages load Google Fonts, and fall back to system fonts offline.

## Deploying

```bash
pip install gunicorn
gunicorn "app:create_app()" --bind 0.0.0.0:8000
```

Set `FLASK_DEBUG=0`, a strong `SECRET_KEY`, `SESSION_COOKIE_SECURE=1`, and serve behind HTTPS.
