import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import requests
import threading
import time

class ProxyManager:
    def __init__(self, parent, db_manager):
        self.parent = parent
        self.db = db_manager
        
        self.window = tk.Toplevel(parent)
        self.window.title("Proxy Manager")
        self.window.geometry("800x600")
        self.window.transient(parent)
        self.window.grab_set()
        
        self.setup_ui()
        self.load_proxies()
    
    def setup_ui(self):
        # Main frame
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Control buttons
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(control_frame, text="Import from File", command=self.import_proxies).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(control_frame, text="Convert Format", command=self.convert_proxy_format).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(control_frame, text="Test All Proxies", command=self.test_all_proxies).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(control_frame, text="Auto Assign", command=self.auto_assign_proxies).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(control_frame, text="Clear All", command=self.clear_all_proxies).pack(side=tk.LEFT)
        
        # Format info
        info_frame = ttk.Frame(main_frame)
        info_frame.pack(fill=tk.X, pady=(0, 10))
        
        info_text = "Supported formats:\n" \
                   "• http://ip:port\n" \
                   "• http://username:password@ip:port\n" \
                   "• ip:port:username:password\n" \
                   "• ip:username:password:port"
        
        ttk.Label(info_frame, text=info_text, font=('TkDefaultFont', 8), justify=tk.LEFT).pack(side=tk.LEFT)
        
        # Proxy list
        list_frame = ttk.Frame(main_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        # Proxy input
        input_frame = ttk.Frame(list_frame)
        input_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(input_frame, text="Add Proxy:").pack(side=tk.LEFT)
        self.proxy_entry = ttk.Entry(input_frame, width=50)
        self.proxy_entry.pack(side=tk.LEFT, padx=(5, 5), fill=tk.X, expand=True)
        ttk.Button(input_frame, text="Add", command=self.add_proxy).pack(side=tk.LEFT)
        
        # Proxy text area
        self.proxy_text = scrolledtext.ScrolledText(list_frame, height=15)
        self.proxy_text.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Status frame
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill=tk.X)
        
        self.status_label = ttk.Label(status_frame, text="Ready")
        self.status_label.pack(side=tk.LEFT)
        
        self.progress_bar = ttk.Progressbar(status_frame, mode='determinate')
        self.progress_bar.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(10, 0))
    
    def load_proxies(self):
        # Load existing proxies from accounts
        accounts = self.db.get_all_accounts()
        proxy_list = []
        for account in accounts:
            if account['proxy']:
                proxy_list.append(f"{account['name']}: {account['proxy']}")
        
        if proxy_list:
            self.proxy_text.insert(tk.END, "\n".join(proxy_list))
    
    def parse_proxy(self, proxy_string):
        """
        Convert various proxy formats to standard http://username:password@ip:port format
        Supported formats:
        - http://ip:port
        - http://username:password@ip:port 
        - ip:port:username:password
        - ip:username:password:port
        - username:password@ip:port
        """
        proxy_string = proxy_string.strip()
        
        # Already in correct format
        if proxy_string.startswith(('http://', 'https://', 'socks5://')):
            return proxy_string
        
        parts = proxy_string.split(':')
        
        if len(parts) == 2:
            # Format: ip:port
            ip, port = parts
            return f"http://{ip}:{port}"
        
        elif len(parts) == 4:
            # Format: ip:port:username:password or ip:username:password:port
            ip = parts[0]
            
            # Try to determine if second part is port or username
            try:
                port = int(parts[1])
                username = parts[2]
                password = parts[3]
                # Format: ip:port:username:password
                return f"http://{username}:{password}@{ip}:{port}"
            except ValueError:
                # Format: ip:username:password:port
                username = parts[1]
                password = parts[2]
                port = parts[3]
                return f"http://{username}:{password}@{ip}:{port}"
        
        elif len(parts) == 3:
            # Format: ip:username:password (assuming default port 8080)
            ip, username, password = parts
            return f"http://{username}:{password}@{ip}:8080"
        
        elif '@' in proxy_string:
            # Format: username:password@ip:port
            auth_part, server_part = proxy_string.split('@')
            return f"http://{auth_part}@{server_part}"
        
        # Return original if can't parse
        return proxy_string
    
    def convert_proxy_format(self):
        proxy_text = self.proxy_text.get(1.0, tk.END).strip()
        if not proxy_text:
            messagebox.showwarning("Warning", "No proxies to convert!")
            return
        
        lines = proxy_text.split('\n')
        converted_proxies = []
        
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#'):  # Skip comments
                # Skip account assignments (lines with account names)
                if ':' in line and ' ' in line.split(':')[0]:
                    converted_proxies.append(line)  # Keep account assignments as is
                else:
                    converted = self.parse_proxy(line)
                    converted_proxies.append(converted)
            elif line:
                converted_proxies.append(line)  # Keep empty lines and comments
        
        # Replace content
        self.proxy_text.delete(1.0, tk.END)
        self.proxy_text.insert(1.0, '\n'.join(converted_proxies))
        
        messagebox.showinfo("Success", "Proxy formats converted!")
    
    def add_proxy(self):
        proxy = self.proxy_entry.get().strip()
        if proxy:
            # Auto-convert format
            converted_proxy = self.parse_proxy(proxy)
            self.proxy_text.insert(tk.END, converted_proxy + "\n")
            self.proxy_entry.delete(0, tk.END)
    
    def import_proxies(self):
        file_path = filedialog.askopenfilename(
            title="Select Proxy File",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    proxies = f.read()
                self.proxy_text.insert(tk.END, proxies)
                messagebox.showinfo("Success", "Proxies imported successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to import proxies: {str(e)}")
    
    def test_all_proxies(self):
        proxy_text = self.proxy_text.get(1.0, tk.END).strip()
        if not proxy_text:
            messagebox.showwarning("Warning", "No proxies to test!")
            return
        
        proxies = [line.strip() for line in proxy_text.split('\n') if line.strip()]
        if not proxies:
            return
        
        self.progress_bar.config(maximum=len(proxies))
        self.status_label.config(text="Testing proxies...")
        
        def test_proxies():
            working_proxies = []
            failed_proxies = []
            
            for i, proxy in enumerate(proxies):
                # Skip lines that are account assignments
                if ':' in proxy and ' ' in proxy.split(':')[0]:
                    continue
                    
                try:
                    proxy_dict = {'http': proxy, 'https': proxy}
                    response = requests.get('http://httpbin.org/ip', proxies=proxy_dict, timeout=5)
                    if response.status_code == 200:
                        working_proxies.append(proxy)
                    else:
                        failed_proxies.append(proxy)
                except:
                    failed_proxies.append(proxy)
                
                self.progress_bar.config(value=i + 1)
                self.window.update()
            
            # Update UI in main thread
            self.window.after(0, lambda: self.show_test_results(working_proxies, failed_proxies))
        
        threading.Thread(target=test_proxies, daemon=True).start()
    
    def show_test_results(self, working, failed):
        self.progress_bar.config(value=0)
        self.status_label.config(text="Test completed")
        
        result_msg = f"Proxy Test Results:\n\n"
        result_msg += f"✅ Working: {len(working)}\n"
        result_msg += f"❌ Failed: {len(failed)}\n\n"
        
        if working:
            result_msg += "Working Proxies:\n" + "\n".join(working[:10])  # Show first 10
            if len(working) > 10:
                result_msg += f"\n... and {len(working) - 10} more"
        
        messagebox.showinfo("Test Results", result_msg)
    
    def auto_assign_proxies(self):
        proxy_text = self.proxy_text.get(1.0, tk.END).strip()
        if not proxy_text:
            messagebox.showwarning("Warning", "No proxies available!")
            return
        
        # Extract clean proxy URLs and convert formats
        proxies = []
        for line in proxy_text.split('\n'):
            line = line.strip()
            if line and not line.startswith('#'):
                # Skip account assignments (lines with account names)
                if ':' in line and ' ' in line.split(':')[0]:
                    continue
                converted_proxy = self.parse_proxy(line)
                proxies.append(converted_proxy)
        
        if not proxies:
            messagebox.showwarning("Warning", "No valid proxies found!")
            return
        
        accounts = self.db.get_all_accounts()
        if not accounts:
            messagebox.showwarning("Warning", "No accounts found!")
            return
        
        # Assign proxies to accounts
        assigned = 0
        for i, account in enumerate(accounts):
            if i < len(proxies):
                proxy = proxies[i % len(proxies)]  # Cycle through proxies
                self.db.update_account(
                    account['id'],
                    account['name'],
                    account['token'],
                    proxy,
                    account['delay'],
                    account['config']
                )
                assigned += 1
        
        messagebox.showinfo("Success", f"Assigned proxies to {assigned} accounts!")
        self.window.destroy()
    
    def clear_all_proxies(self):
        if messagebox.askyesno("Confirm", "Clear all proxies from accounts?"):
            accounts = self.db.get_all_accounts()
            for account in accounts:
                self.db.update_account(
                    account['id'],
                    account['name'],
                    account['token'],
                    "",  # Clear proxy
                    account['delay'],
                    account['config']
                )
            messagebox.showinfo("Success", "All proxies cleared!")
            self.window.destroy()
