import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import time
import sys
import os
from datetime import datetime
import json
from tkinter import filedialog

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
    from export_dialog import ExportDialog
    from import_dialog import ImportDialog
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
        ttk.Button(control_frame, text="Export Accounts", command=self.export_accounts).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(control_frame, text="Import Accounts", command=self.import_accounts).pack(side=tk.LEFT, padx=(0, 5))
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
        
        # Configure colors for different status
        self.setup_status_colors()
        
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
    
    def setup_status_colors(self):
        """Setup color tags for different account statuses"""
        # Configure tags for different statuses
        self.accounts_tree.tag_configure('running', background='#E8F5E8', foreground='#2E7D32')      # Light green
        self.accounts_tree.tag_configure('connecting', background='#FFF3E0', foreground='#F57C00')   # Light orange
        self.accounts_tree.tag_configure('waiting', background='#FFFDE7', foreground='#F9A825')      # Light yellow
        self.accounts_tree.tag_configure('error', background='#FFEBEE', foreground='#C62828')        # Light red
        self.accounts_tree.tag_configure('stopped', background='#F5F5F5', foreground='#616161')      # Light gray
        self.accounts_tree.tag_configure('inactive', background='#FAFAFA', foreground='#9E9E9E')     # Very light gray
        self.accounts_tree.tag_configure('banned', background='#FCE4EC', foreground='#AD1457')       # Light pink
        self.accounts_tree.tag_configure('token_invalid', background='#FFF8E1', foreground='#FF8F00') # Light amber
    
    def get_status_tag(self, status):
        """Get the appropriate tag for a status"""
        status_lower = status.lower()
        
        if 'running' in status_lower:
            return 'running'
        elif 'connecting' in status_lower:
            return 'connecting'
        elif any(word in status_lower for word in ['waiting', 'processing', 'video']):
            return 'waiting'
        elif any(word in status_lower for word in ['error', 'failed']):
            if 'banned' in status_lower or 'ban' in status_lower:
                return 'banned'
            elif 'token' in status_lower and ('invalid' in status_lower or 'expired' in status_lower):
                return 'token_invalid'
            else:
                return 'error'
        elif 'stopped' in status_lower:
            return 'stopped'
        elif 'inactive' in status_lower:
            return 'inactive'
        else:
            return 'inactive'
    
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
            
            # Check token status with colors
            if account.get('token'):
                token_status = "✅ Ready"
                token_color = 'running'
            else:
                token_status = "❌ No Token"
                token_color = 'error'
            
            # Get status tag for coloring
            status_tag = self.get_status_tag(account['status'])
            
            # Insert item with appropriate tag
            item = self.accounts_tree.insert('', tk.END, values=(
                account['id'],
                account['name'],
                account['email'] or 'Unknown',
                account['coin'],
                self.format_status_display(account['status']),
                account['total_videos'],
                account['total_coins'],
                token_status,
                last_run
            ), tags=(status_tag,))
        
        self.status_bar.config(text=f"Loaded {len(accounts)} accounts")
    
    def format_status_display(self, status):
        """Format status text with icons for better visual appeal"""
        status_lower = status.lower()
        
        if 'running' in status_lower:
            return f"🟢 {status}"
        elif 'connecting' in status_lower:
            return f"🟡 {status}"
        elif any(word in status_lower for word in ['waiting', 'processing']):
            return f"🟡 {status}"
        elif 'error' in status_lower:
            if 'banned' in status_lower or 'ban' in status_lower:
                return f"🔴 {status}"
            elif 'token' in status_lower:
                return f"🟠 {status}"
            else:
                return f"🔴 {status}"
        elif 'stopped' in status_lower:
            return f"⚪ {status}"
        elif 'inactive' in status_lower:
            return f"⚫ {status}"
        else:
            return f"⚫ {status}"
    
    def update_account_status_display(self, account_id, status):
        """Update the display of a specific account's status with colors"""
        # Find the item in treeview
        for item in self.accounts_tree.get_children():
            if self.accounts_tree.item(item)['values'][0] == account_id:
                # Get current values
                values = list(self.accounts_tree.item(item)['values'])
                # Update status (index 4)
                values[4] = self.format_status_display(status)
                
                # Get new tag
                status_tag = self.get_status_tag(status)
                
                # Update item
                self.accounts_tree.item(item, values=values, tags=(status_tag,))
                break
    
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
            # Update display with colors immediately
            self.update_account_status_display(account_id, data['status'])
            self.root.after(0, self.refresh_accounts)
        elif callback_type == 'stats':
            self.db.update_account_stats(account_id, data['videos'], data['coins'])
        elif callback_type == 'update_token':
            self.db.update_account_token(account_id, data)
            self.log_message(f"[ID:{account_id}] Updated real token from sign-in")
            # Refresh to update token status color
            self.root.after(0, self.refresh_accounts)
    
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

    def export_accounts(self):
        """Export accounts to JSON file"""
        try:
            accounts = self.db.get_all_accounts()
            if not accounts:
                messagebox.showwarning("Warning", "No accounts to export!")
                return
            
            # Ask user what to export
            export_dialog = ExportDialog(self.root, len(accounts))
            self.root.wait_window(export_dialog.dialog)
            
            if not export_dialog.result:
                return
                
            export_options = export_dialog.result
            
            # Choose file location
            file_path = filedialog.asksaveasfilename(
                title="Export Accounts",
                defaultextension=".json",
                filetypes=[
                    ("JSON files", "*.json"),
                    ("Text files", "*.txt"),
                    ("All files", "*.*")
                ]
            )
            
            if not file_path:
                return
            
            # Prepare export data
            export_data = {
                "export_info": {
                    "tool": "TubeRocket Multi-Account Manager",
                    "version": "1.0",
                    "export_date": datetime.now().isoformat(),
                    "total_accounts": len(accounts),
                    "options": export_options
                },
                "accounts": []
            }
            
            for account in accounts:
                account_data = {
                    "name": account['name'],
                    "token_signin": account['token_signin'],
                    "version_code": account['version_code'],
                    "android": account['android'],
                    "device": account['device'],
                    "locale": account['locale'],
                    "device_token": account['device_token'],
                    "delay": account['delay'],
                    "config": account['config']
                }
                
                # Include optional data based on user selection
                if export_options['include_proxy']:
                    account_data['proxy'] = account['proxy']
                
                if export_options['include_real_token']:
                    account_data['token'] = account['token']
                
                if export_options['include_stats']:
                    account_data['email'] = account['email']
                    account_data['coin'] = account['coin']
                    account_data['status'] = account['status']
                    account_data['total_videos'] = account['total_videos']
                    account_data['total_coins'] = account['total_coins']
                    account_data['last_run'] = account['last_run']
                
                export_data["accounts"].append(account_data)
            
            # Write to file
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            self.log_message(f"Exported {len(accounts)} accounts to {file_path}")
            messagebox.showinfo("Success", f"Successfully exported {len(accounts)} accounts!")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export accounts: {str(e)}")
    
    def import_accounts(self):
        """Import accounts from JSON file"""
        try:
            # Choose file to import
            file_path = filedialog.askopenfilename(
                title="Import Accounts",
                filetypes=[
                    ("JSON files", "*.json"),
                    ("Text files", "*.txt"),
                    ("All files", "*.*")
                ]
            )
            
            if not file_path:
                return
            
            # Read and validate file
            with open(file_path, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
            
            if 'accounts' not in import_data:
                messagebox.showerror("Error", "Invalid file format! Missing 'accounts' data.")
                return
            
            accounts_to_import = import_data['accounts']
            if not accounts_to_import:
                messagebox.showwarning("Warning", "No accounts found in the file!")
                return
            
            # Show import preview
            import_dialog = ImportDialog(self.root, import_data)
            self.root.wait_window(import_dialog.dialog)
            
            if not import_dialog.result:
                return
            
            import_options = import_dialog.result
            
            # Import accounts
            imported_count = 0
            skipped_count = 0
            errors = []
            
            existing_names = [acc['name'] for acc in self.db.get_all_accounts()]
            
            for account_data in accounts_to_import:
                try:
                    # Check for required fields
                    if not account_data.get('name') or not account_data.get('token_signin'):
                        errors.append(f"Account missing required fields: {account_data.get('name', 'Unknown')}")
                        continue
                    
                    # Check for duplicates
                    if account_data['name'] in existing_names and not import_options['overwrite_existing']:
                        skipped_count += 1
                        continue
                    
                    # Prepare account data
                    name = account_data['name']
                    token_signin = account_data['token_signin']
                    version_code = account_data.get('version_code', 187)
                    android = account_data.get('android', 29)
                    device = account_data.get('device', '')
                    locale = account_data.get('locale', 'VN')
                    device_token = account_data.get('device_token', '')
                    proxy = account_data.get('proxy', '') if import_options['import_proxy'] else ''
                    delay = account_data.get('delay', 5)
                    config = account_data.get('config', {})
                    
                    # Handle duplicates
                    if account_data['name'] in existing_names:
                        if import_options['overwrite_existing']:
                            # Update existing account
                            existing_account = next(acc for acc in self.db.get_all_accounts() if acc['name'] == name)
                            self.db.update_account(
                                existing_account['id'], name, token_signin, version_code,
                                android, device, locale, device_token, proxy, delay, config
                            )
                            # Update real token if included
                            if import_options['import_real_token'] and account_data.get('token'):
                                self.db.update_account_token(existing_account['id'], account_data['token'])
                        else:
                            skipped_count += 1
                            continue
                    else:
                        # Add new account
                        account_id = self.db.add_account(
                            name, token_signin, version_code, android, device,
                            locale, device_token, proxy, delay, config
                        )
                        # Update real token if included
                        if import_options['import_real_token'] and account_data.get('token'):
                            self.db.update_account_token(account_id, account_data['token'])
                    
                    imported_count += 1
                    
                except Exception as e:
                    errors.append(f"Error importing {account_data.get('name', 'Unknown')}: {str(e)}")
            
            # Refresh accounts list
            self.refresh_accounts()
            
            # Show results
            result_msg = f"Import completed!\n\n"
            result_msg += f"✅ Imported: {imported_count} accounts\n"
            if skipped_count > 0:
                result_msg += f"⏭️ Skipped: {skipped_count} accounts (duplicates)\n"
            if errors:
                result_msg += f"❌ Errors: {len(errors)} accounts\n\n"
                result_msg += "Errors:\n" + "\n".join(errors[:5])
                if len(errors) > 5:
                    result_msg += f"\n... and {len(errors) - 5} more errors"
            
            self.log_message(f"Imported {imported_count} accounts from {file_path}")
            messagebox.showinfo("Import Results", result_msg)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to import accounts: {str(e)}")

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
