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
        
        # Check if table exists and recreate with correct structure
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='accounts'")
        table_exists = cursor.fetchone()
        
        if table_exists:
            # Check current structure
            cursor.execute("PRAGMA table_info(accounts)")
            columns = cursor.fetchall()
            column_names = [col[1] for col in columns]
            
            # Add missing columns
            if 'token_signin' not in column_names:
                cursor.execute('ALTER TABLE accounts ADD COLUMN token_signin TEXT')
            if 'version_code' not in column_names:
                cursor.execute('ALTER TABLE accounts ADD COLUMN version_code INTEGER DEFAULT 187')
            if 'android' not in column_names:
                cursor.execute('ALTER TABLE accounts ADD COLUMN android INTEGER DEFAULT 29')
            if 'device' not in column_names:
                cursor.execute('ALTER TABLE accounts ADD COLUMN device TEXT DEFAULT ""')
            if 'locale' not in column_names:
                cursor.execute('ALTER TABLE accounts ADD COLUMN locale TEXT DEFAULT "VN"')
            if 'device_token' not in column_names:
                cursor.execute('ALTER TABLE accounts ADD COLUMN device_token TEXT DEFAULT ""')
        else:
            # Create new table with correct structure
            cursor.execute('''
                CREATE TABLE accounts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    token_signin TEXT NOT NULL,
                    token TEXT,
                    version_code INTEGER DEFAULT 187,
                    android INTEGER DEFAULT 29,
                    device TEXT DEFAULT '',
                    locale TEXT DEFAULT 'VN',
                    device_token TEXT DEFAULT '',
                    email TEXT,
                    coin INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'Inactive',
                    proxy TEXT DEFAULT '',
                    delay INTEGER DEFAULT 5,
                    config TEXT DEFAULT '{}',
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
    
    def add_account(self, name, token_signin, version_code=187, android=29, device="", locale="VN", device_token="", proxy="", delay=5, config=None):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        encrypted_token_signin = self.encrypt_data(token_signin)
        config_json = json.dumps(config) if config else "{}"
        
        cursor.execute('''
            INSERT INTO accounts (name, token_signin, version_code, android, device, locale, device_token, proxy, delay, config)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (name, encrypted_token_signin, version_code, android, device, locale, device_token, proxy, delay, config_json))
        
        conn.commit()
        account_id = cursor.lastrowid
        conn.close()
        return account_id
    
    def get_all_accounts(self):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        # First, check the current structure of the table
        cursor.execute("PRAGMA table_info(accounts)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        cursor.execute('SELECT * FROM accounts ORDER BY id')
        accounts = cursor.fetchall()
        conn.close()
        
        result = []
        for account in accounts:
            try:
                # Create a dictionary mapping column names to values
                account_data = dict(zip(column_names, account))
                
                # Handle token_signin (might be encrypted or None)
                token_signin = account_data.get('token_signin', '')
                if token_signin:
                    try:
                        token_signin = self.decrypt_data(token_signin)
                    except:
                        token_signin = ''
                else:
                    token_signin = ''
                
                # Handle config field (might be string, None, or already JSON)
                config_data = account_data.get('config', '{}')
                if config_data:
                    try:
                        if isinstance(config_data, str):
                            config = json.loads(config_data)
                        else:
                            config = {}
                    except:
                        config = {}
                else:
                    config = {}
                
                account_dict = {
                    'id': account_data.get('id', 0),
                    'name': account_data.get('name', ''),
                    'token_signin': token_signin,
                    'token': account_data.get('token', ''),
                    'version_code': account_data.get('version_code', 187),
                    'android': account_data.get('android', 29),
                    'device': account_data.get('device', ''),
                    'locale': account_data.get('locale', 'VN'),
                    'device_token': account_data.get('device_token', ''),
                    'email': account_data.get('email', None),
                    'coin': account_data.get('coin', 0),
                    'status': account_data.get('status', 'Inactive'),
                    'proxy': account_data.get('proxy', ''),
                    'delay': account_data.get('delay', 5),
                    'config': config,
                    'created_at': account_data.get('created_at', None),
                    'last_run': account_data.get('last_run', None),
                    'total_videos': account_data.get('total_videos', 0),
                    'total_coins': account_data.get('total_coins', 0)
                }
                result.append(account_dict)
            except Exception as e:
                print(f"Error processing account {account[0] if account else 'unknown'}: {e}")
                continue
        
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
    
    def update_account(self, account_id, name, token_signin, version_code=187, android=29, device="", locale="VN", device_token="", proxy="", delay=5, config=None):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        encrypted_token_signin = self.encrypt_data(token_signin)
        config_json = json.dumps(config) if config else "{}"
        
        cursor.execute('''
            UPDATE accounts 
            SET name = ?, token_signin = ?, version_code = ?, android = ?, device = ?, locale = ?, device_token = ?, proxy = ?, delay = ?, config = ?
            WHERE id = ?
        ''', (name, encrypted_token_signin, version_code, android, device, locale, device_token, proxy, delay, config_json, account_id))
        
        conn.commit()
        conn.close()
    
    def update_account_token(self, account_id, token):
        """Update the main token after successful sign-in"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE accounts 
            SET token = ?
            WHERE id = ?
        ''', (token, account_id))
        conn.commit()
        conn.close()
