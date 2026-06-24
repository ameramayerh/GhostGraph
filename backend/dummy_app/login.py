
import sqlite3
import os

def login(username, password):
    # Vulnerability 1: SQL Injection
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    query = "SELECT * FROM users WHERE username = '" + username + "' AND password = '" + password + "'"
    cursor.execute(query)
    
    # Vulnerability 2: Hardcoded Secret
    AWS_SECRET_KEY = "AKIAIOSFODNN7EXAMPLE"
    
    return cursor.fetchone()
