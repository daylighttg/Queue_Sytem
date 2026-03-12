import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from database import create_tables, connect
from queue_logic import (
    join_queue, call_next, mark_done, view_queue, view_history,
    count_waiting, delete_record, clear_all_records, generate_ticket
)


class QueueSystemGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🏥 Queue System")
        self.root.geometry("900x650")
        self.root.resizable(True, True)
        
        # Initialize database
        create_tables()
        
        # Configure style
        style = ttk.Style()
        style.theme_use('clam')
        
        # Create main frame
        self.create_widgets()
        
    def create_widgets(self):
        """Creates the main GUI layout."""
        # Header
        header = ttk.Frame(self.root)
        header.pack(fill=tk.X, padx=10, pady=10)
        
        title = ttk.Label(header, text="🏥 QUEUE SYSTEM", font=("Arial", 24, "bold"))
        title.pack(side=tk.LEFT)
        
        # Main content frame
        content = ttk.Frame(self.root)
        content.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left panel - Actions
        left_panel = ttk.LabelFrame(content, text="Actions", padding=10)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=(0, 10))
        
        # Buttons
        button_width = 20
        
        ttk.Button(left_panel, text="➕ Join Queue", width=button_width, 
                  command=self.join_queue_dialog).pack(pady=5, fill=tk.X)
        
        ttk.Button(left_panel, text="📢 Call Next Customer", width=button_width,
                  command=self.call_next_action).pack(pady=5, fill=tk.X)
        
        ttk.Button(left_panel, text="✅ Mark as Done", width=button_width,
                  command=self.mark_done_action).pack(pady=5, fill=tk.X)
        
        ttk.Button(left_panel, text="🗑️  Delete Record", width=button_width,
                  command=self.delete_record_dialog).pack(pady=5, fill=tk.X)
        
        ttk.Button(left_panel, text="⚠️  Clear All Records", width=button_width,
                  command=self.clear_all_records_dialog).pack(pady=5, fill=tk.X)
        
        ttk.Separator(left_panel, orient=tk.HORIZONTAL).pack(pady=10, fill=tk.X)
        
        ttk.Button(left_panel, text="🔄 Refresh", width=button_width,
                  command=self.refresh_display).pack(pady=5, fill=tk.X)
        
        ttk.Button(left_panel, text="❌ Exit", width=button_width,
                  command=self.root.quit).pack(pady=5, fill=tk.X)
        
        # Right panel - Display
        right_panel = ttk.Frame(content)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Tabs for different views
        self.notebook = ttk.Notebook(right_panel)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Tab 1: Waiting Queue
        waiting_frame = ttk.Frame(self.notebook)
        self.notebook.add(waiting_frame, text="⏳ Waiting Queue")
        
        ttk.Label(waiting_frame, text="Customers Waiting:", font=("Arial", 12, "bold")).pack(padx=10, pady=5, anchor=tk.W)
        
        # Scrollbar for waiting queue
        scrollbar_waiting = ttk.Scrollbar(waiting_frame)
        scrollbar_waiting.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.waiting_text = tk.Text(waiting_frame, height=20, width=60, 
                                   yscrollcommand=scrollbar_waiting.set, 
                                   font=("Courier", 10))
        self.waiting_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        scrollbar_waiting.config(command=self.waiting_text.yview)
        
        # Tab 2: Full History
        history_frame = ttk.Frame(self.notebook)
        self.notebook.add(history_frame, text="📋 Full History")
        
        ttk.Label(history_frame, text="All Records:", font=("Arial", 12, "bold")).pack(padx=10, pady=5, anchor=tk.W)
        
        # Scrollbar for history
        scrollbar_history = ttk.Scrollbar(history_frame)
        scrollbar_history.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.history_text = tk.Text(history_frame, height=20, width=60,
                                   yscrollcommand=scrollbar_history.set,
                                   font=("Courier", 10))
        self.history_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        scrollbar_history.config(command=self.history_text.yview)
        
        # Tab 3: Statistics
        stats_frame = ttk.Frame(self.notebook)
        self.notebook.add(stats_frame, text="📊 Statistics")
        
        self.stats_text = tk.Text(stats_frame, height=20, width=60,
                                 font=("Courier", 10))
        self.stats_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Initial display
        self.refresh_display()
        
    def join_queue_dialog(self):
        """Opens a dialog to add a new customer to the queue."""
        name = simpledialog.askstring("Join Queue", "Enter customer name:")
        if name and name.strip():
            try:
                join_queue(name.strip())
                messagebox.showinfo("Success", f"🎫 Welcome {name.strip()}! Your ticket is {generate_ticket()}")
                self.refresh_display()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to join queue: {str(e)}")
        elif name is not None:
            messagebox.showwarning("Warning", "Name cannot be empty.")
    
    def call_next_action(self):
        """Calls the next customer in the queue."""
        try:
            conn = connect()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, ticket, name FROM customers WHERE status = 'waiting' ORDER BY id ASC LIMIT 1"
            )
            row = cursor.fetchone()
            
            if row is None:
                messagebox.showinfo("Queue", "📭 No one is waiting in the queue.")
                conn.close()
                return
            
            customer_id, ticket, name = row
            cursor.execute(
                "UPDATE customers SET status = 'serving' WHERE id = ?", (customer_id,)
            )
            conn.commit()
            conn.close()
            
            messagebox.showinfo("Now Serving", f"📢 Now serving: {name}\nTicket: {ticket}")
            self.refresh_display()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to call next customer: {str(e)}")
    
    def mark_done_action(self):
        """Marks the current customer as done."""
        try:
            conn = connect()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, ticket, name FROM customers WHERE status = 'serving' ORDER BY id ASC LIMIT 1"
            )
            row = cursor.fetchone()
            
            if row is None:
                messagebox.showwarning("Warning", "⚠️  No customer is currently being served.")
                conn.close()
                return
            
            customer_id, ticket, name = row
            cursor.execute(
                "UPDATE customers SET status = 'done' WHERE id = ?", (customer_id,)
            )
            conn.commit()
            conn.close()
            
            messagebox.showinfo("Complete", f"✅ {name} (Ticket {ticket}) has been marked as done.")
            self.refresh_display()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to mark customer as done: {str(e)}")
    
    def delete_record_dialog(self):
        """Opens a dialog to delete a specific record."""
        try:
            conn = connect()
            cursor = conn.cursor()
            cursor.execute("SELECT id, ticket, name, status FROM customers ORDER BY id ASC")
            rows = cursor.fetchall()
            conn.close()
            
            if not rows:
                messagebox.showinfo("Delete", "📭 No records found.")
                return
            
            # Create a new window to show records
            delete_window = tk.Toplevel(self.root)
            delete_window.title("Delete Record")
            delete_window.geometry("500x400")
            
            ttk.Label(delete_window, text="Select a record to delete:", font=("Arial", 10, "bold")).pack(padx=10, pady=5)
            
            # Listbox with scrollbar
            scrollbar = ttk.Scrollbar(delete_window)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            listbox = tk.Listbox(delete_window, yscrollcommand=scrollbar.set, font=("Courier", 9))
            listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
            scrollbar.config(command=listbox.yview)
            
            # Populate listbox
            self.record_ids = []
            for id, ticket, name, status in rows:
                self.record_ids.append(id)
                listbox.insert(tk.END, f"ID: {id}  |  {ticket}  |  {name}  |  {status.upper()}")
            
            def delete_selected():
                selection = listbox.curselection()
                if selection:
                    index = selection[0]
                    record_id = self.record_ids[index]
                    
                    # Get record info for confirmation
                    conn = connect()
                    cursor = conn.cursor()
                    cursor.execute("SELECT ticket, name FROM customers WHERE id = ?", (record_id,))
                    record = cursor.fetchone()
                    conn.close()
                    
                    if record:
                        ticket, name = record
                        if messagebox.askyesno("Confirm", f"⚠️  Delete {ticket} ({name})?"):
                            try:
                                conn = connect()
                                cursor = conn.cursor()
                                cursor.execute("DELETE FROM customers WHERE id = ?", (record_id,))
                                conn.commit()
                                conn.close()
                                messagebox.showinfo("Success", f"✅ Record {ticket} ({name}) has been deleted.")
                                self.refresh_display()
                                delete_window.destroy()
                            except Exception as e:
                                messagebox.showerror("Error", f"Failed to delete record: {str(e)}")
                else:
                    messagebox.showwarning("Warning", "Please select a record to delete.")
            
            ttk.Button(delete_window, text="Delete Selected", command=delete_selected).pack(pady=10)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open delete dialog: {str(e)}")
    
    def clear_all_records_dialog(self):
        """Confirms and clears all records."""
        try:
            conn = connect()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM customers")
            count = cursor.fetchone()[0]
            conn.close()
            
            if count == 0:
                messagebox.showinfo("Clear", "📭 No records to clear.")
                return
            
            if messagebox.askyesno("Confirm", f"⚠️  WARNING: Delete ALL {count} records?\n\nThis action cannot be undone!"):
                conn = connect()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM customers")
                conn.commit()
                conn.close()
                messagebox.showinfo("Success", f"✅ All {count} records have been deleted.")
                self.refresh_display()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to clear records: {str(e)}")
    
    def refresh_display(self):
        """Refreshes all displays with current data."""
        # Clear all text widgets
        self.waiting_text.delete(1.0, tk.END)
        self.history_text.delete(1.0, tk.END)
        self.stats_text.delete(1.0, tk.END)
        
        try:
            conn = connect()
            cursor = conn.cursor()
            
            # Waiting Queue
            cursor.execute(
                "SELECT ticket, name, created_at FROM customers WHERE status = 'waiting' ORDER BY id ASC"
            )
            waiting_rows = cursor.fetchall()
            
            if waiting_rows:
                self.waiting_text.insert(tk.END, "--- 🕐 Waiting Queue ---\n\n")
                for ticket, name, created_at in waiting_rows:
                    self.waiting_text.insert(tk.END, f"{ticket}  |  {name}  |  {created_at}\n")
                self.waiting_text.insert(tk.END, f"\nTotal waiting: {len(waiting_rows)}\n")
            else:
                self.waiting_text.insert(tk.END, "📭 The queue is empty — no one is waiting.\n")
            
            # Full History
            cursor.execute(
                "SELECT ticket, name, status, created_at FROM customers ORDER BY id ASC"
            )
            history_rows = cursor.fetchall()
            
            if history_rows:
                self.history_text.insert(tk.END, "--- 📋 Full History ---\n\n")
                for ticket, name, status, created_at in history_rows:
                    self.history_text.insert(tk.END, f"{ticket}  |  {name}  |  {status.upper()}  |  {created_at}\n")
                self.history_text.insert(tk.END, f"\nTotal records: {len(history_rows)}\n")
            else:
                self.history_text.insert(tk.END, "📭 No records found.\n")
            
            # Statistics
            cursor.execute("SELECT COUNT(*) FROM customers WHERE status = 'waiting'")
            waiting_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM customers WHERE status = 'serving'")
            serving_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM customers WHERE status = 'done'")
            done_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM customers")
            total_count = cursor.fetchone()[0]
            
            conn.close()
            
            # Display statistics
            stats = f"""
--- 📊 STATISTICS ---

Waiting:     {waiting_count}
Serving:     {serving_count}
Done:        {done_count}
──────────────────
Total:       {total_count}

"""
            self.stats_text.insert(tk.END, stats)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to refresh display: {str(e)}")


def main():
    """Main entry point for the GUI."""
    root = tk.Tk()
    app = QueueSystemGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()

