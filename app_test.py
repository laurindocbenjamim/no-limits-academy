from flask import Flask, render_template, redirect, url_for, request, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_migrate import Migrate
from app.configs import db
import sqlalchemy
from datetime import datetime
from datetime import timezone

from flask_migrate import Migrate
from app.models import User, TokenBlocklist
from app import create_app
#from app.models import User
from werkzeug.security import generate_password_hash
#app = Flask(__name__)
#app.config['SECRET_KEY'] = 'your_secret_key'
#app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
#db = SQLAlchemy()

app = create_app()

class User(db.Model):
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            return redirect(url_for('dashboard'))
        return 'Invalid credentials'
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password, method='sha256')
        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' in session:
        return 'Welcome to your dashboard!'
    return redirect(url_for('login'))

Migrate(app=app,db=db)
db.init_app(app=app)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)