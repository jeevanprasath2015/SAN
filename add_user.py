"""
Small CLI helper to add a user to users.json with a hashed password.
Usage:
  python add_user.py --username alice --password secret
or:
  python add_user.py --username alice    # you'll be prompted for the password

This script uses werkzeug.security.generate_password_hash to store the password safely.
"""
import argparse
import json
import os
import sys
from getpass import getpass

try:
    from werkzeug.security import generate_password_hash
except Exception as e:
    print("Error: werkzeug is not installed or could not be imported.")
    print("Install with: pip install werkzeug")
    raise

USERS_FILE = os.path.join(os.path.dirname(__file__), 'users.json')


def load_users():
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, 'r') as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return data
                else:
                    print("Warning: users.json content is not a dict. Reinitializing.")
        except json.JSONDecodeError:
            print("Warning: users.json is empty or malformed. Reinitializing.")
    return {}


def save_users(users):
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=4)


def main():
    parser = argparse.ArgumentParser(description='Add a user to users.json')
    parser.add_argument('--username', '-u', required=True, help='Username to add')
    parser.add_argument('--password', '-p', help='Password (if omitted you will be prompted)')
    parser.add_argument('--role', '-r', choices=['student', 'teacher'], default='student', help='Role for the user (student or teacher)')
    args = parser.parse_args()

    username = args.username.strip()
    if not username:
        print('Username cannot be empty')
        sys.exit(1)

    password = args.password
    if not password:
        try:
            password = getpass('Password: ')
        except Exception:
            # fallback
            password = input('Password: ')

    if not password:
        print('Password cannot be empty')
        sys.exit(1)

    users = load_users()
    if username in users:
        print(f"User '{username}' already exists. Overwrite? (y/N)", end=' ')
        ans = input().strip().lower()
        if ans != 'y':
            print('Aborting.')
            sys.exit(0)

    hashed = generate_password_hash(password)
    users[username] = {'password': hashed, 'role': args.role}
    save_users(users)
    print(f"User '{username}' added/updated in {USERS_FILE}")


if __name__ == '__main__':
    main()
