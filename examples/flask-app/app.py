import sys
sys.path.append("..") # the sys import isn't necessary outside of my testing
import destipy
from flask import Flask, request, render_template, redirect, url_for, abort


app = Flask(__name__)


@app.route('/')
def index():
    return render_template("index.html")

@app.route('/api/<platform>/<username>')
def api(platform, username):
    api_user = destipy.DestinyAccount(platform, username)
    return render_template("api.html", api_user=api_user)

if __name__ == '__main__':
    app.run(debug=True)