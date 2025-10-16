from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import json, os

app = Flask(__name__)
app.secret_key = 'your_secret_key'

USER_FILE = 'users.json'
CLASS_FILE = 'class.json'
ATTENDANCE_FILE = 'attendance.json'
ACTIVITIES_FILE = 'activities.json'

def load_users():
    if os.path.exists(USER_FILE):
        with open(USER_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USER_FILE, 'w') as f:
        json.dump(users, f, indent=4)

# load users once at startup (file may be added/edited later if you implement registration)
users = load_users()


def get_current_user():
    username = session.get('username')
    if not username:
        return None
    return users.get(username)


def current_role():
    u = get_current_user()
    if not u:
        return None
    return u.get('role', 'student')


def load_json(path, default=None):
    if default is None:
        default = {}
    if os.path.exists(path):
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return default
    return default


def save_json(path, data):
    with open(path, 'w') as f:
        json.dump(data, f, indent=4)

@app.route('/', methods=['GET', 'POST'])
def start():
    if request.method == 'POST':
        # use .get to avoid KeyError if the form is malformed
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        
        if username in users and check_password_hash(users[username]['password'], password):
            session['username'] = username
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials')
    if 'username' in session:
        return redirect(url_for('dashboard'))
    return render_template('start.html')


@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('start'))

    username = session.get('username')
    all_classes = load_json(CLASS_FILE, default=[])
    
    # Filter classes to get only those taught by this teacher
    teacher_classes = [c for c in all_classes if c['teacher'] == username]

    # If teacher_classes is empty, you could show a message or default class
    if not teacher_classes:
        teacher_classes = [{
            'class_name': 'No class assigned',
            'teacher': username,
            'representative': 'N/A',
            'students': []
        }]

    # Pass only the teacher's class(es)
    return render_template('dashboard.html', username=username, classes=teacher_classes, role=current_role())

@app.route('/class', methods=['GET', 'POST'])
def class_info():
    if 'username' not in session:
        return redirect(url_for('start'))
    data = load_json(CLASS_FILE, default={'class_name':'Class 1','teacher':'Mr. Smith','representative':'Not assigned','students':[]})
    if request.method == 'POST':
        # only teachers may update class info
        if current_role() != 'teacher':
            flash('Permission denied: only teachers can update class information')
            return redirect(url_for('class_info'))
        data['class_name'] = request.form.get('class_name', data.get('class_name'))
        data['teacher'] = request.form.get('teacher', data.get('teacher'))
        data['representative'] = request.form.get('representative', data.get('representative'))
        # students list expected as newline-separated
        students_raw = request.form.get('students', '')
        if students_raw:
            students = [s.strip() for s in students_raw.split('\n') if s.strip()]
            data['students'] = students
        save_json(CLASS_FILE, data)
        flash('Class information updated')
        return redirect(url_for('class_info'))
    # prepare students as textarea content
    students_text = '\n'.join(data.get('students', []))
    return render_template('class_info.html', data=data, students_text=students_text, role=current_role())


@app.route('/attendance', methods=['GET', 'POST'])
def attendance():
    if 'username' not in session:
        return redirect(url_for('start'))
    class_data = load_json(CLASS_FILE, default={ 'students': [] })
    attendance_data = load_json(ATTENDANCE_FILE, default={})
    date = request.args.get('date') or request.form.get('date') or None
    if request.method == 'POST':
        # only teachers may save attendance
        if current_role() != 'teacher':
            flash('Permission denied: only teachers can save attendance')
            return redirect(url_for('attendance'))
        date = request.form.get('date')
        # collect attendance for each student
        records = {}
        for s in class_data.get('students',[]):
            val = request.form.get(f'student_{s}', 'absent')
            records[s] = val
        attendance_data[date] = records
        save_json(ATTENDANCE_FILE, attendance_data)
        flash('Attendance saved for ' + date)
        return redirect(url_for('attendance'))
    # view attendance for selected date
    selected = attendance_data.get(date, {}) if date else {}
    return render_template('attendance.html', students=class_data.get('students',[]), date=date, records=selected, all_records=attendance_data, role=current_role())


@app.route('/activities', methods=['GET', 'POST'])
def activities():
    if 'username' not in session:
        return redirect(url_for('start'))
    activities_data = load_json(ACTIVITIES_FILE, default={})
    if request.method == 'POST':
        # only teachers may update activities
        if current_role() != 'teacher':
            flash('Permission denied: only teachers can update activities')
            return redirect(url_for('activities'))
        date = request.form.get('date')
        notes = request.form.get('notes','')
        activities_data[date] = notes
        save_json(ACTIVITIES_FILE, activities_data)
        flash('Activities updated for ' + date)
        return redirect(url_for('activities'))
    return render_template('activities.html', activities=activities_data, role=current_role())

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('start'))   

if __name__ == '__main__':
    app.run(debug=True)
