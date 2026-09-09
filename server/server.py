from flask import Flask, render_template, request
from secrets import token_urlsafe
from enum import Enum


SYNC_KEY_BYTES = 16


class SyncState(Enum):
    SYNC_WAITING = 0
    SYNC_SYNCED = 1
    SYNC_LOST = 2


app = Flask(__name__)
state = SyncState.SYNC_WAITING
current_sync_key = token_urlsafe(SYNC_KEY_BYTES)
current_score_key = None
scores = {}


@app.route("/")
def index():
    return render_template("index.html", sync_state=state.name, sync_key=current_sync_key if state == SyncState.SYNC_WAITING else None)


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
            return current_sync_key, 200
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
        return "Sync lost, restart the server to continue."

@app.route("/score")
def score():
    pass
