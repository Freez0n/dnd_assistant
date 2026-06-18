import json
import os
import bcrypt
from datetime import datetime
from app.database import DatabaseManager
from app.utils.seed_data import seed_new_user_data

SESSION_FILE = "local_session.json"

def register_user(db: DatabaseManager, username: str, password: str) -> dict:
    try:
        existing = db.fetchone("SELECT id FROM `users` WHERE username = %s", (username,))
        if existing:
            return {'success': False, 'error': 'Имя пользователя уже занято'}
            
        pwd_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        user_id = db.create_user(username, pwd_hash)
        
        seed_new_user_data(db.host, db.user, db.password, db.database_name, user_id)
        
        return {'success': True, 'user_id': user_id}
    except Exception as e:
        return {'success': False, 'error': f'Ошибка регистрации: {str(e)}'}

def login_user(db: DatabaseManager, username: str, password: str) -> dict:
    try:
        user = db.get_user_by_username(username)
        if not user: 
            return {'success': False, 'error': 'Неверный логин или пароль'}
        
        if bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
            save_session(user['id'])
            return {'success': True, 'user': user}
            
        return {'success': False, 'error': 'Неверный логин или пароль'}
    except Exception as e:
        return {'success': False, 'error': f'Ошибка входа: {str(e)}'}

def change_password(db: DatabaseManager, user_id: int, old_pass: str, new_pass: str) -> dict:
    try:
        user = db.fetchone("SELECT password_hash FROM `users` WHERE id = %s", (user_id,))
        if not user or not bcrypt.checkpw(old_pass.encode('utf-8'), user['password_hash'].encode('utf-8')):
            return {'success': False, 'error': 'Неверный текущий пароль'}
            
        new_hash = bcrypt.hashpw(new_pass.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        db.update_password(user_id, new_hash)
        return {'success': True}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def save_session(user_id: int):
    data = {"user_id": user_id, "timestamp": datetime.now().isoformat()}
    with open(SESSION_FILE, "w") as f: 
        json.dump(data, f)

def load_session(db: DatabaseManager) -> int:
    if os.path.exists(SESSION_FILE):
        try:
            with open(SESSION_FILE, "r") as f:
                data = json.load(f)
                uid = data.get('user_id')
                if uid and db.fetchone("SELECT id FROM `users` WHERE id = %s", (uid,)):
                    return uid
        except: pass
    return None

def clear_session():
    if os.path.exists(SESSION_FILE): 
        os.remove(SESSION_FILE)