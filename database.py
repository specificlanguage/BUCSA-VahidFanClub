import sqlite3
import mail_service
from werkzeug.security import generate_password_hash, check_password_hash

con_init = sqlite3.connect('database.db')
init_cursor = con_init.cursor()

# Initialize tables if non-existent
init_cursor.execute("""CREATE TABLE IF NOT EXISTS users ('id' INTEGER PRIMARY KEY, 'email' VARCHAR(255), 'hash' VARCHAR(255), 'verified' BOOLEAN, 'isadmin' BOOLEAN)""")
con_init.commit() # this is very hacky and barely a temp fix
# IMPORTANT!!! default admin password is 'vahidfanclub', AND IT SHOULD BE CHANGED ON INITIAL LOGIN!
insecure_password_hash = generate_password_hash("vahidfanclub")
init_cursor.execute("""INSERT OR IGNORE INTO users (id, email, hash, verified, isadmin) VALUES (0, 'admin', ?, ?, ?)""",[insecure_password_hash, True, True])
init_cursor.execute("""CREATE TABLE IF NOT EXISTS email_list (id INTEGER PRIMARY KEY, email VARCHAR(255))""")
init_cursor.execute("""CREATE TABLE IF NOT EXISTS verify_tokens (email VARCHAR(255), verify_token VARCHAR(255))""")
con_init.commit()

def login_user(email, password):
    with sqlite3.connect("database.db") as con:
        con.row_factory = sqlite3.Row
        cursor = con.cursor()
        result = cursor.execute("""SELECT * FROM users WHERE email = ?;""", [email]).fetchone()
        if result is None:
            return 0
        result = dict(result)
        if result["verified"] == 0: # index of verified. This does seem hacky but it does work for me...
            return -1  # not verified, need to resend email!
        test_hash = check_password_hash(result["hash"], password)
        if test_hash == True:
            if result["isadmin"] == 1:
                return 2  # admin is logging in :)
            return 1  # logged in
        return 0


def register_user(email_address, password):
    if len(password) < 6 or len(password) > 30:
        return -1
    with sqlite3.connect("database.db") as con:
        con.row_factory = sqlite3.Row
        cursor = con.cursor()
        result = cursor.execute("""SELECT * FROM users WHERE email = ?;""", [email_address]).fetchone()
        if result is None: # user doesn't exist yet
            hash = generate_password_hash(password)
            last_user_id = dict(cursor.execute("SELECT id FROM users ORDER BY id DESC LIMIT 1").fetchone())["id"]
            cursor.execute("""INSERT INTO users VALUES (?, ?, ?, 0, 0)""", [last_user_id + 1, email_address, hash])
            con.commit()
            create_verify_token(email_address)
            return 1
        else:
            return -2  # already has an account, can just go to login.


def verify_token(token):
    with sqlite3.connect("database.db") as con:
        con.row_factory = sqlite3.Row
        cursor = con.cursor()
        valid_address = cursor.execute("""SELECT * FROM verify_tokens WHERE verify_token = ?""", [token]).fetchone()
        if valid_address is None: # no token exists yet for that user
            return False
        address = dict(valid_address)["email"]
        cursor.execute("""UPDATE users SET verified = 1 WHERE email = ?""", [address])
        cursor.execute("""DELETE FROM verify_tokens WHERE email = ?""", [address])
    add_to_email_list(address)
    return True


def add_to_email_list(address):
    with sqlite3.connect("database.db") as con:
        con.row_factory = sqlite3.Row
        cursor = con.cursor()
        last_user_id = cursor.execute("SELECT id FROM users ORDER BY id DESC LIMIT 1").fetchone()
        if last_user_id is None:
            last_user_id = -1
        else:
            last_user_id = dict(last_user_id)["id"]
        cursor.execute("""INSERT INTO email_list (id, email) VALUES (?, ?)""",
                       [last_user_id + 1, address])

def create_verify_token(email_address):
    with sqlite3.connect("database.db") as con:
        con.row_factory = sqlite3.Row
        cursor = con.cursor()
        token = mail_service.generate_token()
        cursor.execute("""INSERT INTO verify_tokens (email, verify_token)
          VALUES(?, ?)""", [email_address, token])
        mail_service.email_verify(email_address, token)


def reset_password(email_address, password):
    with sqlite3.connect("database.db") as con:
        con.row_factory = sqlite3.Row
        cursor = con.cursor()
        hash = generate_password_hash(password)
        cursor.execute("""REPLACE INTO users (hash, verified) VALUES (?, ?)""", [hash, 1])
        cursor.execute("""DELETE FROM verify_tokens WHERE email = ?""", [email_address])


def update_user(email_address):
    with sqlite3.connect("database.db") as con:
        con.row_factory = sqlite3.Row
        cursor = con.cursor()
        email = cursor.execute("""SELECT * FROM users WHERE email=?""", [email_address]).fetchone()
        if email is None:
            return
        cursor.execute("""UPDATE users SET isadmin=1 WHERE email=?""", [email["email"]])


def get_emails():
    with sqlite3.connect("database.db") as con:
        con.row_factory = sqlite3.Row
        cursor = con.cursor()
    emails = cursor.execute("""SELECT * FROM email_list""").fetchall()
    if emails is None:
        return []
    return [(email["email"], "") for email in emails]

