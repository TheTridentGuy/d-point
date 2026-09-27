import base64
import hmac
import os
import re
import subprocess
from datetime import datetime, timezone, timedelta
from secrets import token_bytes

import dotenv
from flask import Flask, render_template, request

dotenv.load_dotenv()
NONCE_BYTES = 16
NONCE_LIFESPAN = timedelta(minutes=5, seconds=10)
SCORE_INTERVAL = timedelta(minutes=5, seconds=10)
LEADERBOARD_INTERVAL = timedelta(days=3)
OATH_SECRET = base64.b32decode(os.environ["OATH_SECRET_B32"])

subprocess.run(["prisma", "db", "push"], check=True)
from prisma import Prisma

db = Prisma()
db.connect()
app = Flask(__name__)
nonce_hmacs_expirations = {}
utc_now = lambda: datetime.now(timezone.utc)


def clean_nonce_hmacs_expirations(now):
    keys_to_be_deleted = []
    for nonce_hmac, expiration in nonce_hmacs_expirations.items():
        if expiration < now:
            keys_to_be_deleted.append(nonce_hmac)
    for key in keys_to_be_deleted:
        del nonce_hmacs_expirations[key]


@app.route("/")
def index():
    now = utc_now()
    timedeltas_users = []
    active_usernames = []
    users = db.user.find_many(
        include={"captures": {"where": {"end": {"gt": now - LEADERBOARD_INTERVAL}}, "orderBy": {"end": "desc"}}})
    for user in users:
        timedeltas_users.append(
            (sum([capture.end - max(capture.start, now - LEADERBOARD_INTERVAL) for capture in user.captures],
                 timedelta()), user))
        if len(user.captures) > 0 and now - user.captures[0].end < SCORE_INTERVAL:
            active_usernames.append(user.username)
    timedeltas_users.sort(key=lambda x: x[0].total_seconds(), reverse=True)
    return render_template("index.html", timedeltas_users=timedeltas_users, active_usernames=active_usernames)


@app.route("/capture")
def capture():
    now = utc_now()
    username = request.values.get("username")
    alleged_hmac = request.values.get("hmac")
    if not username:
        return "You must provide a username URL parameter.\n", 400
    matched_username = re.match(r"[a-zA-Z\d._-]{1,32}", username)
    if not matched_username or not matched_username.group() == username:
        return "Your username can only include alphanumeric characters, underscores, hyphens, and periods. It can be a maximum of 32 characters long.\n", 400
    if not alleged_hmac:
        return "You must provide a hmac URL parameter, with a valid HMAC of a recent nonce.\n", 400
    try:
        alleged_hmac = bytes.fromhex(alleged_hmac)
    except ValueError:
        return "Unable to decode hmac url parameter. It should be bytes in hexadecimal string format.\n", 400
    clean_nonce_hmacs_expirations(now)
    if not nonce_hmacs_expirations.get(alleged_hmac):
        return "Expired or invalid hmac url parameter.\n", 503
    user = db.user.find_unique(where={"username": username}, include={"captures": {"where": {"completed": False}}})
    if user:
        assert len(user.captures) <= 1
        if len(user.captures) == 1:
            capture = user.captures[0]
            if now - capture.end < SCORE_INTERVAL:
                db.capture.update(where={"id": capture.id}, data={"end": now})
                return "", 200
            else:
                db.capture.update(where={"id": capture.id}, data={"completed": True})
        db.capture.create(data={"username": username})
        return "", 200
    db.user.create(data={"username": username})
    return "", 200


@app.route("/nonce")
def nonce():
    now = utc_now()
    clean_nonce_hmacs_expirations(now)
    nonce = token_bytes(NONCE_BYTES)
    nonce_hmac = hmac.digest(OATH_SECRET, nonce, "sha256")
    nonce_hmacs_expirations[nonce_hmac] = now + NONCE_LIFESPAN
    return nonce.hex()


@app.route("/user/<username>")
def user(username):
    user = db.user.find_unique(where={"username": username}, include={"captures": {"orderBy": {"end": "desc"}}})
    if not user:
        return "User does not exist.", 404
    return f"User page for {user.username} coming soon."
