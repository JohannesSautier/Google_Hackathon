# minimal HTTP app for Cloud Run
from flask import Flask

app = Flask(__name__)

@app.get("/")
def index():
    return "Hello from Cloud Run 👋"

if __name__ == "__main__":
    # local dev only
    app.run(host="0.0.0.0", port=8080)
