import os
import re
import dotenv
import base64
from flask import Flask, render_template, request
from prisma import Prisma
from datetime import datetime, timezone, timedelta
from secrets import token_bytes

dotenv.load_dotenv()
NONCE_BYTES = 16
OATH_SECRET = base64.b32decode(os.environ["OATH_SECRET_B32"])


db = Prisma()
db.connect()
app = Flask(__name__)
current_nonce = token_bytes(NONCE_BYTES).hex()


@app.route("/")
def index():
    timedelta_users = []
    users = db.user.find_many(include={"captures": True})
    for user in users:
        timedelta_users.append((sum([capture.start - capture.end for capture in user.captures]), user))
    timedelta_users.sort(key=lambda x: x[0].total_seconds(), reverse=True)
    return render_template("index.html", timedelta_user=timedelta_users)


@app.route("/capture")
def capture():
    username = request.values.get("username")
    response = request.values.get("hmac")
    if not username:
        return "You must provide a username URL parameter.", 400
    if not response:
        return "You must provide a hmac URL parameter, with a valid HMAC of a recent nonce."
    if not re.match(r"[a-zA-Z\d._-]{1,32}", username) == username:
        return "Your username can only include alphanumeric characters, underscores, hyphens, and periods. It can be a maximum of 32 characters long.", 400
    user = db.user.find_unique(where={"username": username}, include={"captures": {"where": {"completed": False}}})
    if user:
        assert len(user.captures) <= 1
        if len(user.captures) == 1:
            capture = user.captures[0]
            if datetime.now(timezone.utc) - capture.end < timedelta(minutes=1):
                db.capture.update(where={"id": capture.id}, data={"end": datetime.now(timezone.utc)})
                return "", 200
            else:
                db.capture.update(where={"id": capture.id}, data={"completed": True})
                db.capture.create(data={"username": username})
                return "", 200
    db.user.create(data={"username": username})
    return "", 200


@app.route("/nonce")
def nonce():
    return current_nonce
