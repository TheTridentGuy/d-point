import datetime
from flask import Flask, render_template, request
from prisma import Prisma
from secrets import token_urlsafe
from enum import Enum


SYNC_KEY_BYTES = 16
SCORE_INTERVAL = datetime.timedelta(minutes=1)
SCORE_INTERVAL_ERROR = "You can only score once per minute."


class SyncState(Enum):
    SYNC_WAITING = 0
    SYNC_SYNCED = 1
    SYNC_LOST = 2


db = Prisma()
db.connect()
app = Flask(__name__)
state = SyncState.SYNC_WAITING
current_sync_key = token_urlsafe(SYNC_KEY_BYTES)
current_score_key = None


@app.route("/")
def index():
    users = db.user.find_many(order={
        "score": "desc"
    })
    return render_template("index.html", sync_state=state.name, sync_key=current_sync_key if state == SyncState.SYNC_WAITING else None, users=users)


@app.route("/sync")
def sync():
    global current_score_key, current_sync_key, state
    score_key = request.values.get("score_key")
    sync_key = request.values.get("sync_key")
    if state == SyncState.SYNC_WAITING:
        score_key = request.values.get("score_key")
        if not score_key:
            return "You must provide a score_key URL parameter!", 400
        else:
            current_score_key = score_key
            state = SyncState.SYNC_SYNCED
            return current_sync_key
    elif state == SyncState.SYNC_SYNCED:
        if score_key and sync_key == current_sync_key:
            current_score_key = score_key
            current_sync_key = token_urlsafe(SYNC_KEY_BYTES)
            return current_sync_key
        else:
            state = SyncState.SYNC_LOST
            return "You must provide a score_key URL parameter, and a valid sync_key URL parameter. Sync lost, restart the server to continue.", 400
    else:
        assert state == SyncState.SYNC_LOST
        return "Sync lost, restart the server to continue.", 422

@app.route("/score")
def score():
    score_key = request.values.get("score_key")
    username = request.values.get("username")
    if not username:
        return "You must provide a username parameter", 400
    else:
        username = username[:32]
    if username and score_key == current_score_key:
        user = db.user.find_unique(where={
            "username": username
        })
        if user:
            if user.last_score < (datetime.datetime.now().astimezone(None) - SCORE_INTERVAL):
                db.user.update(where={
                    "username": username
                }, data={
                    "score": user.score + 1
                })
            else:
                return SCORE_INTERVAL_ERROR, 429
        else:
            user = db.user.create(data={
                "username": username,
                "score": 1
            })
        return str(user.score)
    else:
        return "You must provide a username parameter a valid score_key parameter.", 400
