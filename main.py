from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)
DB_path = f"C:Users\mclau\Documents\Python Projects\Mortgages\CRUD\example.db"

def init_db():
    conn = sqlite3.connect(DB_path)
    cursor = conn.cursor()
    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS users(
                       id INTEGER PRIMARY KEY, 
                       name TEXT NOT NULL,
                       age INTEGER NOT NULL
                       )
    ''')
    conn.commit()
    conn.close()

def get_users():
    conn = sqlite3.connect(DB_path)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users')
    users = cursor.fetchall()
    conn.close()
    return users

def add_user(name, age):
    conn = sqlite3.connect(DB_path)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO users (name, age) VALUES (?, ?)', (name, age))
    conn.commit()
    conn.close()
    
def update_user(id, name, age):
    conn = sqlite3.connect(DB_path)
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET name = ?, age = ?, WHERE id = ?', (name, age, id))
    conn.commit()
    conn.close()
    
def delete_user(id):
    conn = sqlite3.connect(DB_path)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM users WHERE id = ?', (id))
    conn.commit()
    conn.close()
    
@app.route("/")
def index():
    users = get_users()
    return render_template('index.html', users=users)

@app.route('/add_user', methods=['POST'])
def add_user_route():
    name = request.form['name']
    age = request.form['age']
    add_user(name, age)
    return redirect(url_for('index'))

@app.route('/update_user/<int:id>', methods=['GET', 'POST'])
def update_user_route(id):
    if request.method == 'POST':
        name = request.form['name']
        age = request.form['age']
        update_user(id, name, age)
        return redirect(url_for('index'))
    
if __name__ == '__main__':
    init_db()
    app.run(debug=True)

#conn = sqlite3.connect(DB_path)
#cursor = conn.cursor()
#cursor.execute('SELECT * FROM users WHERE id = ?', (id, None))
#user = user.fetchall()
#conn.close()
#return render_template('update_user_html', user = user)


