from flask import Flask, render_template, request, flash, redirect, url_for, session
import pyodbc
import bcrypt

app = Flask(__name__)
app.secret_key = "your_secret_key"  # Required for session and flashing messages

# Configure database connection
def get_db_connection():
    conn = pyodbc.connect(
        "DRIVER={ODBC Driver 17 for SQL Server};"
        "SERVER=88.222.244.120;"
        "DATABASE=LoginDBR;"
        "UID=ams;"
        "PWD=pC6p[Pb84et0"
    )
    return conn

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/register', methods=['POST'])
def register():
    first_name = request.form['first_name']
    last_name = request.form['last_name']
    email = request.form['email']
    password = request.form['password']
    confirm_password = request.form['confirm_password']

    if password != confirm_password:
        flash("Passwords do not match!", "error")
        return redirect(url_for('home'))

    try:
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if email already exists
        cursor.execute("SELECT COUNT(*) FROM Users WHERE Email = ?", email)
        email_count = cursor.fetchone()[0]

        if email_count > 0:
            flash("Email already exists!", "error")
            return redirect(url_for('home'))

        # Insert data into the database
        cursor.execute("""
            INSERT INTO Users (FirstName, LastName, Email, Password)
            VALUES (?, ?, ?, ?)""",
            first_name, last_name, email, hashed_password.decode('utf-8'))
        conn.commit()

        flash("Registration successful! Please log in.", "success")
        return redirect(url_for('login'))
    except Exception as e:
        flash(f"An error occurred: {e}", "error")
        return redirect(url_for('home'))
    finally:
        conn.close()

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Fetch user by email
            cursor.execute("SELECT Password FROM Users WHERE Email = ?", email)
            result = cursor.fetchone()

            if result and bcrypt.checkpw(password.encode('utf-8'), result[0].encode('utf-8')):
                session['user'] = email  # Store user email in session
                flash("Login successful!", "success")
                return redirect(url_for('test'))
            else:
                flash("Invalid email or password!", "error")
        except Exception as e:
            flash(f"An error occurred: {e}", "error")
        finally:
            conn.close()

    return render_template('login.html')

@app.route('/test', methods=['GET', 'POST'])
def test():
    if 'user' not in session:
        flash("You need to log in first!", "error")
        return redirect(url_for('login'))

    if request.method == 'POST':
        # Retrieve user's selected answers
        selected_answers = {
            'question1': request.form.get('question1', ''),
            'question2': request.form.get('question2', ''),
            'question3': request.form.get('question3', ''),
            'question4': request.form.get('question4', '')
        }

        # Correct answers
        correct_answers = {
            'question1': '15',
            'question2': 'Jupiter',
            'question3': '9',
            'question4': 'Paris'
        }

        # Calculate score
        score = 0
        for key, correct_answer in correct_answers.items():
            if selected_answers.get(key, '').lower() == correct_answer.lower():
                score += 1

        # Store results in session
        session['test_results'] = {
            'score': score,
            'total_questions': len(correct_answers),
            'selected_answers': selected_answers
        }

        flash(f"Test completed! You scored {score}/{len(correct_answers)}.", "success")
        return redirect(url_for('results'))

    return render_template('test.html')

@app.route('/results', methods=['GET'])
def results():
    if 'user' not in session or 'test_results' not in session:
        flash("You need to log in and take the test first!", "error")
        return redirect(url_for('login'))

    # Retrieve results from session
    test_results = session.get('test_results', {})
    return render_template('results.html', results=test_results)

if __name__ == "__main__":
    app.run(debug=True)
