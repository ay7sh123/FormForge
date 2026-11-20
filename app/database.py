from pymongo import ASCENDING, DESCENDING, MongoClient
from pymongo.errors import PyMongoError

_client = None
_db = None


def init_db(app):
    """Connect to MongoDB and make sure the indexes exist."""
    global _client, _db
    uri = app.config["MONGO_URI"]
    if not uri:
        raise RuntimeError(
            "MONGO_URI is not configured. Set it in your .env file to your "
            "MongoDB Atlas connection string."
        )

    try:
        _client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        _client.admin.command("ping")
    except PyMongoError as exc:
        raise RuntimeError(
            "Could not connect to MongoDB Atlas. Check MONGO_URI, confirm "
            "your Atlas database user credentials, and allow your IP address "
            "in the Atlas Network Access settings."
        ) from exc

    _db = _client[app.config["MONGO_DB_NAME"]]
    _db["users"].create_index("email", unique=True)
    _db["forms"].create_index("public_id", unique=True)
    _db["forms"].create_index([("owner_id", ASCENDING), ("created_at", DESCENDING)])
    _db["responses"].create_index([("form_id", ASCENDING), ("submitted_at", DESCENDING)])


def get_db():
    return _db
