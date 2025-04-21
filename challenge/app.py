import asyncio
import datetime
import os
import secrets
import sqlite3
import uuid

from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask, redirect, render_template, jsonify, request, session
from playwright.async_api import async_playwright

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)
admin_password = secrets.token_hex(8)

def init_db():
    with sqlite3.connect('database.db') as conn:
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS chall1_posts (id INTEGER PRIMARY KEY, uuid TEXT, title TEXT, content TEXT)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS chall3_posts (id INTEGER PRIMARY KEY, user_id INTEGER, is_public Boolean, title TEXT, content TEXT)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS chall3_users (id INTEGER PRIMARY KEY, name text, password text)''')
        # Create admin user with random password
        cursor.execute('INSERT OR REPLACE INTO chall3_users (id, name, password) VALUES (1, ?, ?)',
                       ('admin', admin_password))

        # Add a private post using the flag from the environment variable
        flag = os.getenv('FLAG', 'default_flag')
        cursor.execute('INSERT OR IGNORE INTO chall3_posts (id, user_id, is_public, title, content) VALUES (1, ?, ?, ?, ?)',
                       (1, 0, 'Private Post', flag))
        conn.commit()



@app.route('/')
def hello_world():  # put application's code here
    return 'Hello World!'

@app.route('/chall1')
def chall1_redirect():
    random_uuid = str(uuid.uuid4())
    return redirect('/chall1/' + random_uuid)

@app.route('/chall1/<random_uuid>')
def chall1(random_uuid):
    return render_template('chall1.html')

@app.route('/chall1/<random_uuid>/posts', methods=['GET'])
def get_chall1_posts(random_uuid):
    # Fetch all posts from the database
    with sqlite3.connect('database.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT title, content FROM chall1_posts where uuid= ?', (random_uuid,))
        posts = [{'title': row[0], 'content': row[1]} for row in cursor.fetchall()]
    return jsonify(posts)

@app.route('/chall1/<random_uuid>/posts', methods=['POST'])
def post_chall1_posts(random_uuid):
    # Add a new post to the database
    data = request.get_json()
    title = data.get('title', '')
    content = data.get('content', '')

    with sqlite3.connect('database.db') as conn:
        cursor = conn.cursor()
        cursor.execute('INSERT INTO chall1_posts (uuid, title, content) VALUES (?, ?, ?)',
                       (random_uuid, title, content))
        conn.commit()
    return jsonify({'message': 'Post created successfully'}), 201


@app.route('/chall2')
def chall2_redirect():
    random_uuid = str(uuid.uuid4())
    return redirect('/chall2/' + random_uuid +"/posts")

@app.route('/chall2/<random_uuid>/posts', methods=['GET', 'POST'])
def chall2(random_uuid):
    if request.method == 'POST':
        title = request.form.get('title', '')
        content = request.form.get('content', '')
        with sqlite3.connect('database.db') as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO chall1_posts (uuid, title, content) VALUES (?, ?, ?)',
                           (random_uuid, title, content))
            conn.commit()
        return redirect(f'/chall2/{random_uuid}/posts')
    else:
        with sqlite3.connect('database.db') as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT title, content FROM chall1_posts where uuid= ?', (random_uuid,))
            posts = [{'title': row[0], 'content': row[1]} for row in cursor.fetchall()]
        return render_template('chall2.html', posts=posts)


@app.route('/chall3')
def chall3_login_redirect():
    return redirect('/chall3/login')
@app.route('/chall3/login')
def chall3_login():
    if(session.get('user_id_chall3') is not None):
        return redirect('/chall3/posts')
    return render_template('chall3_login.html')

@app.route('/chall3/login', methods=['POST'])
def chall3_login_post():
    username = request.form.get('username', '')
    password = request.form.get('password', '')
    with sqlite3.connect('database.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM chall3_users WHERE name = ? AND password = ?', (username, password))
        user = cursor.fetchone()
        if user:
            session['user_id_chall3'] = user[0]
            return redirect(f'/chall3/posts')
    return 'Invalid credentials', 401

@app.route('/chall3/register', methods=['POST'])
def chall3_register():
    username = request.form.get('username', '')
    password = request.form.get('password', '')
    with sqlite3.connect('database.db') as conn:
        cursor = conn.cursor()
        cursor.execute('INSERT INTO chall3_users (name, password) VALUES (?, ?)',
                       (username, password))
        conn.commit()
    return redirect(f'/chall3/login')

@app.route('/chall3/posts', methods=['GET'])
def chall3_posts():
    user_id = session.get('user_id_chall3')
    with sqlite3.connect('database.db') as conn:
        cursor = conn.cursor()
        if user_id:
            cursor.execute('''
                SELECT title, content, is_public FROM chall3_posts 
                WHERE is_public = 1  or (is_public = 0 AND user_id = ?)
            ''', (user_id, ))
            posts = [{'title': row[0], 'content': row[1], 'is_public': row[2]} for row in cursor.fetchall()]
            return render_template('chall3_posts.html', posts=posts)
        else:
            return redirect(f'/chall3/login')

@app.route('/chall3/posts', methods=['POST'])
def chall3_create_post():
    user_id = session.get('user_id_chall3')
    if not user_id:
        return redirect(f'/chall3/login')

    title = request.form.get('title', '')
    content = request.form.get('content', '')
    is_public = 1 if request.form.get('is_public') else 0

    with sqlite3.connect('database.db') as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO chall3_posts (user_id, is_public, title, content)
            VALUES (?, ?, ?, ?)
        ''', (user_id, is_public, title, content))
        conn.commit()

    return redirect(f'/chall3/posts')

@app.route('/chall3/logout')
def chall3_logout():
    session.pop('user_id_chall3', None)
    return redirect(f'/chall3/login')

scheduler = BackgroundScheduler()

# Define your task
def scheduled_task():
    app.logger.warning("Calling admin bot")
    asyncio.run(visit_site())

# Async function to visit the website using Playwright
async def visit_site():
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            url = os.getenv("URL")
            await page.goto(url + "/chall3/login")

            await page.wait_for_load_state("networkidle")
            # Fill out the form
            await page.fill("input#username", "admin")  # Replace with the desired username
            await page.fill("input#password", admin_password)  # Replace with the desired password

            # Click the login button
            await page.click("button#login_submit")

            await asyncio.sleep(5)
            app.logger.warning("Admin done")

            with sqlite3.connect('database.db') as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM chall3_posts WHERE is_public = 1')
                conn.commit()

            await browser.close()
    except Exception as e:
        app.logger.error(f"Error visiting site: {e}")

# Start the scheduler with a simple interval job
scheduler.add_job(scheduled_task, 'interval', seconds=60, start_date=datetime.datetime.now() + datetime.timedelta(seconds=5))
app.logger.warning("Starting")
init_db()
scheduler.start()
if __name__ == '__main__':
    app.run()
