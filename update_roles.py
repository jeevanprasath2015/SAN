"""
Update roles in users.json based on class.json.
- Students listed in class.json -> role 'student'
- The teacher name in class.json -> converted to a username (lowercase, underscores) and role 'teacher'

If a user does not exist, create them with a generated password and print the credentials.
"""
import json
import os
import re
import secrets
from werkzeug.security import generate_password_hash

ROOT = os.path.dirname(__file__)
USERS_FILE = os.path.join(ROOT, 'users.json')
CLASS_FILE = os.path.join(ROOT, 'class.json')


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


def normalize_username(name):
    # convert to lowercase, remove titles like Mr./Ms., replace non-alnum with underscore
    name = name.strip()
    # remove common honorifics
    name = re.sub(r'(?i)^(mr|mrs|ms|dr)\.\s*', '', name)
    name = re.sub(r'[^0-9a-zA-Z]+', '_', name)
    name = name.strip('_').lower()
    if not name:
        name = 'user'
    return name


def main():
    users = load_json(USERS_FILE, default={})
    class_data = load_json(CLASS_FILE, default={})

    created = []

    # Ensure students have role 'student'
    for s in class_data.get('students', []):
        if s in users:
            users[s]['role'] = 'student'
        else:
            pwd = secrets.token_urlsafe(6)
            users[s] = {
                'password': generate_password_hash(pwd),
                'role': 'student'
            }
            created.append((s, pwd, 'student'))

    # Representative may be a student name; try to set role if present
    rep = class_data.get('representative')
    if rep:
        rep_username = rep
        if rep_username in users:
            users[rep_username]['role'] = users[rep_username].get('role', 'student')

    # Teacher: convert name to username and ensure role 'teacher'
    teacher_name = class_data.get('teacher')
    if teacher_name:
        teacher_username = normalize_username(teacher_name)
        # if teacher name already matches an existing username, prefer that
        if teacher_name in users:
            users[teacher_name]['role'] = 'teacher'
        else:
            if teacher_username in users:
                users[teacher_username]['role'] = 'teacher'
            else:
                pwd = secrets.token_urlsafe(8)
                users[teacher_username] = {
                    'password': generate_password_hash(pwd),
                    'role': 'teacher'
                }
                created.append((teacher_username, pwd, 'teacher'))

    save_json(USERS_FILE, users)

    if created:
        print('Created the following accounts (change their passwords as needed):')
        for u, p, r in created:
            print(f" - {u} ({r}) password: {p}")
    else:
        print('No new accounts were created. Roles updated.')


if __name__ == '__main__':
    main()
