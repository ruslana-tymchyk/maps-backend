from flask import Flask

app = Flask(__name__)
app.config["DEBUG"] = True  # Enables automatic reloading

@app.route("/")
def hello_world():
    return "<p>Ori loves Lana!</p>"