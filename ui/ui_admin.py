import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

from core.database import create_tables
from core.queue_logic import (
    join_queue,
    call_next,
    mark_done,
    get_waiting,
    get_history,
    get_all_records,
    delete_record,
    clear_all_records,
    get_stats,
)


class QueueSystemGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🏥 Queue System")
        self.root.geometry("900x650")
        self.root.resizable(True, True)

        create_tables()

        style = ttk.Style()
        style.theme_use("clam")

        self.create_widgets()

    # ── Layout ────────────────────────────────────────────────
    def create_widgets(self):
        """Creates the main GUI layout."""
        # Header
        header = ttk.Frame(self.root)
        header.pack(fill=tk.X, padx=10, pady=10)
        ttk.Label(
            header, text="🏥 QUEUE SYSTEM", font=("Arial", 24, "bold")
        ).pack(side=tk.LEFT)

        # Main content frame
        content = ttk.Frame(self.root)
        content.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Left panel — Actions
        left_panel = ttk.LabelFrame(content, text="Actions", padding=10)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=(0, 10))

        button_width = 20
        ttk.Button(
            left_panel, text="➕ Join Queue", width=button_width,
            command=self.join_queue_dialog,
        ).pack(pady=5, fill=tk.X)
        ttk.Button(
            left_panel, text="📢 Call Next Customer", width=button_width,
            command=self.call_next_action,
        ).pack(pady=5, fill=tk.X)
        ttk.Button(
            left_panel, text="✅ Mark as Done", width=button_width,
            command=self.mark_done_action,
        ).pack(pady=5, fill=tk.X)
        ttk.Button(
            left_panel, text="🗑️  Delete Record", width=button_width,
            command=self.delete_record_dialog,
        ).pack(pady=5, fill=tk.X)
        ttk.Button(
            left_panel, text="⚠️  Clear All Records", width=button_width,
            command=self.clear_all_records_dialog,
        ).pack(pady=5, fill=tk.X)

        ttk.Separator(left_panel, orient=tk.HORIZONTAL).pack(pady=10, fill=tk.X)

        ttk.Button(
            left_panel, text="🔄 Refresh", width=button_width,
            command=self.refresh_display,
        ).pack(pady=5, fill=tk.X)
        ttk.Button(
            left_panel, text="❌ Exit", width=button_width,
            command=self.root.quit,
        ).pack(pady=5, fill=tk.X)

        # Right panel — tabbed display
        right_panel = ttk.Frame(content)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.notebook = ttk.Notebook(right_panel)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        self.waiting_text = self._make_tab("⏳ Waiting Queue", "Customers Waiting:")
        self.history_text = self._make_tab("📋 Full History", "All Records:")

        stats_frame = ttk.Frame(self.notebook)
        self.notebook.add(stats_frame, text="📊 Statistics")
        self.stats_text = tk.Text(stats_frame, height=20, width=60, font=("Courier", 10))
        self.stats_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.refresh_display()

    def _make_tab(self, tab_label, header_text):
        """Helper: creates a scrollable text tab and returns the Text widget."""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text=tab_label)
        ttk.Label(frame, text=header_text, font=("Arial", 12, "bold")).pack(
            padx=10, pady=5, anchor=tk.W
        )
        scrollbar = ttk.Scrollbar(frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        text_widget = tk.Text(
            frame, height=20, width=60,
            yscrollcommand=scrollbar.set, font=("Courier", 10),
        )
        text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        scrollbar.config(command=text_widget.yview)
        return text_widget

    # ── Actions ───────────────────────────────────────────────
    def join_queue_dialog(self):
        """Opens a dialog to add a new customer to the queue."""
        name = simpledialog.askstring("Join Queue", "Enter customer name:")
        if name and name.strip():
            try:
                ticket = join_queue(name.strip())
                messagebox.showinfo(
                    "Success", f"🎫 Welcome {name.strip()}!\nYour ticket is {ticket}"
                )
                self.refresh_display()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to join queue: {e}")
        elif name is not None:
            messagebox.showwarning("Warning", "Name cannot be empty.")

    def call_next_action(self):
        """Calls the next customer in the queue."""
        try:
            result = call_next()
            if result is None:
                messagebox.showinfo("Queue", "📭 No one is waiting in the queue.")
            else:
                ticket, name = result
                messagebox.showinfo("Now Serving", f"📢 Now serving: {name}\nTicket: {ticket}")
            self.refresh_display()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to call next customer: {e}")

    def mark_done_action(self):
        """Marks the current customer as done."""
        try:
            result = mark_done()
            if result is None:
                messagebox.showwarning("Warning", "⚠️  No customer is currently being served.")
            else:
                ticket, name = result
                messagebox.showinfo(
                    "Complete", f"✅ {name} (Ticket {ticket}) has been marked as done."
                )
            self.refresh_display()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to mark customer as done: {e}")

    def delete_record_dialog(self):
        """Opens a window listing records; the selected one can be deleted."""
        try:
            rows = get_all_records()
            if not rows:
                messagebox.showinfo("Delete", "📭 No records found.")
                return

            delete_window = tk.Toplevel(self.root)
            delete_window.title("Delete Record")
            delete_window.geometry("500x400")
            ttk.Label(
                delete_window, text="Select a record to delete:",
                font=("Arial", 10, "bold"),
            ).pack(padx=10, pady=5)

            scrollbar = ttk.Scrollbar(delete_window)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            listbox = tk.Listbox(
                delete_window, yscrollcommand=scrollbar.set, font=("Courier", 9)
            )
            listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
            scrollbar.config(command=listbox.yview)

            record_ids = []
            for record_id, ticket, name, status in rows:
                record_ids.append(record_id)
                listbox.insert(
                    tk.END, f"ID: {record_id}  |  {ticket}  |  {name}  |  {status.upper()}"
                )

            def delete_selected():
                selection = listbox.curselection()
                if not selection:
                    messagebox.showwarning("Warning", "Please select a record to delete.")
                    return
                record_id = record_ids[selection[0]]
                record_info = next(
                    ((t, n) for rid, t, n, s in rows if rid == record_id), None
                )
                if record_info and messagebox.askyesno(
                    "Confirm", f"⚠️  Delete {record_info[0]} ({record_info[1]})?"
                ):
                    try:
                        delete_record(record_id)
                        messagebox.showinfo(
                            "Success",
                            f"✅ Record {record_info[0]} ({record_info[1]}) has been deleted.",
                        )
                        self.refresh_display()
                        delete_window.destroy()
                    except Exception as e:
                        messagebox.showerror("Error", f"Failed to delete record: {e}")

            ttk.Button(
                delete_window, text="Delete Selected", command=delete_selected
            ).pack(pady=10)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open delete dialog: {e}")

    def clear_all_records_dialog(self):
        """Confirms and clears all records."""
        try:
            rows = get_all_records()
            count = len(rows)
            if count == 0:
                messagebox.showinfo("Clear", "📭 No records to clear.")
                return
            if messagebox.askyesno(
                "Confirm",
                f"⚠️  WARNING: Delete ALL {count} records?\n\nThis action cannot be undone!",
            ):
                clear_all_records()
                messagebox.showinfo("Success", f"✅ All {count} records have been deleted.")
                self.refresh_display()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to clear records: {e}")

    # ── Display refresh ───────────────────────────────────────
    def refresh_display(self):
        """Refreshes all tabs with current data from the database."""
        self.waiting_text.delete(1.0, tk.END)
        self.history_text.delete(1.0, tk.END)
        self.stats_text.delete(1.0, tk.END)
        try:
            # Waiting queue tab
            waiting_rows = get_waiting()
            if waiting_rows:
                self.waiting_text.insert(tk.END, "--- 🕐 Waiting Queue ---\n\n")
                for ticket, name, created_at in waiting_rows:
                    self.waiting_text.insert(
                        tk.END, f"{ticket}  |  {name}  |  {created_at}\n"
                    )
                self.waiting_text.insert(tk.END, f"\nTotal waiting: {len(waiting_rows)}\n")
            else:
                self.waiting_text.insert(
                    tk.END, "📭 The queue is empty — no one is waiting.\n"
                )

            # History tab
            history_rows = get_history()
            if history_rows:
                self.history_text.insert(tk.END, "--- 📋 Full History ---\n\n")
                for ticket, name, status, created_at in history_rows:
                    self.history_text.insert(
                        tk.END, f"{ticket}  |  {name}  |  {status.upper()}  |  {created_at}\n"
                    )
                self.history_text.insert(
                    tk.END, f"\nTotal records: {len(history_rows)}\n"
                )
            else:
                self.history_text.insert(tk.END, "📭 No records found.\n")

            # Statistics tab
            s = get_stats()
            self.stats_text.insert(
                tk.END,
                f"--- 📊 STATISTICS ---\n\n"
                f"Waiting:     {s['waiting']}\n"
                f"Serving:     {s['serving']}\n"
                f"Done:        {s['done']}\n"
                f"──────────────────\n"
                f"Total:       {s['total']}\n",
            )
        except Exception as e:
            messagebox.showerror("Error", f"Failed to refresh display: {e}")


def main():
    """Main entry point for the GUI."""
    root = tk.Tk()
    app = QueueSystemGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
