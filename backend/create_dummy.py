import zipfile
import os

vuln_code = """
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
"""

os.makedirs("dummy_app", exist_ok=True)
with open("dummy_app/login.py", "w") as f:
    f.write(vuln_code)

with zipfile.ZipFile("vuln_app.zip", "w") as zf:
    zf.write("dummy_app/login.py", "login.py")

print("Created vuln_app.zip")
