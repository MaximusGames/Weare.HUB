import os
import sqlite3
from datetime import datetime
from functools import wraps
from flask import Flask, render_template, request, jsonify, session, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
app = Flask(__name__)
app.secret_key = 'HUB-local-development-secret-change-later'
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, 'hub.db')
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads', 'hubs')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = ON')
    return conn

def init_db():
    conn = get_db()
    conn.executescript("\n\n        CREATE TABLE IF NOT EXISTS users (\n\n            id INTEGER PRIMARY KEY AUTOINCREMENT,\n\n            username TEXT NOT NULL UNIQUE,\n\n            password_hash TEXT NOT NULL,\n\n            avatar TEXT DEFAULT '',\n\n            bio TEXT DEFAULT '',\n\n            status TEXT DEFAULT 'online',\n\n            theme TEXT DEFAULT 'dark',\n\n            compact_mode INTEGER DEFAULT 0,\n\n            notifications INTEGER DEFAULT 1,\n\n            created_at TEXT NOT NULL\n\n        );\n\n\n        CREATE TABLE IF NOT EXISTS friends (\n\n            id INTEGER PRIMARY KEY AUTOINCREMENT,\n\n            sender_id INTEGER NOT NULL,\n\n            receiver_id INTEGER NOT NULL,\n\n            status TEXT DEFAULT 'pending',\n\n            created_at TEXT NOT NULL,\n\n            UNIQUE(sender_id, receiver_id),\n\n            FOREIGN KEY(sender_id)\n                REFERENCES users(id)\n                ON DELETE CASCADE,\n\n            FOREIGN KEY(receiver_id)\n                REFERENCES users(id)\n                ON DELETE CASCADE\n\n        );\n\n\n        CREATE TABLE IF NOT EXISTS hubs (\n\n            id INTEGER PRIMARY KEY AUTOINCREMENT,\n\n            owner_id INTEGER NOT NULL,\n\n            name TEXT NOT NULL,\n\n            description TEXT DEFAULT '',\n\n            icon TEXT DEFAULT '',\n\n            icon_type TEXT DEFAULT 'letter',\n\n            color TEXT DEFAULT '#7c5cff',\n\n            banner TEXT DEFAULT '',\n\n            public INTEGER DEFAULT 0,\n\n            rules TEXT DEFAULT '',\n\n            created_at TEXT NOT NULL,\n\n            FOREIGN KEY(owner_id)\n                REFERENCES users(id)\n                ON DELETE CASCADE\n\n        );\n\n\n        CREATE TABLE IF NOT EXISTS hub_members (\n\n            id INTEGER PRIMARY KEY AUTOINCREMENT,\n\n            hub_id INTEGER NOT NULL,\n\n            user_id INTEGER NOT NULL,\n\n            role TEXT DEFAULT 'member',\n\n            joined_at TEXT NOT NULL,\n\n            UNIQUE(hub_id, user_id),\n\n            FOREIGN KEY(hub_id)\n                REFERENCES hubs(id)\n                ON DELETE CASCADE,\n\n            FOREIGN KEY(user_id)\n                REFERENCES users(id)\n                ON DELETE CASCADE\n\n        );\n\n\n        CREATE TABLE IF NOT EXISTS channels (\n\n            id INTEGER PRIMARY KEY AUTOINCREMENT,\n\n            hub_id INTEGER NOT NULL,\n\n            name TEXT NOT NULL,\n\n            channel_type TEXT DEFAULT 'text',\n\n            position INTEGER DEFAULT 0,\n\n            created_at TEXT NOT NULL,\n\n            FOREIGN KEY(hub_id)\n                REFERENCES hubs(id)\n                ON DELETE CASCADE\n\n        );\n\n\n        CREATE TABLE IF NOT EXISTS messages (\n\n            id INTEGER PRIMARY KEY AUTOINCREMENT,\n\n            channel_id INTEGER NOT NULL,\n\n            user_id INTEGER NOT NULL,\n\n            content TEXT NOT NULL,\n\n            reply_to INTEGER,\n\n            edited INTEGER DEFAULT 0,\n\n            pinned INTEGER DEFAULT 0,\n\n            created_at TEXT NOT NULL,\n\n            updated_at TEXT,\n\n            FOREIGN KEY(channel_id)\n                REFERENCES channels(id)\n                ON DELETE CASCADE,\n\n            FOREIGN KEY(user_id)\n                REFERENCES users(id)\n                ON DELETE CASCADE,\n\n            FOREIGN KEY(reply_to)\n                REFERENCES messages(id)\n                ON DELETE SET NULL\n\n        );\n\n\n        CREATE TABLE IF NOT EXISTS reactions (\n\n            id INTEGER PRIMARY KEY AUTOINCREMENT,\n\n            message_id INTEGER NOT NULL,\n\n            user_id INTEGER NOT NULL,\n\n            emoji TEXT NOT NULL,\n\n            UNIQUE(message_id, user_id, emoji),\n\n            FOREIGN KEY(message_id)\n                REFERENCES messages(id)\n                ON DELETE CASCADE,\n\n            FOREIGN KEY(user_id)\n                REFERENCES users(id)\n                ON DELETE CASCADE\n\n        );\n\n\n        CREATE TABLE IF NOT EXISTS invitations (\n\n            id INTEGER PRIMARY KEY AUTOINCREMENT,\n\n            hub_id INTEGER NOT NULL,\n\n            sender_id INTEGER NOT NULL,\n\n            receiver_id INTEGER NOT NULL,\n\n            status TEXT DEFAULT 'pending',\n\n            created_at TEXT NOT NULL,\n\n            FOREIGN KEY(hub_id)\n                REFERENCES hubs(id)\n                ON DELETE CASCADE,\n\n            FOREIGN KEY(sender_id)\n                REFERENCES users(id)\n                ON DELETE CASCADE,\n\n            FOREIGN KEY(receiver_id)\n                REFERENCES users(id)\n                ON DELETE CASCADE\n\n        );\n\n\n        CREATE TABLE IF NOT EXISTS files (\n\n            id INTEGER PRIMARY KEY AUTOINCREMENT,\n\n            hub_id INTEGER NOT NULL,\n\n            channel_id INTEGER,\n\n            user_id INTEGER NOT NULL,\n\n            filename TEXT NOT NULL,\n\n            stored_name TEXT NOT NULL,\n\n            created_at TEXT NOT NULL,\n\n            FOREIGN KEY(hub_id)\n                REFERENCES hubs(id)\n                ON DELETE CASCADE,\n\n            FOREIGN KEY(channel_id)\n                REFERENCES channels(id)\n                ON DELETE SET NULL,\n\n            FOREIGN KEY(user_id)\n                REFERENCES users(id)\n                ON DELETE CASCADE\n\n        );\n\n\n        CREATE TABLE IF NOT EXISTS events (\n\n            id INTEGER PRIMARY KEY AUTOINCREMENT,\n\n            hub_id INTEGER NOT NULL,\n\n            creator_id INTEGER NOT NULL,\n\n            title TEXT NOT NULL,\n\n            description TEXT DEFAULT '',\n\n            event_date TEXT NOT NULL,\n\n            created_at TEXT NOT NULL,\n\n            FOREIGN KEY(hub_id)\n                REFERENCES hubs(id)\n                ON DELETE CASCADE,\n\n            FOREIGN KEY(creator_id)\n                REFERENCES users(id)\n                ON DELETE CASCADE\n\n        );\n\n\n        CREATE TABLE IF NOT EXISTS tasks (\n\n            id INTEGER PRIMARY KEY AUTOINCREMENT,\n\n            hub_id INTEGER NOT NULL,\n\n            creator_id INTEGER NOT NULL,\n\n            title TEXT NOT NULL,\n\n            description TEXT DEFAULT '',\n\n            status TEXT DEFAULT 'todo',\n\n            assigned_to INTEGER,\n\n            created_at TEXT NOT NULL,\n\n            FOREIGN KEY(hub_id)\n                REFERENCES hubs(id)\n                ON DELETE CASCADE,\n\n            FOREIGN KEY(creator_id)\n                REFERENCES users(id)\n                ON DELETE CASCADE,\n\n            FOREIGN KEY(assigned_to)\n                REFERENCES users(id)\n                ON DELETE SET NULL\n\n        );\n\n\n        CREATE TABLE IF NOT EXISTS notes (\n\n            id INTEGER PRIMARY KEY AUTOINCREMENT,\n\n            hub_id INTEGER NOT NULL,\n\n            user_id INTEGER NOT NULL,\n\n            title TEXT NOT NULL,\n\n            content TEXT DEFAULT '',\n\n            updated_at TEXT NOT NULL,\n\n            FOREIGN KEY(hub_id)\n                REFERENCES hubs(id)\n                ON DELETE CASCADE,\n\n            FOREIGN KEY(user_id)\n                REFERENCES users(id)\n                ON DELETE CASCADE\n\n        );\n\n\n        CREATE TABLE IF NOT EXISTS polls (\n\n            id INTEGER PRIMARY KEY AUTOINCREMENT,\n\n            hub_id INTEGER NOT NULL,\n\n            user_id INTEGER NOT NULL,\n\n            question TEXT NOT NULL,\n\n            options TEXT NOT NULL,\n\n            created_at TEXT NOT NULL,\n\n            FOREIGN KEY(hub_id)\n                REFERENCES hubs(id)\n                ON DELETE CASCADE,\n\n            FOREIGN KEY(user_id)\n                REFERENCES users(id)\n                ON DELETE CASCADE\n\n        );\n\n\n        CREATE TABLE IF NOT EXISTS notifications (\n\n            id INTEGER PRIMARY KEY AUTOINCREMENT,\n\n            user_id INTEGER NOT NULL,\n\n            title TEXT NOT NULL,\n\n            content TEXT NOT NULL,\n\n            type TEXT DEFAULT 'info',\n\n            read INTEGER DEFAULT 0,\n\n            created_at TEXT NOT NULL,\n\n            FOREIGN KEY(user_id)\n                REFERENCES users(id)\n                ON DELETE CASCADE\n\n        );\n\n\n        CREATE TABLE IF NOT EXISTS activity (\n\n            id INTEGER PRIMARY KEY AUTOINCREMENT,\n\n            hub_id INTEGER,\n\n            user_id INTEGER,\n\n            action TEXT NOT NULL,\n\n            details TEXT DEFAULT '',\n\n            created_at TEXT NOT NULL,\n\n            FOREIGN KEY(hub_id)\n                REFERENCES hubs(id)\n                ON DELETE CASCADE,\n\n            FOREIGN KEY(user_id)\n                REFERENCES users(id)\n                ON DELETE CASCADE\n\n        );\n\n\n        CREATE TABLE IF NOT EXISTS hub_invite_links (\n\n            id INTEGER PRIMARY KEY AUTOINCREMENT,\n\n            hub_id INTEGER NOT NULL,\n\n            code TEXT NOT NULL UNIQUE,\n\n            created_at TEXT NOT NULL,\n\n            FOREIGN KEY(hub_id)\n                REFERENCES hubs(id)\n                ON DELETE CASCADE\n\n        );\n\n        ")
    columns = [row[1] for row in conn.execute("PRAGMA table_info(users)").fetchall()]
    if "language" not in columns:
        conn.execute("ALTER TABLE users ADD COLUMN language TEXT DEFAULT 'de'")
    conn.commit()
    conn.close()

def now():
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

def current_user():
    user_id = session.get('user_id')
    if not user_id:
        return None
    conn = get_db()
    user = conn.execute('\n        SELECT *\n        FROM users\n        WHERE id = ?\n        ', (user_id,)).fetchone()
    conn.close()
    return user

def login_required_api(function):

    @wraps(function)
    def wrapper(*args, **kwargs):
        if not current_user():
            return (jsonify({'success': False, 'error': 'Nicht angemeldet.'}), 401)
        return function(*args, **kwargs)
    return wrapper

def is_hub_member(hub_id, user_id):
    conn = get_db()
    result = conn.execute('\n        SELECT *\n        FROM hub_members\n        WHERE hub_id = ?\n        AND user_id = ?\n        ', (hub_id, user_id)).fetchone()
    conn.close()
    return result

def is_hub_admin(hub_id, user_id):
    member = is_hub_member(hub_id, user_id)
    if not member:
        return False
    return member['role'] in ('owner', 'admin')

def is_hub_owner(hub_id, user_id):
    member = is_hub_member(hub_id, user_id)
    return bool(member and member['role'] == 'owner')

def add_activity(hub_id, user_id, action, details=''):
    conn = get_db()
    conn.execute('\n        INSERT INTO activity\n        (hub_id, user_id, action, details, created_at)\n        VALUES (?, ?, ?, ?, ?)\n        ', (hub_id, user_id, action, details, now()))
    conn.commit()
    conn.close()

def notify(user_id, title, content, notification_type='info'):
    conn = get_db()
    conn.execute('\n        INSERT INTO notifications\n        (user_id, title, content, type, created_at)\n        VALUES (?, ?, ?, ?, ?)\n        ', (user_id, title, content, notification_type, now()))
    conn.commit()
    conn.close()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/me')
def me():
    user = current_user()
    if not user:
        return jsonify({'logged_in': False})
    return jsonify({'logged_in': True, 'user': dict(user)})

@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json() or {}
    username = data.get('username', '').strip()
    password = data.get('password', '')
    if len(username) < 3:
        return jsonify({'success': False, 'error': 'Der Benutzername muss mindestens 3 Zeichen haben.'})
    if len(password) < 6:
        return jsonify({'success': False, 'error': 'Das Passwort muss mindestens 6 Zeichen haben.'})
    conn = get_db()
    existing = conn.execute('\n        SELECT id\n        FROM users\n        WHERE LOWER(username) = LOWER(?)\n        ', (username,)).fetchone()
    if existing:
        conn.close()
        return jsonify({'success': False, 'error': 'Dieser Benutzername ist bereits vergeben.'})
    cursor = conn.execute('\n        INSERT INTO users\n        (\n            username,\n            password_hash,\n            created_at\n        )\n        VALUES (?, ?, ?)\n        ', (username, generate_password_hash(password), now()))
    user_id = cursor.lastrowid
    conn.commit()
    conn.close()
    session['user_id'] = user_id
    return jsonify({'success': True})

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    username = data.get('username', '').strip()
    password = data.get('password', '')
    conn = get_db()
    user = conn.execute('\n        SELECT *\n        FROM users\n        WHERE LOWER(username) = LOWER(?)\n        ', (username,)).fetchone()
    conn.close()
    if not user:
        return jsonify({'success': False, 'error': 'Benutzername oder Passwort ist falsch.'})
    if not check_password_hash(user['password_hash'], password):
        return jsonify({'success': False, 'error': 'Benutzername oder Passwort ist falsch.'})
    session['user_id'] = user['id']
    return jsonify({'success': True})

@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'success': True})

@app.route('/api/settings', methods=['POST'])
@login_required_api
def save_settings():
    user = current_user()
    data = request.get_json() or {}
    theme = data.get('theme', 'dark')
    if theme not in ('dark', 'light'):
        theme = 'dark'
    compact_mode = 1 if data.get('compact_mode') else 0
    notifications_enabled = 1 if data.get('notifications') else 0
    bio = data.get('bio', '').strip()
    language = data.get('language', user['language'] if 'language' in user.keys() else 'de')
    if language not in ('de', 'en'):
        language = 'de'
    conn = get_db()
    conn.execute('\n        UPDATE users\n        SET\n            theme = ?,\n            compact_mode = ?,\n            notifications = ?,\n            bio = ?,\n            language = ?\n        WHERE id = ?\n        ', (theme, compact_mode, notifications_enabled, bio, language, user['id']))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/settings/username', methods=['POST'])
@login_required_api
def change_username():
    user = current_user()
    data = request.get_json() or {}
    username = data.get('username', '').strip()
    if len(username) < 3:
        return jsonify({'success': False, 'error': 'Der Benutzername ist zu kurz.'})
    conn = get_db()
    exists = conn.execute('\n        SELECT id\n        FROM users\n        WHERE LOWER(username) = LOWER(?)\n        AND id != ?\n        ', (username, user['id'])).fetchone()
    if exists:
        conn.close()
        return jsonify({'success': False, 'error': 'Dieser Benutzername ist bereits vergeben.'})
    conn.execute('\n        UPDATE users\n        SET username = ?\n        WHERE id = ?\n        ', (username, user['id']))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/settings/password', methods=['POST'])
@login_required_api
def change_password():
    user = current_user()
    data = request.get_json() or {}
    old_password = data.get('old_password', '')
    new_password = data.get('new_password', '')
    conn = get_db()
    stored = conn.execute('\n        SELECT password_hash\n        FROM users\n        WHERE id = ?\n        ', (user['id'],)).fetchone()
    if not check_password_hash(stored['password_hash'], old_password):
        conn.close()
        return jsonify({'success': False, 'error': 'Das aktuelle Passwort ist falsch.'})
    if len(new_password) < 6:
        conn.close()
        return jsonify({'success': False, 'error': 'Das neue Passwort muss mindestens 6 Zeichen haben.'})
    conn.execute('\n        UPDATE users\n        SET password_hash = ?\n        WHERE id = ?\n        ', (generate_password_hash(new_password), user['id']))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/users/search')
@login_required_api
def search_users():
    user = current_user()
    query = request.args.get('q', '').strip()
    if len(query) < 1:
        return jsonify({'users': []})
    conn = get_db()
    users = conn.execute('\n        SELECT\n            id,\n            username,\n            avatar,\n            bio,\n            status\n        FROM users\n        WHERE LOWER(username)\n        LIKE LOWER(?)\n        AND id != ?\n        ORDER BY username\n        LIMIT 20\n        ', ('%' + query + '%', user['id'])).fetchall()
    conn.close()
    return jsonify({'users': [dict(item) for item in users]})

@app.route('/api/friends')
@login_required_api
def get_friends():
    user = current_user()
    conn = get_db()
    friends = conn.execute('\n        SELECT\n            f.id,\n            f.sender_id,\n            f.receiver_id,\n            f.status,\n            u.id AS user_id,\n            u.username,\n            u.avatar,\n            u.bio,\n            u.status AS online_status\n        FROM friends f\n        JOIN users u\n        ON\n            CASE\n                WHEN f.sender_id = ?\n                THEN f.receiver_id\n                ELSE f.sender_id\n            END = u.id\n        WHERE\n            (\n                f.sender_id = ?\n                OR\n                f.receiver_id = ?\n            )\n        ', (user['id'], user['id'], user['id'])).fetchall()
    conn.close()
    return jsonify({'friends': [dict(friend) for friend in friends]})

@app.route('/api/friends/request', methods=['POST'])
@login_required_api
def friend_request():
    user = current_user()
    data = request.get_json() or {}
    receiver_id = data.get('user_id')
    if not receiver_id:
        return jsonify({'success': False, 'error': 'Kein Benutzer angegeben.'})
    if int(receiver_id) == user['id']:
        return jsonify({'success': False, 'error': 'Du kannst dich nicht selbst hinzufügen.'})
    conn = get_db()
    try:
        conn.execute("\n            INSERT INTO friends\n            (\n                sender_id,\n                receiver_id,\n                status,\n                created_at\n            )\n            VALUES (?, ?, 'pending', ?)\n            ", (user['id'], receiver_id, now()))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({'success': False, 'error': 'Eine Anfrage existiert bereits.'})
    conn.close()
    notify(receiver_id, 'Neue Freundschaftsanfrage', user['username'] + ' möchte dich als Freund hinzufügen.', 'friend')
    return jsonify({'success': True})

@app.route('/api/friends/<int:friend_id>/<action>', methods=['POST'])
@login_required_api
def handle_friend(friend_id, action):
    user = current_user()
    conn = get_db()
    friendship = conn.execute('\n        SELECT *\n        FROM friends\n        WHERE id = ?\n        AND receiver_id = ?\n        ', (friend_id, user['id'])).fetchone()
    if not friendship:
        conn.close()
        return jsonify({'success': False, 'error': 'Anfrage nicht gefunden.'})
    if action == 'accept':
        conn.execute("\n            UPDATE friends\n            SET status = 'accepted'\n            WHERE id = ?\n            ", (friend_id,))
    elif action == 'decline':
        conn.execute('\n            DELETE FROM friends\n            WHERE id = ?\n            ', (friend_id,))
    else:
        conn.close()
        return jsonify({'success': False})
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/hubs')
@login_required_api
def get_hubs():
    user = current_user()
    conn = get_db()
    hubs = conn.execute('\n        SELECT\n            h.*,\n            hm.role\n        FROM hubs h\n        JOIN hub_members hm\n        ON h.id = hm.hub_id\n        WHERE hm.user_id = ?\n        ORDER BY h.name\n        ', (user['id'],)).fetchall()
    conn.close()
    return jsonify({'hubs': [dict(hub) for hub in hubs]})

@app.route('/api/hubs/create', methods=['POST'])
@login_required_api
def create_hub():
    user = current_user()
    name = request.form.get('name', '').strip()
    description = request.form.get('description', '').strip()
    color = request.form.get('color', '#7c5cff')
    public = 1 if request.form.get('public') == '1' else 0
    rules = request.form.get('rules', '').strip()
    if not name:
        return jsonify({'success': False, 'error': 'Bitte gib einen Namen ein.'})
    icon = name[0].upper()
    icon_type = 'letter'
    icon_file = request.files.get('icon_file')
    if icon_file and icon_file.filename:
        filename = secure_filename(icon_file.filename)
        if filename:
            unique_name = str(int(datetime.now().timestamp() * 1000)) + '_' + filename
            path = os.path.join(UPLOAD_FOLDER, unique_name)
            icon_file.save(path)
            icon = '/static/uploads/hubs/' + unique_name
            icon_type = 'image'
    conn = get_db()
    cursor = conn.execute('\n        INSERT INTO hubs\n        (\n            owner_id,\n            name,\n            description,\n            icon,\n            icon_type,\n            color,\n            public,\n            rules,\n            created_at\n        )\n        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)\n        ', (user['id'], name, description, icon, icon_type, color, public, rules, now()))
    hub_id = cursor.lastrowid
    conn.execute("\n        INSERT INTO hub_members\n        (\n            hub_id,\n            user_id,\n            role,\n            joined_at\n        )\n        VALUES (?, ?, 'owner', ?)\n        ", (hub_id, user['id'], now()))
    conn.execute("\n        INSERT INTO channels\n        (\n            hub_id,\n            name,\n            channel_type,\n            position,\n            created_at\n        )\n        VALUES (?, 'general', 'text', 0, ?)\n        ", (hub_id, now()))
    conn.execute("\n        INSERT INTO channels\n        (\n            hub_id,\n            name,\n            channel_type,\n            position,\n            created_at\n        )\n        VALUES (?, 'announcements', 'announcement', 1, ?)\n        ", (hub_id, now()))
    conn.commit()
    conn.close()
    add_activity(hub_id, user['id'], 'created', 'created the Hub')
    return jsonify({'success': True, 'hub_id': hub_id})

@app.route('/api/hubs/<int:hub_id>')
@login_required_api
def hub_details(hub_id):
    user = current_user()
    if not is_hub_member(hub_id, user['id']):
        return (jsonify({'success': False, 'error': 'Du bist kein Mitglied dieses Hubs.'}), 403)
    conn = get_db()
    hub = conn.execute('\n        SELECT *\n        FROM hubs\n        WHERE id = ?\n        ', (hub_id,)).fetchone()
    members = conn.execute("\n        SELECT\n            hm.id,\n            hm.user_id,\n            hm.role,\n            hm.joined_at,\n            u.username,\n            u.avatar,\n            u.bio,\n            u.status\n        FROM hub_members hm\n        JOIN users u\n        ON hm.user_id = u.id\n        WHERE hm.hub_id = ?\n        ORDER BY\n            CASE hm.role\n                WHEN 'owner' THEN 0\n                WHEN 'admin' THEN 1\n                ELSE 3\n            END,\n            u.username\n        ", (hub_id,)).fetchall()
    channels = conn.execute('\n        SELECT *\n        FROM channels\n        WHERE hub_id = ?\n        ORDER BY position, name\n        ', (hub_id,)).fetchall()
    conn.close()
    return jsonify({'success': True, 'hub': dict(hub), 'members': [dict(member) for member in members], 'channels': [dict(channel) for channel in channels]})

@app.route('/api/hubs/<int:hub_id>/channels', methods=['POST'])
@login_required_api
def create_channel(hub_id):
    user = current_user()
    if not is_hub_admin(hub_id, user['id']):
        return (jsonify({'success': False, 'error': 'Keine Berechtigung.'}), 403)
    data = request.get_json() or {}
    name = data.get('name', '').strip()
    channel_type = data.get('type', 'text')
    if channel_type not in ('text', 'announcement'):
        channel_type = 'text'
    if not name:
        return jsonify({'success': False, 'error': 'Bitte gib einen Namen ein.'})
    conn = get_db()
    maximum = conn.execute('\n        SELECT COALESCE(MAX(position), -1)\n        FROM channels\n        WHERE hub_id = ?\n        ', (hub_id,)).fetchone()[0]
    conn.execute('\n        INSERT INTO channels\n        (\n            hub_id,\n            name,\n            channel_type,\n            position,\n            created_at\n        )\n        VALUES (?, ?, ?, ?, ?)\n        ', (hub_id, name, channel_type, maximum + 1, now()))
    conn.commit()
    conn.close()
    add_activity(hub_id, user['id'], 'channel', 'created #' + name)
    return jsonify({'success': True})

@app.route('/api/channels/<int:channel_id>', methods=['DELETE'])
@login_required_api
def delete_channel(channel_id):
    user = current_user()
    conn = get_db()
    channel = conn.execute('\n        SELECT *\n        FROM channels\n        WHERE id = ?\n        ', (channel_id,)).fetchone()
    if not channel:
        conn.close()
        return jsonify({'success': False})
    if not is_hub_admin(channel['hub_id'], user['id']):
        conn.close()
        return (jsonify({'success': False, 'error': 'Keine Berechtigung.'}), 403)
    count = conn.execute('\n        SELECT COUNT(*)\n        FROM channels\n        WHERE hub_id = ?\n        ', (channel['hub_id'],)).fetchone()[0]
    if count <= 1:
        conn.close()
        return jsonify({'success': False, 'error': 'Der letzte Channel kann nicht gelöscht werden.'})
    conn.execute('\n        DELETE FROM channels\n        WHERE id = ?\n        ', (channel_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/channels/<int:channel_id>/messages')
@login_required_api
def get_messages(channel_id):
    user = current_user()
    conn = get_db()
    channel = conn.execute('\n        SELECT *\n        FROM channels\n        WHERE id = ?\n        ', (channel_id,)).fetchone()
    if not channel:
        conn.close()
        return jsonify({'messages': []})
    if not is_hub_member(channel['hub_id'], user['id']):
        conn.close()
        return (jsonify({'success': False}), 403)
    messages = conn.execute('\n        SELECT\n            m.*,\n            u.username,\n            u.avatar,\n            (\n                SELECT COUNT(*)\n                FROM reactions r\n                WHERE r.message_id = m.id\n            ) AS reaction_count\n        FROM messages m\n        JOIN users u\n        ON m.user_id = u.id\n        WHERE m.channel_id = ?\n        ORDER BY m.created_at ASC, m.id ASC\n        LIMIT 300\n        ', (channel_id,)).fetchall()
    result = []
    for message in messages:
        item = dict(message)
        reactions = conn.execute('\n            SELECT\n                emoji,\n                COUNT(*) AS count\n            FROM reactions\n            WHERE message_id = ?\n            GROUP BY emoji\n            ORDER BY count DESC\n            ', (message['id'],)).fetchall()
        item['reactions'] = [dict(reaction) for reaction in reactions]
        result.append(item)
    conn.close()
    return jsonify({'messages': result})

@app.route('/api/channels/<int:channel_id>/messages', methods=['POST'])
@login_required_api
def send_message(channel_id):
    user = current_user()
    data = request.get_json() or {}
    content = data.get('content', '').strip()
    reply_to = data.get('reply_to')
    if not content:
        return jsonify({'success': False, 'error': 'Die Nachricht ist leer.'})
    if len(content) > 4000:
        return jsonify({'success': False, 'error': 'Die Nachricht ist zu lang.'})
    conn = get_db()
    channel = conn.execute('\n        SELECT *\n        FROM channels\n        WHERE id = ?\n        ', (channel_id,)).fetchone()
    if not channel:
        conn.close()
        return jsonify({'success': False})
    if not is_hub_member(channel['hub_id'], user['id']):
        conn.close()
        return (jsonify({'success': False, 'error': 'Keine Berechtigung.'}), 403)
    if channel['channel_type'] == 'announcement' and (not is_hub_admin(channel['hub_id'], user['id'])):
        conn.close()
        return (jsonify({'success': False, 'error': 'Nur Owner und Admins können in Announcements posten.'}), 403)
    cursor = conn.execute('\n        INSERT INTO messages\n        (\n            channel_id,\n            user_id,\n            content,\n            reply_to,\n            created_at\n        )\n        VALUES (?, ?, ?, ?, ?)\n        ', (channel_id, user['id'], content, reply_to, now()))
    message_id = cursor.lastrowid
    conn.commit()
    conn.close()
    add_activity(channel['hub_id'], user['id'], 'message', 'sent a message')
    return jsonify({'success': True, 'message_id': message_id})

@app.route('/api/messages/<int:message_id>', methods=['PUT'])
@login_required_api
def edit_message(message_id):
    user = current_user()
    data = request.get_json() or {}
    content = data.get('content', '').strip()
    if not content:
        return jsonify({'success': False, 'error': 'Die Nachricht ist leer.'})
    conn = get_db()
    message = conn.execute('\n        SELECT *\n        FROM messages\n        WHERE id = ?\n        ', (message_id,)).fetchone()
    if not message:
        conn.close()
        return jsonify({'success': False})
    if message['user_id'] != user['id']:
        conn.close()
        return (jsonify({'success': False, 'error': 'Du kannst nur deine eigenen Nachrichten bearbeiten.'}), 403)
    conn.execute('\n        UPDATE messages\n        SET\n            content = ?,\n            edited = 1,\n            updated_at = ?\n        WHERE id = ?\n        ', (content, now(), message_id))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/messages/<int:message_id>', methods=['DELETE'])
@login_required_api
def delete_message(message_id):
    user = current_user()
    conn = get_db()
    message = conn.execute('\n        SELECT\n            m.*,\n            c.hub_id\n        FROM messages m\n        JOIN channels c\n        ON m.channel_id = c.id\n        WHERE m.id = ?\n        ', (message_id,)).fetchone()
    if not message:
        conn.close()
        return jsonify({'success': False, 'error': 'Nachricht nicht gefunden.'})
    allowed = message['user_id'] == user['id'] or is_hub_admin(message['hub_id'], user['id'])
    if not allowed:
        conn.close()
        return (jsonify({'success': False, 'error': 'Du darfst diese Nachricht nicht löschen.'}), 403)
    conn.execute('\n        DELETE FROM messages\n        WHERE id = ?\n        ', (message_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/messages/<int:message_id>/pin', methods=['POST'])
@login_required_api
def pin_message(message_id):
    user = current_user()
    conn = get_db()
    message = conn.execute('\n        SELECT\n            m.*,\n            c.hub_id\n        FROM messages m\n        JOIN channels c\n        ON m.channel_id = c.id\n        WHERE m.id = ?\n        ', (message_id,)).fetchone()
    if not message:
        conn.close()
        return jsonify({'success': False})
    if not is_hub_admin(message['hub_id'], user['id']):
        conn.close()
        return (jsonify({'success': False, 'error': 'Nur Owner und Admins können Nachrichten anpinnen.'}), 403)
    new_value = 0 if message['pinned'] else 1
    conn.execute('\n        UPDATE messages\n        SET pinned = ?\n        WHERE id = ?\n        ', (new_value, message_id))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'pinned': bool(new_value)})

@app.route('/api/messages/<int:message_id>/reaction', methods=['POST'])
@login_required_api
def reaction(message_id):
    user = current_user()
    data = request.get_json() or {}
    emoji = data.get('emoji', '').strip()
    if not emoji:
        return jsonify({'success': False})
    conn = get_db()
    try:
        conn.execute('\n            INSERT INTO reactions\n            (\n                message_id,\n                user_id,\n                emoji\n            )\n            VALUES (?, ?, ?)\n            ', (message_id, user['id'], emoji))
    except sqlite3.IntegrityError:
        conn.execute('\n            DELETE FROM reactions\n            WHERE message_id = ?\n            AND user_id = ?\n            AND emoji = ?\n            ', (message_id, user['id'], emoji))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/invitations')
@login_required_api
def invitations():
    user = current_user()
    conn = get_db()
    rows = conn.execute("\n        SELECT\n            i.*,\n            h.name AS hub_name,\n            h.icon AS hub_icon,\n            h.icon_type,\n            u.username AS sender_username\n        FROM invitations i\n        JOIN hubs h\n        ON i.hub_id = h.id\n        JOIN users u\n        ON i.sender_id = u.id\n        WHERE i.receiver_id = ?\n        AND i.status = 'pending'\n        ORDER BY i.created_at DESC\n        ", (user['id'],)).fetchall()
    conn.close()
    return jsonify({'invitations': [dict(row) for row in rows]})

@app.route('/api/hubs/<int:hub_id>/invite', methods=['POST'])
@login_required_api
def invite_user(hub_id):
    user = current_user()
    if not is_hub_admin(hub_id, user['id']):
        return (jsonify({'success': False, 'error': 'Nur Admins können Personen einladen.'}), 403)
    data = request.get_json() or {}
    username = data.get('username', '').strip()
    conn = get_db()
    receiver = conn.execute('\n        SELECT *\n        FROM users\n        WHERE LOWER(username) = LOWER(?)\n        ', (username,)).fetchone()
    if not receiver:
        conn.close()
        return jsonify({'success': False, 'error': 'Benutzer nicht gefunden.'})
    if receiver['id'] == user['id']:
        conn.close()
        return jsonify({'success': False, 'error': 'Du bist bereits Mitglied.'})
    member = conn.execute('\n        SELECT id\n        FROM hub_members\n        WHERE hub_id = ?\n        AND user_id = ?\n        ', (hub_id, receiver['id'])).fetchone()
    if member:
        conn.close()
        return jsonify({'success': False, 'error': 'Diese Person ist bereits im Hub.'})
    invitation = conn.execute("\n        SELECT id\n        FROM invitations\n        WHERE hub_id = ?\n        AND receiver_id = ?\n        AND status = 'pending'\n        ", (hub_id, receiver['id'])).fetchone()
    if invitation:
        conn.close()
        return jsonify({'success': False, 'error': 'Es gibt bereits eine offene Einladung.'})
    conn.execute("\n        INSERT INTO invitations\n        (\n            hub_id,\n            sender_id,\n            receiver_id,\n            status,\n            created_at\n        )\n        VALUES (?, ?, ?, 'pending', ?)\n        ", (hub_id, user['id'], receiver['id'], now()))
    conn.commit()
    conn.close()
    notify(receiver['id'], 'Neue Hub-Einladung', user['username'] + ' hat dich in einen Hub eingeladen.', 'invite')
    return jsonify({'success': True})

@app.route('/api/invitations/<int:invitation_id>/<action>', methods=['POST'])
@login_required_api
def invitation_action(invitation_id, action):
    user = current_user()
    conn = get_db()
    invitation = conn.execute("\n        SELECT *\n        FROM invitations\n        WHERE id = ?\n        AND receiver_id = ?\n        AND status = 'pending'\n        ", (invitation_id, user['id'])).fetchone()
    if not invitation:
        conn.close()
        return jsonify({'success': False})
    if action == 'accept':
        conn.execute("\n            UPDATE invitations\n            SET status = 'accepted'\n            WHERE id = ?\n            ", (invitation_id,))
        conn.execute("\n            INSERT OR IGNORE INTO hub_members\n            (\n                hub_id,\n                user_id,\n                role,\n                joined_at\n            )\n            VALUES (?, ?, 'member', ?)\n            ", (invitation['hub_id'], user['id'], now()))
        result = True
    elif action == 'decline':
        conn.execute("\n            UPDATE invitations\n            SET status = 'declined'\n            WHERE id = ?\n            ", (invitation_id,))
        result = True
    else:
        result = False
    conn.commit()
    conn.close()
    return jsonify({'success': result})

@app.route('/api/hubs/<int:hub_id>/members/<int:user_id>/role', methods=['POST'])
@login_required_api
def change_role(hub_id, user_id):
    user = current_user()
    if not is_hub_owner(hub_id, user['id']):
        return (jsonify({'success': False, 'error': 'Nur der Owner kann Rollen ändern.'}), 403)
    data = request.get_json() or {}
    role = data.get('role', 'member')
    if role not in ('member', 'admin'):
        return (jsonify({'success': False, 'error': 'Ungültige Rolle.'}), 400)
    conn = get_db()
    target = conn.execute('\n        SELECT user_id, role\n        FROM hub_members\n        WHERE hub_id = ?\n        AND user_id = ?\n        ', (hub_id, user_id)).fetchone()
    if not target:
        conn.close()
        return (jsonify({'success': False, 'error': 'Mitglied nicht gefunden.'}), 404)
    if target['role'] == 'owner':
        conn.close()
        return (jsonify({'success': False, 'error': 'Der Owner kann nicht herabgestuft werden.'}), 403)
    conn.execute('\n        UPDATE hub_members\n        SET role = ?\n        WHERE hub_id = ?\n        AND user_id = ?\n        ', (role, hub_id, user_id))
    conn.commit()
    conn.close()
    notify(user_id, 'HUB-Rolle geändert', 'Deine Rolle wurde auf ' + ('Admin' if role == 'admin' else 'Member') + ' gesetzt.', 'role')
    return jsonify({'success': True})

@app.route('/api/hubs/<int:hub_id>/members/<int:user_id>', methods=['DELETE'])
@login_required_api
def remove_member(hub_id, user_id):
    user = current_user()
    if not is_hub_admin(hub_id, user['id']):
        return (jsonify({'success': False, 'error': 'Keine Berechtigung.'}), 403)
    conn = get_db()
    target = conn.execute('\n        SELECT *\n        FROM hub_members\n        WHERE hub_id = ?\n        AND user_id = ?\n        ', (hub_id, user_id)).fetchone()
    if not target:
        conn.close()
        return jsonify({'success': False})
    if target['role'] == 'owner':
        conn.close()
        return jsonify({'success': False, 'error': 'Der Besitzer kann nicht entfernt werden.'})
    if target['role'] == 'admin' and not is_hub_owner(hub_id, user['id']):
        conn.close()
        return jsonify({'success': False, 'error': 'Admins können keine anderen Admins entfernen.'}), 403
    conn.execute('\n        DELETE FROM hub_members\n        WHERE hub_id = ?\n        AND user_id = ?\n        ', (hub_id, user_id))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/hubs/<int:hub_id>', methods=['PUT'])
@login_required_api
def update_hub(hub_id):
    user = current_user()
    if not is_hub_admin(hub_id, user['id']):
        return (jsonify({'success': False, 'error': 'Keine Berechtigung.'}), 403)
    data = request.get_json() or {}
    name = data.get('name', '').strip()
    description = data.get('description', '').strip()
    color = data.get('color', '#7c5cff')
    rules = data.get('rules', '').strip()
    public = 1 if data.get('public') else 0
    conn = get_db()
    conn.execute('\n        UPDATE hubs\n        SET\n            name = ?,\n            description = ?,\n            color = ?,\n            rules = ?,\n            public = ?\n        WHERE id = ?\n        ', (name, description, color, rules, public, hub_id))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/hubs/<int:hub_id>', methods=['DELETE'])
@login_required_api
def delete_hub(hub_id):
    user = current_user()
    conn = get_db()
    hub = conn.execute('\n        SELECT *\n        FROM hubs\n        WHERE id = ?\n        AND owner_id = ?\n        ', (hub_id, user['id'])).fetchone()
    if not hub:
        conn.close()
        return (jsonify({'success': False, 'error': 'Nur der Besitzer kann den Hub löschen.'}), 403)
    conn.execute('\n        DELETE FROM hubs\n        WHERE id = ?\n        ', (hub_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/hubs/<int:hub_id>/events', methods=['GET', 'POST'])
@app.route('/api/events/<int:event_id>', methods=['DELETE'])
@login_required_api
def events(hub_id=None, event_id=None):
    user = current_user()

    if event_id is not None:
        conn = get_db()
        event = conn.execute('SELECT * FROM events WHERE id = ?', (event_id,)).fetchone()
        if not event:
            conn.close()
            return jsonify({'success': False, 'error': 'Termin nicht gefunden.'}), 404
        if not is_hub_member(event['hub_id'], user['id']):
            conn.close()
            return jsonify({'success': False, 'error': 'Keine Berechtigung.'}), 403
        role = conn.execute('SELECT role FROM hub_members WHERE hub_id = ? AND user_id = ?', (event['hub_id'], user['id'])).fetchone()
        can_delete = event['creator_id'] == user['id'] or (role and role['role'] in ('owner', 'admin'))
        if not can_delete:
            conn.close()
            return jsonify({'success': False, 'error': 'Du darfst diesen Termin nicht löschen.'}), 403
        conn.execute('DELETE FROM events WHERE id = ?', (event_id,))
        conn.commit()
        conn.close()
        return jsonify({'success': True})

    if not is_hub_member(hub_id, user['id']):
        return (jsonify({'success': False}), 403)
    if request.method == 'GET':
        conn = get_db()
        rows = conn.execute('\n            SELECT\n                e.*,\n                u.username AS creator\n            FROM events e\n            JOIN users u\n            ON e.creator_id = u.id\n            WHERE e.hub_id = ?\n            ORDER BY e.event_date\n            ', (hub_id,)).fetchall()
        conn.close()
        return jsonify({'events': [dict(row) for row in rows]})
    data = request.get_json() or {}
    title = data.get('title', '').strip()
    description = data.get('description', '').strip()
    event_date = data.get('event_date', '')
    if not title or not event_date:
        return jsonify({'success': False, 'error': 'Titel und Datum sind erforderlich.'})
    conn = get_db()
    conn.execute('\n        INSERT INTO events\n        (\n            hub_id,\n            creator_id,\n            title,\n            description,\n            event_date,\n            created_at\n        )\n        VALUES (?, ?, ?, ?, ?, ?)\n        ', (hub_id, user['id'], title, description, event_date, now()))
    conn.commit()
    conn.close()
    add_activity(hub_id, user['id'], 'event', 'created event: ' + title)
    return jsonify({'success': True})

@app.route('/api/hubs/<int:hub_id>/tasks', methods=['GET', 'POST'])
@login_required_api
def tasks(hub_id):
    user = current_user()
    if not is_hub_member(hub_id, user['id']):
        return (jsonify({'success': False}), 403)
    if request.method == 'GET':
        conn = get_db()
        rows = conn.execute('\n            SELECT\n                t.*,\n                u.username AS creator\n            FROM tasks t\n            JOIN users u\n            ON t.creator_id = u.id\n            WHERE t.hub_id = ?\n            ORDER BY t.created_at DESC\n            ', (hub_id,)).fetchall()
        conn.close()
        return jsonify({'tasks': [dict(row) for row in rows]})
    data = request.get_json() or {}
    title = data.get('title', '').strip()
    description = data.get('description', '').strip()
    if not title:
        return jsonify({'success': False, 'error': 'Ein Titel ist erforderlich.'})
    conn = get_db()
    conn.execute('\n        INSERT INTO tasks\n        (\n            hub_id,\n            creator_id,\n            title,\n            description,\n            created_at\n        )\n        VALUES (?, ?, ?, ?, ?)\n        ', (hub_id, user['id'], title, description, now()))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/tasks/<int:task_id>', methods=['PUT', 'DELETE'])
@login_required_api
def task_action(task_id):
    user = current_user()
    conn = get_db()
    task = conn.execute('\n        SELECT *\n        FROM tasks\n        WHERE id = ?\n        ', (task_id,)).fetchone()
    if not task:
        conn.close()
        return jsonify({'success': False})
    if not is_hub_member(task['hub_id'], user['id']):
        conn.close()
        return (jsonify({'success': False}), 403)
    if request.method == 'DELETE':
        role = conn.execute('SELECT role FROM hub_members WHERE hub_id = ? AND user_id = ?', (task['hub_id'], user['id'])).fetchone()
        can_delete = task['creator_id'] == user['id'] or (role and role['role'] in ('owner', 'admin'))
        if not can_delete:
            conn.close()
            return jsonify({'success': False, 'error': 'Du darfst diesen Plan nicht löschen.'}), 403
        conn.execute('\n            DELETE FROM tasks\n            WHERE id = ?\n            ', (task_id,))
    else:
        data = request.get_json() or {}
        status = data.get('status', task['status'])
        if status not in ('todo', 'doing', 'done'):
            conn.close()
            return jsonify({'success': False})
        conn.execute('\n            UPDATE tasks\n            SET status = ?\n            WHERE id = ?\n            ', (status, task_id))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/hubs/<int:hub_id>/notes', methods=['GET', 'POST'])
@app.route('/api/notes/<int:note_id>', methods=['DELETE'])
@login_required_api
def notes(hub_id=None, note_id=None):
    user = current_user()

    if note_id is not None:
        conn = get_db()
        note = conn.execute('SELECT * FROM notes WHERE id = ?', (note_id,)).fetchone()
        if not note:
            conn.close()
            return jsonify({'success': False, 'error': 'Notiz nicht gefunden.'}), 404
        if not is_hub_member(note['hub_id'], user['id']):
            conn.close()
            return jsonify({'success': False, 'error': 'Keine Berechtigung.'}), 403
        role = conn.execute('SELECT role FROM hub_members WHERE hub_id = ? AND user_id = ?', (note['hub_id'], user['id'])).fetchone()
        can_delete = note['user_id'] == user['id'] or (role and role['role'] in ('owner', 'admin'))
        if not can_delete:
            conn.close()
            return jsonify({'success': False, 'error': 'Du darfst diese Notiz nicht löschen.'}), 403
        conn.execute('DELETE FROM notes WHERE id = ?', (note_id,))
        conn.commit()
        conn.close()
        return jsonify({'success': True})

    if not is_hub_member(hub_id, user['id']):
        return (jsonify({'success': False}), 403)
    conn = get_db()
    if request.method == 'GET':
        rows = conn.execute('\n            SELECT\n                n.*,\n                u.username\n            FROM notes n\n            JOIN users u\n            ON n.user_id = u.id\n            WHERE n.hub_id = ?\n            ORDER BY n.updated_at DESC\n            ', (hub_id,)).fetchall()
        conn.close()
        return jsonify({'notes': [dict(row) for row in rows]})
    data = request.get_json() or {}
    title = data.get('title', '').strip()
    content = data.get('content', '').strip()
    if not title:
        conn.close()
        return jsonify({'success': False, 'error': 'Ein Titel ist erforderlich.'})
    conn.execute('\n        INSERT INTO notes\n        (\n            hub_id,\n            user_id,\n            title,\n            content,\n            updated_at\n        )\n        VALUES (?, ?, ?, ?, ?)\n        ', (hub_id, user['id'], title, content, now()))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/hubs/<int:hub_id>/polls', methods=['GET', 'POST'])
@app.route('/api/polls/<int:poll_id>', methods=['DELETE'])
@login_required_api
def polls(hub_id=None, poll_id=None):
    user = current_user()

    if poll_id is not None:
        conn = get_db()
        poll = conn.execute('SELECT * FROM polls WHERE id = ?', (poll_id,)).fetchone()
        if not poll:
            conn.close()
            return jsonify({'success': False, 'error': 'Umfrage nicht gefunden.'}), 404
        if not is_hub_member(poll['hub_id'], user['id']):
            conn.close()
            return jsonify({'success': False, 'error': 'Keine Berechtigung.'}), 403
        role = conn.execute('SELECT role FROM hub_members WHERE hub_id = ? AND user_id = ?', (poll['hub_id'], user['id'])).fetchone()
        can_delete = poll['user_id'] == user['id'] or (role and role['role'] in ('owner', 'admin'))
        if not can_delete:
            conn.close()
            return jsonify({'success': False, 'error': 'Du darfst diese Umfrage nicht löschen.'}), 403
        conn.execute('DELETE FROM polls WHERE id = ?', (poll_id,))
        conn.commit()
        conn.close()
        return jsonify({'success': True})

    if not is_hub_member(hub_id, user['id']):
        return (jsonify({'success': False}), 403)
    conn = get_db()
    if request.method == 'GET':
        rows = conn.execute('\n            SELECT\n                p.*,\n                u.username\n            FROM polls p\n            JOIN users u\n            ON p.user_id = u.id\n            WHERE p.hub_id = ?\n            ORDER BY p.created_at DESC\n            ', (hub_id,)).fetchall()
        result = []
        for row in rows:
            item = dict(row)
            try:
                item['options'] = row['options'].split('|')
            except Exception:
                item['options'] = []
            result.append(item)
        conn.close()
        return jsonify({'polls': result})
    data = request.get_json() or {}
    question = data.get('question', '').strip()
    options = data.get('options', [])
    options = [str(option).strip() for option in options if str(option).strip()]
    if not question or len(options) < 2:
        conn.close()
        return jsonify({'success': False, 'error': 'Frage und mindestens zwei Antworten erforderlich.'})
    conn.execute('\n        INSERT INTO polls\n        (\n            hub_id,\n            user_id,\n            question,\n            options,\n            created_at\n        )\n        VALUES (?, ?, ?, ?, ?)\n        ', (hub_id, user['id'], question, '|'.join(options), now()))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/hubs/<int:hub_id>/activity')
@login_required_api
def get_activity(hub_id):
    user = current_user()
    if not is_hub_member(hub_id, user['id']):
        return (jsonify({'success': False}), 403)
    conn = get_db()
    rows = conn.execute('\n        SELECT\n            a.*,\n            u.username,\n            u.avatar\n        FROM activity a\n        LEFT JOIN users u\n        ON a.user_id = u.id\n        WHERE a.hub_id = ?\n        ORDER BY a.created_at DESC\n        LIMIT 50\n        ', (hub_id,)).fetchall()
    conn.close()
    return jsonify({'activity': [dict(row) for row in rows]})

@app.route('/api/notifications')
@login_required_api
def get_notifications():
    user = current_user()
    conn = get_db()
    rows = conn.execute('\n        SELECT *\n        FROM notifications\n        WHERE user_id = ?\n        ORDER BY created_at DESC\n        LIMIT 50\n        ', (user['id'],)).fetchall()
    unread = conn.execute('\n        SELECT COUNT(*)\n        FROM notifications\n        WHERE user_id = ?\n        AND read = 0\n        ', (user['id'],)).fetchone()[0]
    conn.close()
    return jsonify({'notifications': [dict(row) for row in rows], 'unread': unread})

@app.route('/api/notifications/read', methods=['POST'])
@login_required_api
def mark_notifications_read():
    user = current_user()
    conn = get_db()
    conn.execute('\n        UPDATE notifications\n        SET read = 1\n        WHERE user_id = ?\n        ', (user['id'],))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/hubs/<int:hub_id>/files', methods=['POST'])
@login_required_api
def upload_file(hub_id):
    user = current_user()
    if not is_hub_member(hub_id, user['id']):
        return (jsonify({'success': False}), 403)
    uploaded = request.files.get('file')
    if not uploaded or not uploaded.filename:
        return jsonify({'success': False, 'error': 'Keine Datei ausgewählt.'})
    filename = secure_filename(uploaded.filename)
    stored_name = str(int(datetime.now().timestamp() * 1000)) + '_' + filename
    uploaded.save(os.path.join(UPLOAD_FOLDER, stored_name))
    conn = get_db()
    conn.execute('\n        INSERT INTO files\n        (\n            hub_id,\n            user_id,\n            filename,\n            stored_name,\n            created_at\n        )\n        VALUES (?, ?, ?, ?, ?)\n        ', (hub_id, user['id'], filename, stored_name, now()))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/hubs/<int:hub_id>/files')
@login_required_api
def list_files(hub_id):
    user = current_user()
    if not is_hub_member(hub_id, user['id']):
        return (jsonify({'success': False}), 403)
    conn = get_db()
    rows = conn.execute('\n        SELECT\n            f.*,\n            u.username\n        FROM files f\n        JOIN users u\n        ON f.user_id = u.id\n        WHERE f.hub_id = ?\n        ORDER BY f.created_at DESC\n        ', (hub_id,)).fetchall()
    conn.close()
    result = []
    for row in rows:
        item = dict(row)
        item['url'] = '/static/uploads/hubs/' + row['stored_name']
        result.append(item)
    return jsonify({'files': result})

@app.route('/api/search')
@login_required_api
def global_search():
    user = current_user()
    query = request.args.get('q', '').strip()
    if len(query) < 2:
        return jsonify({'users': [], 'hubs': [], 'messages': []})
    conn = get_db()
    users = conn.execute('\n        SELECT id, username, avatar, bio\n        FROM users\n        WHERE LOWER(username)\n        LIKE LOWER(?)\n        AND id != ?\n        LIMIT 10\n        ', ('%' + query + '%', user['id'])).fetchall()
    hubs = conn.execute('\n        SELECT\n            h.id,\n            h.name,\n            h.description,\n            h.icon,\n            h.icon_type,\n            h.public\n        FROM hubs h\n        WHERE\n            (\n                h.public = 1\n                OR EXISTS (\n                    SELECT 1\n                    FROM hub_members hm\n                    WHERE hm.hub_id = h.id\n                    AND hm.user_id = ?\n                )\n            )\n        AND\n            (\n                LOWER(h.name)\n                LIKE LOWER(?)\n                OR\n                LOWER(h.description)\n                LIKE LOWER(?)\n            )\n        LIMIT 10\n        ', (user['id'], '%' + query + '%', '%' + query + '%')).fetchall()
    messages = conn.execute('\n        SELECT\n            m.id,\n            m.content,\n            m.channel_id,\n            c.name AS channel_name,\n            c.hub_id,\n            h.name AS hub_name,\n            u.username\n        FROM messages m\n        JOIN channels c\n        ON m.channel_id = c.id\n        JOIN hubs h\n        ON c.hub_id = h.id\n        JOIN users u\n        ON m.user_id = u.id\n        JOIN hub_members hm\n        ON hm.hub_id = h.id\n        AND hm.user_id = ?\n        WHERE LOWER(m.content)\n        LIKE LOWER(?)\n        ORDER BY m.created_at DESC\n        LIMIT 20\n        ', (user['id'], '%' + query + '%')).fetchall()
    conn.close()
    return jsonify({'users': [dict(item) for item in users], 'hubs': [dict(item) for item in hubs], 'messages': [dict(item) for item in messages]})

@app.route('/api/discover')
@login_required_api
def discover():
    conn = get_db()
    hubs = conn.execute('\n        SELECT\n            h.*,\n            u.username AS owner,\n            (\n                SELECT COUNT(*)\n                FROM hub_members hm\n                WHERE hm.hub_id = h.id\n            ) AS member_count\n        FROM hubs h\n        JOIN users u\n        ON h.owner_id = u.id\n        WHERE h.public = 1\n        ORDER BY member_count DESC, h.created_at DESC\n        LIMIT 50\n        ').fetchall()
    conn.close()
    return jsonify({'hubs': [dict(hub) for hub in hubs]})

@app.route('/api/hubs/<int:hub_id>/invite-link', methods=['POST'])
@login_required_api
def create_invite_link(hub_id):
    user = current_user()
    if not is_hub_admin(hub_id, user['id']):
        return (jsonify({'success': False, 'error': 'Keine Berechtigung.'}), 403)
    import secrets
    code = secrets.token_urlsafe(8)
    conn = get_db()
    conn.execute('\n        INSERT INTO hub_invite_links\n        (\n            hub_id,\n            code,\n            created_at\n        )\n        VALUES (?, ?, ?)\n        ', (hub_id, code, now()))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'code': code})

@app.route('/api/hubs/join/<code>', methods=['POST'])
@login_required_api
def join_by_link(code):
    user = current_user()
    conn = get_db()
    link = conn.execute('\n        SELECT *\n        FROM hub_invite_links\n        WHERE code = ?\n        ', (code,)).fetchone()
    if not link:
        conn.close()
        return jsonify({'success': False, 'error': 'Einladungslink ist ungültig.'})
    conn.execute("\n        INSERT OR IGNORE INTO hub_members\n        (\n            hub_id,\n            user_id,\n            role,\n            joined_at\n        )\n        VALUES (?, ?, 'member', ?)\n        ", (link['hub_id'], user['id'], now()))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'hub_id': link['hub_id']})
if __name__ == '__main__':
    init_db()
    app.run(host='127.0.0.1', port=5000, debug=True)
