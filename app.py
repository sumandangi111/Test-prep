# app.py
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from data import QUIZ_DATA  # Used only for initial database population
import random
from functools import wraps
from datetime import datetime

app = Flask(__name__)
# Configuration for SQLAlchemy (SQLite database)
app.config['SECRET_KEY'] = 'your_super_secret_key_12345' 
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- Database Models ---

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    topic = db.Column(db.String(100), nullable=False)
    question_text = db.Column(db.String(500), nullable=False)
    
    option_a = db.Column(db.String(200), nullable=False)
    option_b = db.Column(db.String(200), nullable=False)
    option_c = db.Column(db.String(200), nullable=False)
    option_d = db.Column(db.String(200), nullable=False)
    
    correct_answer = db.Column(db.String(200), nullable=False)

    def get_options(self):
        """Returns options as a list for easy shuffling/display."""
        return [self.option_a, self.option_b, self.option_c, self.option_d]

    def __repr__(self):
        return f'<Question {self.topic}: {self.question_text[:30]}...>'

class Score(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    topic = db.Column(db.String(100), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    total_questions = db.Column(db.Integer, nullable=False)
    date_recorded = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship to easily access the user object (optional but helpful)
    user = db.relationship('User', backref=db.backref('scores', lazy=True))

    def __repr__(self):
        return f'<Score {self.user_id} - {self.topic}: {self.score}/{self.total_questions}>'
    
# --- Initialization Function for Dummy Data ---
def initialize_database_with_questions():
    """Checks if questions exist, and if not, populates the database."""
    if Question.query.count() == 0:
        
        # QUIZ_DATA imported from data.py
        
        new_questions = []
        for topic, questions_list in QUIZ_DATA.items():
            for q_data in questions_list:
                # Assuming options are always 4 and in order A, B, C, D
                if len(q_data['options']) != 4: continue 
                
                q = Question(
                    topic=topic,
                    question_text=q_data['question'],
                    option_a=q_data['options'][0],
                    option_b=q_data['options'][1],
                    option_c=q_data['options'][2],
                    option_d=q_data['options'][3],
                    correct_answer=q_data['answer']
                )
                new_questions.append(q)
        
        db.session.add_all(new_questions)
        db.session.commit()
        print("Database populated with initial quiz questions.")

# --- Context Processor (Makes login status available everywhere) ---
@app.context_processor
def inject_user():
    return dict(logged_in=session.get('logged_in'), current_user=session.get('username'))

# --- Authentication Routes ---

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if session.get('logged_in'):
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        if User.query.filter_by(username=username).first():
            flash('Username already exists. Please choose a different one.', 'danger')
            return redirect(url_for('signup'))
        if User.query.filter_by(email=email).first():
            flash('Email address already registered.', 'danger')
            return redirect(url_for('signup'))
        
        new_user = User(username=username, email=email)
        new_user.set_password(password)
        
        db.session.add(new_user)
        db.session.commit()

        flash('Account created successfully! Please log in.', 'success')
        return redirect(url_for('login'))
        
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('logged_in'):
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            session['logged_in'] = True
            session['user_id'] = user.id
            session['username'] = user.username
            flash('Logged in successfully.', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password.', 'danger')
            return redirect(url_for('login'))
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('user_id', None)
    session.pop('username', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))


# --- Main Dashboard & Quiz Routes ---

@app.route('/')
def index():
    """Requires login to see the quiz selection dashboard. Topics loaded from DB."""
    if not session.get('logged_in'):
        flash('Please log in or sign up to access the quiz dashboard.', 'info')
        return redirect(url_for('login'))

    # Fetch unique topics from the database
    topics = db.session.query(Question.topic).distinct().all()
    topic_list = [t[0] for t in topics] 

    return render_template('index.html', topics=topic_list)

@app.route('/start_quiz', methods=['POST'])
def start_quiz():
    """Logic to start the quiz, fetching random questions from DB."""
    if not session.get('logged_in'):
        flash('Please log in to start a quiz.', 'warning')
        return redirect(url_for('login'))
    MAX_QUIZ_SIZE=50
    
    topic = request.form.get('topic')
    try:
        num_questions = int(request.form.get('num_questions'))
    except (ValueError, TypeError):
        return "Invalid number of questions selected.", 400
    if num_questions > MAX_QUIZ_SIZE:
        num_questions = MAX_QUIZ_SIZE 
        flash(f"Quiz size limited to maximum of {MAX_QUIZ_SIZE} questions.", 'warning')
    # Fetch questions from the database, ordered randomly, limited by count
    all_questions = Question.query.filter_by(topic=topic).order_by(db.func.random()).limit(num_questions).all()
    
    if not all_questions:
        flash("Topic not found or no questions available.", 'danger')
        return redirect(url_for('index'))

    # Convert SQLAlchemy objects into a session-friendly list of dictionaries
    selected_questions_for_session = []
    for q_obj in all_questions:
        selected_questions_for_session.append({
            'id': q_obj.id,
            'question': q_obj.question_text,
            'options': q_obj.get_options(),
            'answer': q_obj.correct_answer
        })

    # Store quiz state in session
    session['quiz_questions'] = selected_questions_for_session
    session['current_question_index'] = 0
    session['score'] = 0
    session['total_questions'] = len(selected_questions_for_session)
    session['current_quiz_topic'] = topic 

    return redirect(url_for('quiz'))

@app.route('/quiz')
def quiz():
    """Displays the current question."""
    if not session.get('logged_in') or 'quiz_questions' not in session:
        return redirect(url_for('index'))

    questions = session['quiz_questions']
    current_index = session.get('current_question_index', 0)

    if current_index >= len(questions):
        return redirect(url_for('results'))

    current_question = questions[current_index]
    
    # Shuffle options before sending to template
    options_shuffled = current_question['options'][:]
    random.shuffle(options_shuffled) 
    current_question['options_shuffled'] = options_shuffled

    return render_template(
        'quiz.html', 
        question=current_question, 
        q_num=current_index + 1,
        total_q=session['total_questions']
    )

# app.py (in submit_answer route)
@app.route('/submit_answer', methods=['POST'])
def submit_answer():
    if not session.get('logged_in') or 'quiz_questions' not in session:
        return jsonify({'redirect': url_for('index')})
        
    user_answer = request.form.get('answer')
    questions = session['quiz_questions']
    current_index = session['current_question_index']

    correct_answer = questions[current_index]['answer']
    is_correct = (user_answer == correct_answer)

    if current_index < len(questions):
        if is_correct:
            session['score'] += 1
        
        # NOTE: DO NOT increment the index yet. We wait for the JS redirect.
        
        # Return feedback data to the frontend
        return jsonify({
            'is_correct': is_correct,
            'correct_answer_text': correct_answer,
            'user_answer_text': user_answer,
            'quiz_over': (current_index + 1 >= len(questions))
        })
    
    # Should not happen if index check is correct, but handles overflow
    return jsonify({'redirect': url_for('results')})
# app.py (in results route)

@app.route('/results')
def results():
    score = session.get('score', 0)
    total = session.get('total_questions', 0)
    user_id = session.get('user_id')
    quiz_topic = session.get('current_quiz_topic') # Fetch the topic

    if total == 0 or not user_id:
        # Prevent recording score if no quiz was actually taken or user not logged in
        return redirect(url_for('index'))
    
    # --- NEW: Save the Score to the Database ---
    new_score = Score(
        user_id=user_id,
        topic=quiz_topic,
        score=score,
        total_questions=total
    )
    db.session.add(new_score)
    db.session.commit()
    # ------------------------------------------

    # Clear quiz session data
    session.pop('quiz_questions', None)
    session.pop('current_question_index', None)
    session.pop('total_questions', None)
    session.pop('score', None)
    session.pop('current_quiz_topic', None) # Clear the topic too

    return render_template('results.html', score=score, total=total)

# app.py (New History Route)
@app.route('/history')
def history():
    if not session.get('logged_in'):
        flash('Please log in to view your history.', 'warning')
        return redirect(url_for('login'))
        
    user_id = session.get('user_id')
    
    # Fetch all scores for the current user, ordered by date (newest first)
    past_scores = Score.query.filter_by(user_id=user_id).order_by(Score.date_recorded.desc()).all()
    
    return render_template('history.html', scores=past_scores)

# app.py (New Advancement Route to be added)

# --- NEW: Handles advancing to the next question after feedback timeout ---
@app.route('/advance_question', methods=['POST'])
def advance_question():
    """Increments the question index and redirects to the next question or results."""
    # Check if quiz state exists in session
    if 'quiz_questions' not in session:
        # If session is invalid, redirect to the dashboard (via JSON)
        return jsonify({'redirect': url_for('index')})
        
    questions = session['quiz_questions']
    
    # Increment the question index
    session['current_question_index'] += 1
    
    # Check if the quiz is over
    if session['current_question_index'] >= len(questions):
        # Redirect to results page
        return jsonify({'redirect': url_for('results')})
    else:
        # Redirect to the next question page
        return jsonify({'redirect': url_for('quiz')})
if __name__ == '__main__':
    # Initialize the database tables and populate with questions on startup
    with app.app_context():
        db.create_all()
        initialize_database_with_questions()
    
    app.run(debug=True)