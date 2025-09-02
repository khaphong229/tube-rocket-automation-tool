import sqlite3
import json
from cryptography.fernet import Fernet
import os
import base64

class DatabaseManager:
    def __init__(self, db_file="accounts.db"):
        self.db_file = db_file
        self.key_file = "encryption.key"
        self.cipher = self._get_cipher()
        self.init_database()
    
    def _get_cipher(self):
        if os.path.exists(self.key_file):
            with open(self.key_file, 'rb') as f:
                key = f.read()
        else:
            key = Fernet.generate_key()
            with open(self.key_file, 'wb') as f:
                f.write(key)
        return Fernet(key)
    
    def init_database(self):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                token TEXT NOT NULL,
                email TEXT,
                coin INTEGER DEFAULT 0,
                status TEXT DEFAULT 'Inactive',
                proxy TEXT,
                delay INTEGER DEFAULT 5,
                config TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_run TIMESTAMP,
                total_videos INTEGER DEFAULT 0,
                total_coins INTEGER DEFAULT 0
            )
        ''')
        conn.commit()
        conn.close()
    
    def encrypt_data(self, data):
        return self.cipher.encrypt(data.encode()).decode()
    
    def decrypt_data(self, encrypted_data):
        return self.cipher.decrypt(encrypted_data.encode()).decode()
    
    def add_account(self, name, token, proxy="", delay=5, config=None):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        encrypted_token = self.encrypt_data(token)
        config_json = json.dumps(config) if config else "{}"
        
        cursor.execute('''
            INSERT INTO accounts (name, token, proxy, delay, config)
            VALUES (?, ?, ?, ?, ?)
        ''', (name, encrypted_token, proxy, delay, config_json))
        
        conn.commit()
        account_id = cursor.lastrowid
        conn.close()
        return account_id
    
    def get_all_accounts(self):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM accounts ORDER BY id')
        accounts = cursor.fetchall()
        conn.close()
        
        result = []
        for account in accounts:
            account_dict = {
                'id': account[0],
                'name': account[1],
                'token': self.decrypt_data(account[2]),
                'email': account[3],
                'coin': account[4],
                'status': account[5],
                'proxy': account[6],
                'delay': account[7],
                'config': json.loads(account[8]) if account[8] else {},
                'created_at': account[9],
                'last_run': account[10],
                'total_videos': account[11],
                'total_coins': account[12]
            }
            result.append(account_dict)
        return result
    
    def update_account_status(self, account_id, status, email=None, coin=None):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        if email and coin is not None:
            cursor.execute('''
                UPDATE accounts 
                SET status = ?, email = ?, coin = ?, last_run = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (status, email, coin, account_id))
        else:
            cursor.execute('''
                UPDATE accounts 
                SET status = ?, last_run = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (status, account_id))
        
        conn.commit()
        conn.close()
    
    def update_account_stats(self, account_id, videos_count, total_coins):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE accounts 
            SET total_videos = total_videos + ?, total_coins = ?
            WHERE id = ?
        ''', (videos_count, total_coins, account_id))
        conn.commit()
        conn.close()
    
    def delete_account(self, account_id):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM accounts WHERE id = ?', (account_id,))
        conn.commit()
        conn.close()
    
    def update_account(self, account_id, name, token, proxy="", delay=5, config=None):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        encrypted_token = self.encrypt_data(token)
        config_json = json.dumps(config) if config else "{}"
        
        cursor.execute('''
            UPDATE accounts 
            SET name = ?, token = ?, proxy = ?, delay = ?, config = ?
            WHERE id = ?
        ''', (name, encrypted_token, proxy, delay, config_json, account_id))
        
        conn.commit()
        conn.close()
