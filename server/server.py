import os
import dotenv
from flask import Flask, render_template
from prisma import Prisma
from secrets import token_urlsafe


dotenv.load_dotenv()
NONCE_BYTES = 16
OATH_SECRET = os.environ["OATH_SECRET"]


db = Prisma()
db.connect()
app = Flask(__name__)
current_nonce = token_urlsafe(NONCE_BYTES)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/capture")
def capture():
    pass


@app.route("/nonce")
def nonce():
    return current_nonce
