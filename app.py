from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import matplotlib.pyplot as plt
from io import BytesIO
import base64

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///fitness_tracker.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key'
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False, unique=True)
    email = db.Column(db.String(150), nullable=False, unique=True)
    password = db.Column(db.String(150), nullable=False)

class Workout(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), db.ForeignKey('user.username'), nullable=False)
    date = db.Column(db.String(10), nullable=False)
    exercise = db.Column(db.String(150), nullable=False)
    kilograms = db.Column(db.Integer, nullable=False)
    sets = db.Column(db.Integer, nullable=False)
    reps = db.Column(db.Integer, nullable=False)

@app.route('/')
def login():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def do_login():
    username = request.form['username']
    password = request.form['password']
    user = User.query.filter_by(username=username, password=password).first()
    if user:
        session['username'] = username
        return redirect(url_for('main', username=username))
    return redirect(url_for('login'))

@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/register', methods=['POST'])
def do_register():
    username = request.form['username']
    email = request.form['email']
    password = request.form['password']
    new_user = User(username=username, email=email, password=password)
    db.session.add(new_user)
    db.session.commit()
    return redirect(url_for('login'))

@app.route('/main')
def main():
    username = session.get('username')
    user = User.query.filter_by(username=username).first()
    return render_template('main.html', user=user)

@app.route('/add_workout')
def add_workout():
    username = session.get('username')
    user = User.query.filter_by(username=username).first()
    return render_template('add_workout.html', user=user)

@app.route('/add_workout', methods=['POST'])
def do_add_workout():
    username = session.get('username')
    date = request.form['date']
    exercises = request.form.getlist('exercise[]')
    kilograms = request.form.getlist('kilograms[]')
    sets = request.form.getlist('sets[]')
    reps = request.form.getlist('reps[]')
    
    for i in range(len(exercises)):
        exercise = exercises[i]
        kilo = kilograms[i] if kilograms[i] else None
        set_num = sets[i] if sets[i] else None
        rep_num = reps[i] if reps[i] else None

        new_workout = Workout(username=username, date=date, exercise=exercise, kilograms=kilo, sets=set_num, reps=rep_num)
        db.session.add(new_workout)
    
    db.session.commit()
    return redirect(url_for('history', username=username))

@app.route('/history')
def history():
    username = session.get('username')
    user = User.query.filter_by(username=username).first()
    user_activities = Workout.query.filter_by(username=username).all()
    
    activities_dict = {}
    for activity in user_activities:
        formatted_date = datetime.strptime(activity.date, '%Y-%m-%d').strftime('%d %B %Y')
        if formatted_date not in activities_dict:
            activities_dict[formatted_date] = []
        activities_dict[formatted_date].append(activity)

    return render_template('history.html', user=user, activities=activities_dict)

@app.route('/account')
def account():
    username = session.get('username')
    user = User.query.filter_by(username=username).first()
    return render_template('account.html', user=user)

@app.route('/recommended_training')
def recommended_training():
    username = session.get('username')
    user = User.query.filter_by(username=username).first()
    return render_template('recommended_training.html', user=user)

@app.route('/view_progress')
def view_progress():
    username = session.get('username')
    user = User.query.filter_by(username=username).first()
    exercises = db.session.query(Workout.exercise).filter_by(username=username).distinct().all()
    exercises = [exercise[0] for exercise in exercises]
    return render_template('view_progress.html', user=user, exercises=exercises)

@app.route('/exercise_progress/<exercise>')
def exercise_progress(exercise):
    username = session.get('username')
    user = User.query.filter_by(username=username).first()
    exercise_data = Workout.query.filter_by(username=username, exercise=exercise).all()
  
    dates = [datetime.strptime(data.date, '%Y-%m-%d') for data in exercise_data]
    progress = [data.kilograms for data in exercise_data]

    plt.figure(figsize=(10, 6))
    plt.plot(dates, progress)
    plt.xlabel('Date')
    plt.ylabel('Progress (Kilograms)')
    plt.title(f'{exercise} Progress')
    plt.grid(True)
    
    buffer = BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    plot_data = base64.b64encode(buffer.getvalue()).decode('utf-8')

    return render_template('exercise_progress.html', user=user, exercise=exercise, plot_data=plot_data)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5500)