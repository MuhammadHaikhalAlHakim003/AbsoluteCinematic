#!/usr/bin/env python3
"""
Seed script to create an initial admin user in the SQLite database.

Usage (PowerShell):
    .venv\Scripts\Activate.ps1
    python scripts\seed_admin.py --email admin@example.com --password secret

If the user with the provided email exists the script will update the role to 'admin'.
"""
import argparse
import sqlite3
import os
from werkzeug.security import generate_password_hash

ROOT = os.path.dirname(os.path.dirname(__file__))
DB_PATH = os.path.join(ROOT, 'database.db')


def ensure_db():
    # ensure database exists and users table has role column
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, email TEXT NOT NULL UNIQUE, password TEXT NOT NULL, membership TEXT NOT NULL DEFAULT 'member', created_at TEXT)")
    # ensure role column
    cur.execute("PRAGMA table_info(users)")
    cols = [r[1] for r in cur.fetchall()]
    if 'role' not in cols:
        try:
            cur.execute("ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'user'")
        except Exception:
            pass
    conn.commit()
    conn.close()


def seed_admin(name, email, password):
    ensure_db()
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    hashed = generate_password_hash(password)
    now = __import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M')
    # check existing
    cur.execute("SELECT id FROM users WHERE email = ?", (email,))
    row = cur.fetchone()
    if row:
        cur.execute("UPDATE users SET password = ?, role = 'admin' WHERE email = ?", (hashed, email))
        print(f"Updated existing user {email} to admin.")
    else:
        cur.execute("INSERT INTO users (name, email, password, membership, created_at, role) VALUES (?, ?, ?, ?, ?, 'admin')", (name, email, hashed, 'member', now))
        print(f"Created admin user {email}.")
    conn.commit()
    conn.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--name', default='Administrator')
    parser.add_argument('--email', required=True)
    parser.add_argument('--password', required=True)
    args = parser.parse_args()
    seed_admin(args.name, args.email, args.password)


if __name__ == '__main__':
    main()
