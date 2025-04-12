from flask import Flask, redirect, render_template
import uuid
import sqlite3
app = Flask(__name__)

def init_db():
    with sqlite3.connect('database.db') as conn:
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS chall2_posts (id INTEGER PRIMARY KEY, uuid TEXT, title TEXT, content TEXT)''')
        conn.commit()



@app.route('/')
def hello_world():  # put application's code here
    return 'Hello World!'

@app.route('/chall1')
def chall1_redirect():
    random_uuid = str(uuid.uuid4())
    return redirect('/chall1/' + random_uuid)

@app.route('/chall1/<uuid:random_uuid>')
def chall1(random_uuid):
    return render_template('chall1.html')

@app.route('/chall2')
def chall1_redirect():
    random_uuid = str(uuid.uuid4())
    return redirect('/chall1/' + random_uuid)




if __name__ == '__main__':
    init_db()
    app.run()
