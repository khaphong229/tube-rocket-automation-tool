import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import time
import sys
import os
from datetime import datetime

# Add path for bundled resources when running as exe
if getattr(sys, 'frozen', False):
    # Running as compiled exe
    application_path = sys._MEIPASS
else:
    # Running as script
    application_path = os.path.dirname(os.path.abspath(__file__))

# Add application path to sys.path to find modules
sys.path.insert(0, application_path)

try:
    from database import DatabaseManager
    from account_dialog import AccountDialog
    from tuberocket_worker import TubeRocketWorker
    from proxy_manager import ProxyManager
except ImportError as e:
    messagebox.showerror("Import Error", f"Failed to import modules: {e}")
    sys.exit(1)

class TubeRocketGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("TubeRocket Multi-Account Manager")
        self.root.geometry("1200x800")
        
        self.db = DatabaseManager()
        self.workers = {}
        self.stop_events = {}
        
        self.setup_ui()
        self.refresh_accounts()
    
    def setup_ui(self):
        # Create main container
        main_container = ttk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create vertical paned window
        main_paned = ttk.PanedWindow(main_container, orient=tk.VERTICAL)
        main_paned.pack(fill=tk.BOTH, expand=True)
        
        # Top panel - Account management
        top_frame = ttk.Frame(main_paned)
        main_paned.add(top_frame, weight=3)
        
        # Account controls
        control_frame = ttk.Frame(top_frame)
        control_frame.pack(fill=tk.X, padx=5, pady=(5, 10))
        
        ttk.Button(control_frame, text="Add Account", command=self.add_account).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(control_frame, text="Edit Account", command=self.edit_account).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(control_frame, text="Delete Account", command=self.delete_account).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(control_frame, text="Proxy Manager", command=self.open_proxy_manager).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(control_frame, text="Refresh", command=self.refresh_accounts).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Separator(control_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
        ttk.Button(control_frame, text="Start Selected", command=self.start_selected).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(control_frame, text="Stop Selected", command=self.stop_selected).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(control_frame, text="Start All", command=self.start_all).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(control_frame, text="Stop All", command=self.stop_all).pack(side=tk.LEFT)
        
        # Accounts treeview
        tree_frame = ttk.Frame(top_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=5)
        
        columns = ('ID', 'Name', 'Email', 'Coins', 'Status', 'Videos', 'Total Coins', 'Token Status', 'Last Run')
        self.accounts_tree = ttk.Treeview(tree_frame, columns=columns, show='headings', selectmode='extended')
        
        # Configure columns
        self.accounts_tree.heading('ID', text='ID')
        self.accounts_tree.heading('Name', text='Name')
        self.accounts_tree.heading('Email', text='Email')
        self.accounts_tree.heading('Coins', text='Current Coins')
        self.accounts_tree.heading('Status', text='Status')
        self.accounts_tree.heading('Videos', text='Videos')
        self.accounts_tree.heading('Total Coins', text='Total Coins')
        self.accounts_tree.heading('Token Status', text='Token')
        self.accounts_tree.heading('Last Run', text='Last Run')
        
        self.accounts_tree.column('ID', width=50)
        self.accounts_tree.column('Name', width=120)
        self.accounts_tree.column('Email', width=150)
        self.accounts_tree.column('Coins', width=100)
        self.accounts_tree.column('Status', width=120)
        self.accounts_tree.column('Videos', width=80)
        self.accounts_tree.column('Total Coins', width=100)
        self.accounts_tree.column('Token Status', width=80)
        self.accounts_tree.column('Last Run', width=130)
        
        # Scrollbars for treeview
        tree_scroll_y = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.accounts_tree.yview)
        tree_scroll_x = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=self.accounts_tree.xview)
        self.accounts_tree.configure(yscrollcommand=tree_scroll_y.set, xscrollcommand=tree_scroll_x.set)
        
        self.accounts_tree.grid(row=0, column=0, sticky='nsew')
        tree_scroll_y.grid(row=0, column=1, sticky='ns')
        tree_scroll_x.grid(row=1, column=0, sticky='ew')
        
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        # Bottom panel - Logs (smaller)
        bottom_frame = ttk.Frame(main_paned)
        main_paned.add(bottom_frame, weight=1)
        
        # Log controls
        log_control_frame = ttk.Frame(bottom_frame)
        log_control_frame.pack(fill=tk.X, padx=5, pady=(5, 5))
        
        ttk.Label(log_control_frame, text="Activity Logs:", font=('TkDefaultFont', 9, 'bold')).pack(side=tk.LEFT)
        ttk.Button(log_control_frame, text="Clear Logs", command=self.clear_logs).pack(side=tk.RIGHT)
        
        # Log text area (smaller height)
        self.log_text = scrolledtext.ScrolledText(bottom_frame, height=8, state=tk.DISABLED, font=('Consolas', 8))
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=(0, 5))
        
        # Status bar
        self.status_bar = ttk.Label(self.root, text="Ready", relief=tk.SUNKEN)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def refresh_accounts(self):
        # Clear existing items
        for item in self.accounts_tree.get_children():
            self.accounts_tree.delete(item)
        
        # Load accounts from database
        accounts = self.db.get_all_accounts()
        for account in accounts:
            last_run = account['last_run'] if account['last_run'] else 'Never'
            if last_run != 'Never':
                try:
                    last_run = datetime.fromisoformat(last_run.replace('Z', '+00:00')).strftime('%Y-%m-%d %H:%M')
                except:
                    pass
            
            # Check token status
            token_status = "✅ Ready" if account.get('token') else "❌ No Token"
            
            self.accounts_tree.insert('', tk.END, values=(
                account['id'],
                account['name'],
                account['email'] or 'Unknown',
                account['coin'],
                account['status'],
                account['total_videos'],
                account['total_coins'],
                token_status,
                last_run
            ))
        
        self.status_bar.config(text=f"Loaded {len(accounts)} accounts")
    
    def add_account(self):
        dialog = AccountDialog(self.root)
        self.root.wait_window(dialog.dialog)
        
        if dialog.result:
            try:
                self.db.add_account(
                    dialog.result['name'],
                    dialog.result['token_signin'],
                    dialog.result['version_code'],
                    dialog.result['android'],
                    dialog.result['device'],
                    dialog.result['locale'],
                    dialog.result['device_token'],
                    dialog.result['proxy'],
                    dialog.result['delay'],
                    dialog.result['config']
                )
                self.refresh_accounts()
                self.log_message(f"Added account: {dialog.result['name']}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to add account: {str(e)}")
    
    def edit_account(self):
        selected = self.accounts_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select an account to edit!")
            return
        
        account_id = self.accounts_tree.item(selected[0])['values'][0]
        accounts = self.db.get_all_accounts()
        account_data = next((acc for acc in accounts if acc['id'] == account_id), None)
        
        if account_data:
            dialog = AccountDialog(self.root, account_data)
            self.root.wait_window(dialog.dialog)
            
            if dialog.result:
                try:
                    self.db.update_account(
                        account_id,
                        dialog.result['name'],
                        dialog.result['token_signin'],
                        dialog.result['version_code'],
                        dialog.result['android'],
                        dialog.result['device'],
                        dialog.result['locale'],
                        dialog.result['device_token'],
                        dialog.result['proxy'],
                        dialog.result['delay'],
                        dialog.result['config']
                    )
                    self.refresh_accounts()
                    self.log_message(f"Updated account: {dialog.result['name']}")
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to update account: {str(e)}")
    
    def delete_account(self):
        selected = self.accounts_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select an account to delete!")
            return
        
        if messagebox.askyesno("Confirm", "Are you sure you want to delete the selected account(s)?"):
            for item in selected:
                account_id = self.accounts_tree.item(item)['values'][0]
                account_name = self.accounts_tree.item(item)['values'][1]
                
                # Stop worker if running
                if account_id in self.workers:
                    self.stop_worker(account_id)
                
                self.db.delete_account(account_id)
                self.log_message(f"Deleted account: {account_name}")
            
            self.refresh_accounts()
    
    def start_selected(self):
        selected = self.accounts_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select accounts to start!")
            return
        
        for item in selected:
            account_id = self.accounts_tree.item(item)['values'][0]
            self.start_worker(account_id)
    
    def stop_selected(self):
        selected = self.accounts_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select accounts to stop!")
            return
        
        for item in selected:
            account_id = self.accounts_tree.item(item)['values'][0]
            self.stop_worker(account_id)
    
    def start_all(self):
        accounts = self.db.get_all_accounts()
        for account in accounts:
            self.start_worker(account['id'])
    
    def stop_all(self):
        for account_id in list(self.workers.keys()):
            self.stop_worker(account_id)
    
    def start_worker(self, account_id):
        if account_id in self.workers and self.workers[account_id].is_alive():
            return  # Already running
        
        accounts = self.db.get_all_accounts()
        account_data = next((acc for acc in accounts if acc['id'] == account_id), None)
        
        if account_data:
            stop_event = threading.Event()
            worker = TubeRocketWorker(account_data, self.worker_callback, stop_event)
            
            self.workers[account_id] = worker
            self.stop_events[account_id] = stop_event
            
            worker.start()
            self.log_message(f"Started worker for account: {account_data['name']}")
    
    def stop_worker(self, account_id):
        if account_id in self.stop_events:
            self.stop_events[account_id].set()
        
        if account_id in self.workers:
            del self.workers[account_id]
        
        if account_id in self.stop_events:
            del self.stop_events[account_id]
        
        # Update status in database
        self.db.update_account_status(account_id, "Stopped")
        self.refresh_accounts()
    
    def worker_callback(self, account_id, callback_type, data):
        if callback_type == 'log':
            self.log_message(f"[ID:{account_id}] {data}")
        elif callback_type == 'status':
            self.db.update_account_status(account_id, data['status'], data.get('email'), data.get('coin'))
            self.root.after(0, self.refresh_accounts)
        elif callback_type == 'stats':
            self.db.update_account_stats(account_id, data['videos'], data['coins'])
        elif callback_type == 'update_token':
            self.db.update_account_token(account_id, data)
            self.log_message(f"[ID:{account_id}] Updated real token from sign-in")
    
    def log_message(self, message):
        self.log_text.config(state=tk.NORMAL)
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
    
    def clear_logs(self):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)
    
    def open_proxy_manager(self):
        ProxyManager(self.root, self.db)

def main():
    root = tk.Tk()
    app = TubeRocketGUI(root)
    
    def on_closing():
        app.stop_all()
        time.sleep(1)  # Give workers time to stop
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()
