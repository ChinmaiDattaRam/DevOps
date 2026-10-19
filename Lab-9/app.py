import os

from flask import Flask

app = Flask(__name__)


@app.route("/")
def home():
    return "Hello, Jenkins Multi-Stage Pipeline!"


if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        debug=True,
        port=int(os.environ.get("PORT", "5000")),
        use_reloader=False,
    )
