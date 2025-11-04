
from flask import request, jsonify, Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class UserInput(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80))
    email = db.Column(db.String(80))
    ingredients = db.Column(db.Text)



app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///Izzie-Nielsen/forkcast.db'
db.init_app(app)


@app.route("/submit", methods=["POST"])
def submit():
    data = request.get_json()
    new_entry = UserInput(
        name=data.get("name"),
        email=data.get("email"),
        ingredients=data.get("ingredients")
    )
    db.session.add(new_entry)
    db.session.commit()
    return jsonify({"status": "success", "id": new_entry.id})

