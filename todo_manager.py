#!/usr/bin/env python3
"""
To-Do List Manager - A comprehensive desktop application for task management
Features: Add, update, delete, mark complete/incomplete tasks with SQLite storage
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import sqlite3
from datetime import datetime, timedelta
from typing import Optional, List, Tuple, Dict, Any
import json
import os
import csv
from collections import defaultdict

# Database path
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tasks.db")
CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")


class DatabaseManager:
    """Handles all database operations"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        self.connect()
        self.create_tables()
    
    def connect(self):
        """Establish database connection"""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row
            self.cursor = self.conn.cursor()
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Failed to connect to database: {e}")
            raise
    
    def create_tables(self):
        """Create necessary database tables"""
        try:
            # Tasks table
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    description TEXT,
                    completed INTEGER DEFAULT 0,
                    type TEXT NOT NULL,
                    priority TEXT NOT NULL,
                    to_do_at DATETIME,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    parent_id INTEGER,
                    project_name TEXT,
                    tags TEXT,
                    recurrence_rule TEXT,
                    recurrence_end_date DATETIME,
                    recurrence_count INTEGER,
                    time_block_type TEXT DEFAULT 'day',
                    week_number INTEGER,
                    month_number INTEGER,
                    year_number INTEGER,
                    FOREIGN KEY (parent_id) REFERENCES tasks(id)
                )
            ''')
            
            # Projects table
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS projects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    description TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Tags table
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS tags (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL
                )
            ''')
            
            self.conn.commit()
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Failed to create tables: {e}")
            raise
    
    def execute(self, query: str, params: tuple = ()) -> sqlite3.Cursor:
        """Execute a query with error handling"""
        try:
            self.cursor.execute(query, params)
            return self.cursor
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Query failed: {e}")
            raise
    
    def commit(self):
        """Commit changes"""
        try:
            self.conn.commit()
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Failed to commit: {e}")
            raise
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()


class CalendarWidget(ttk.Frame):
    """Browsable calendar widget for the left side"""
    
    def __init__(self, parent, on_date_select_callback):
        super().__init__(parent)
        self.on_date_select = on_date_select_callback
        self.current_year = datetime.now().year
        self.current_month = datetime.now().month
        self.selected_date = datetime.now().date()
        self.days_with_tasks = set()
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the calendar UI"""
        # Navigation frame
        nav_frame = ttk.Frame(self)
        nav_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.prev_btn = ttk.Button(nav_frame, text="<", command=self.prev_month, width=3)
        self.prev_btn.pack(side=tk.LEFT)
        
        self.month_label = ttk.Label(nav_frame, text="", font=("Arial", 12, "bold"))
        self.month_label.pack(side=tk.LEFT, expand=True)
        
        self.next_btn = ttk.Button(nav_frame, text=">", command=self.next_month, width=3)
        self.next_btn.pack(side=tk.RIGHT)
        
        self.today_btn = ttk.Button(nav_frame, text="Today", command=self.go_to_today)
        self.today_btn.pack(side=tk.RIGHT, padx=5)
        
        # View selector
        view_frame = ttk.Frame(self)
        view_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(view_frame, text="View:").pack(side=tk.LEFT)
        self.view_var = tk.StringVar(value="month")
        view_combo = ttk.Combobox(view_frame, textvariable=self.view_var, 
                                   values=["day", "week", "month", "year"], 
                                   state="readonly", width=8)
        view_combo.pack(side=tk.LEFT, padx=5)
        view_combo.bind('<<ComboboxSelected>>', self.on_view_change)
        
        # Calendar grid
        self.calendar_frame = ttk.Frame(self)
        self.calendar_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.render_calendar()
    
    def render_calendar(self):
        """Render the calendar based on current view"""
        for widget in self.calendar_frame.winfo_children():
            widget.destroy()
        
        view = self.view_var.get()
        
        if view == "year":
            self.render_year_view()
        elif view == "month":
            self.render_month_view()
        elif view == "week":
            self.render_week_view()
        else:
            self.render_day_view()
    
    def render_month_view(self):
        """Render month view calendar"""
        # Day headers
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        for i, day in enumerate(days):
            lbl = ttk.Label(self.calendar_frame, text=day, font=("Arial", 9, "bold"))
            lbl.grid(row=0, column=i, padx=1, pady=1, sticky="ew")
        
        # Get first day and number of days in month
        first_day = datetime(self.current_year, self.current_month, 1)
        if self.current_month == 12:
            next_month = datetime(self.current_year + 1, 1, 1)
        else:
            next_month = datetime(self.current_year, self.current_month + 1, 1)
        
        num_days = (next_month - first_day).days
        start_weekday = (first_day.weekday()) % 7
        
        # Update month label
        self.month_label.config(text=f"{first_day.strftime('%B')} {self.current_year}")
        
        # Create day buttons
        row = 1
        col = start_weekday
        
        for day in range(1, num_days + 1):
            date = datetime(self.current_year, self.current_month, day).date()
            is_selected = date == self.selected_date
            has_tasks = date in self.days_with_tasks
            
            btn_style = "selected.TButton" if is_selected else "task.TButton" if has_tasks else "TButton"
            
            btn = ttk.Button(self.calendar_frame, text=str(day), 
                            command=lambda d=day: self.select_date(d),
                            style=btn_style if hasattr(self, 'style') else "TButton")
            btn.grid(row=row, column=col, padx=1, pady=1, sticky="nsew")
            
            col += 1
            if col > 6:
                col = 0
                row += 1
        
        # Configure grid weights
        for i in range(7):
            self.calendar_frame.columnconfigure(i, weight=1)
        for i in range(row + 1):
            self.calendar_frame.rowconfigure(i, weight=1)
    
    def render_year_view(self):
        """Render year view with all months"""
        self.month_label.config(text=f"{self.current_year}")
        
        for month in range(1, 13):
            month_frame = ttk.LabelFrame(self.calendar_frame, text=datetime(self.current_year, month, 1).strftime("%B"))
            row = (month - 1) // 3
            col = (month - 1) % 3
            month_frame.grid(row=row, column=col, padx=2, pady=2, sticky="nsew")
            
            # Simple month representation
            first_day = datetime(self.current_year, month, 1)
            if month == 12:
                next_month = datetime(self.current_year + 1, 1, 1)
            else:
                next_month = datetime(self.current_year, month + 1, 1)
            
            num_days = (next_month - first_day).days
            day = 1
            for week in range(6):
                for weekday in range(7):
                    if day <= num_days:
                        if (week == 0 and weekday < first_day.weekday()) or day > num_days:
                            pass
                        else:
                            date = datetime(self.current_year, month, day).date()
                            is_selected = date == self.selected_date
                            btn = ttk.Button(month_frame, text=str(day), width=2,
                                           command=lambda m=month, d=day: self.select_date(d, m))
                            if is_selected:
                                btn.config(style="selected.TButton")
                            btn.grid(row=week, column=weekday, padx=0, pady=0)
                            day += 1
        
        for i in range(4):
            self.calendar_frame.columnconfigure(i, weight=1)
        for i in range(4):
            self.calendar_frame.rowconfigure(i, weight=1)
    
    def render_week_view(self):
        """Render week view"""
        # Find the start of the current week (Monday)
        current_date = datetime(self.current_year, self.current_month, 1)
        start_of_week = current_date - timedelta(days=current_date.weekday())
        
        self.month_label.config(text=f"Week starting {start_of_week.strftime('%b %d, %Y')}")
        
        for i in range(7):
            day_date = start_of_week + timedelta(days=i)
            is_selected = day_date.date() == self.selected_date
            has_tasks = day_date.date() in self.days_with_tasks
            
            frame = ttk.Frame(self.calendar_frame)
            frame.grid(row=0, column=i, padx=2, pady=2, sticky="nsew")
            
            day_name = ttk.Label(frame, text=day_date.strftime("%a"), font=("Arial", 9, "bold"))
            day_name.pack()
            
            day_num = ttk.Label(frame, text=str(day_date.day), font=("Arial", 14))
            day_num.pack()
            
            if has_tasks:
                task_indicator = ttk.Label(frame, text="●", foreground="blue")
                task_indicator.pack()
            
            btn = ttk.Button(frame, text="Select", 
                           command=lambda d=day_date.day, m=day_date.month, y=day_date.year: 
                                   self.select_date(d, m, y))
            btn.pack()
            
            self.calendar_frame.columnconfigure(i, weight=1)
            self.calendar_frame.rowconfigure(0, weight=1)
    
    def render_day_view(self):
        """Render detailed day view"""
        current_date = datetime(self.current_year, self.current_month, self.selected_date.day)
        self.month_label.config(text=current_date.strftime("%A, %B %d, %Y"))
        
        # Show hours of the day
        for hour in range(24):
            hour_frame = ttk.Frame(self.calendar_frame)
            hour_frame.grid(row=hour, column=0, columnspan=7, sticky="ew", pady=1)
            
            hour_label = ttk.Label(hour_frame, text=f"{hour:02d}:00", width=8, anchor="e")
            hour_label.pack(side=tk.LEFT)
            
            hour_line = ttk.Separator(hour_frame, orient=tk.HORIZONTAL)
            hour_line.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        self.calendar_frame.rowconfigure(0, weight=1)
    
    def select_date(self, day: int, month: Optional[int] = None, year: Optional[int] = None):
        """Handle date selection"""
        if month is None:
            month = self.current_month
        if year is None:
            year = self.current_year
        
        self.selected_date = datetime(year, month, day).date()
        self.render_calendar()
        
        if self.on_date_select:
            self.on_date_select(self.selected_date)
    
    def prev_month(self):
        """Navigate to previous month"""
        if self.current_month == 1:
            self.current_month = 12
            self.current_year -= 1
        else:
            self.current_month -= 1
        self.render_calendar()
    
    def next_month(self):
        """Navigate to next month"""
        if self.current_month == 12:
            self.current_month = 1
            self.current_year += 1
        else:
            self.current_month += 1
        self.render_calendar()
    
    def go_to_today(self):
        """Go to today's date"""
        today = datetime.now()
        self.current_year = today.year
        self.current_month = today.month
        self.selected_date = today.date()
        self.render_calendar()
    
    def on_view_change(self, event=None):
        """Handle view change"""
        self.render_calendar()
    
    def set_days_with_tasks(self, dates: set):
        """Mark dates that have tasks"""
        self.days_with_tasks = dates
        self.render_calendar()


class TaskEditor(tk.Toplevel):
    """Rich text editor for creating tasks with subtasks"""
    
    def __init__(self, parent, db_manager, task_data=None, on_save_callback=None):
        super().__init__(parent)
        self.db = db_manager
        self.task_data = task_data
        self.on_save = on_save_callback
        self.title("Edit Task" if task_data else "New Task")
        self.geometry("600x500")
        self.transient(parent)
        self.grab_set()
        
        self.setup_ui()
        
        if task_data:
            self.load_task(task_data)
    
    def setup_ui(self):
        """Setup the editor UI"""
        # Main frame
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title entry
        ttk.Label(main_frame, text="Title:").pack(anchor=tk.W)
        self.title_entry = ttk.Entry(main_frame, font=("Arial", 12))
        self.title_entry.pack(fill=tk.X, pady=(0, 10))
        
        # Text area for description and subtasks
        ttk.Label(main_frame, text="Description & Subtasks (use indentation for subtasks):").pack(anchor=tk.W)
        
        self.text_frame = ttk.Frame(main_frame)
        self.text_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.description_text = tk.Text(self.text_frame, wrap=tk.WORD, font=("Arial", 11), height=15)
        self.description_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(self.text_frame, command=self.description_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.description_text.config(yscrollcommand=scrollbar.set)
        
        # Bind Tab key for indentation
        self.description_text.bind('<Tab>', self.insert_indent)
        
        # Options frame
        options_frame = ttk.LabelFrame(main_frame, text="Options", padding="5")
        options_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Type
        ttk.Label(options_frame, text="Type:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.type_var = tk.StringVar()
        type_combo = ttk.Combobox(options_frame, textvariable=self.type_var, 
                                  values=["Work", "Personal", "Shopping", "Health", "Finance", "Other"],
                                  state="readonly", width=15)
        type_combo.grid(row=0, column=1, padx=5, pady=5)
        
        # Priority
        ttk.Label(options_frame, text="Priority:").grid(row=0, column=2, sticky=tk.W, padx=5)
        self.priority_var = tk.StringVar()
        priority_combo = ttk.Combobox(options_frame, textvariable=self.priority_var,
                                      values=["Low", "Medium", "High"],
                                      state="readonly", width=15)
        priority_combo.grid(row=0, column=3, padx=5, pady=5)
        
        # Due date/time
        ttk.Label(options_frame, text="Due Date/Time:").grid(row=1, column=0, sticky=tk.W, padx=5)
        self.due_date_entry = ttk.Entry(options_frame, width=20)
        self.due_date_entry.grid(row=1, column=1, padx=5, pady=5)
        self.due_date_entry.insert(0, datetime.now().strftime("%Y-%m-%d %H:%M"))
        
        ttk.Button(options_frame, text="Select", command=self.select_due_date).grid(row=1, column=2, padx=5)
        
        # Time block type
        ttk.Label(options_frame, text="Time Block:").grid(row=1, column=2, sticky=tk.W, padx=5)
        self.time_block_var = tk.StringVar(value="day")
        time_block_combo = ttk.Combobox(options_frame, textvariable=self.time_block_var,
                                        values=["day", "week", "month", "year"],
                                        state="readonly", width=10)
        time_block_combo.grid(row=1, column=3, padx=5, pady=5)
        
        # Project
        ttk.Label(options_frame, text="Project:").grid(row=2, column=0, sticky=tk.W, padx=5)
        self.project_var = tk.StringVar()
        project_combo = ttk.Combobox(options_frame, textvariable=self.project_var, state="readonly", width=15)
        project_combo.grid(row=2, column=1, padx=5, pady=5)
        self.load_projects(project_combo)
        
        ttk.Button(options_frame, text="+", command=self.add_project).grid(row=2, column=2, padx=5)
        
        # Tags
        ttk.Label(options_frame, text="Tags:").grid(row=2, column=2, sticky=tk.W, padx=5)
        self.tags_entry = ttk.Entry(options_frame, width=20)
        self.tags_entry.grid(row=2, column=3, padx=5, pady=5)
        self.tags_entry.insert(0, "")
        
        # Recurrence
        rec_frame = ttk.LabelFrame(options_frame, text="Recurrence", padding="5")
        rec_frame.grid(row=3, column=0, columnspan=4, sticky="ew", pady=5)
        
        ttk.Label(rec_frame, text="Repeat:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.recurrence_var = tk.StringVar(value="none")
        rec_combo = ttk.Combobox(rec_frame, textvariable=self.recurrence_var,
                                 values=["none", "daily", "every_n_days", "weekly", "monthly", "yearly"],
                                 state="readonly", width=12)
        rec_combo.grid(row=0, column=1, padx=5, pady=5)
        rec_combo.bind('<<ComboboxSelected>>', self.on_recurrence_change)
        
        self.rec_interval_label = ttk.Label(rec_frame, text="Every:")
        self.rec_interval_label.grid(row=0, column=2, sticky=tk.W, padx=5)
        self.rec_interval_spin = ttk.Spinbox(rec_frame, from_=1, to=365, width=5)
        self.rec_interval_spin.grid(row=0, column=3, padx=5)
        self.rec_interval_label.grid_remove()
        self.rec_interval_spin.grid_remove()
        
        self.rec_end_label = ttk.Label(rec_frame, text="End Date:")
        self.rec_end_label.grid(row=0, column=4, sticky=tk.W, padx=5)
        self.rec_end_entry = ttk.Entry(rec_frame, width=12)
        self.rec_end_entry.grid(row=0, column=5, padx=5)
        self.rec_end_label.grid_remove()
        self.rec_end_entry.grid_remove()
        
        # Buttons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X)
        
        ttk.Button(btn_frame, text="Save", command=self.save_task).pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=self.destroy).pack(side=tk.RIGHT, padx=5)
    
    def insert_indent(self, event):
        """Insert 4 spaces for indentation"""
        self.description_text.insert(tk.INSERT, "    ")
        return 'break'
    
    def load_projects(self, combo):
        """Load projects into combobox"""
        try:
            cursor = self.db.execute("SELECT name FROM projects ORDER BY name")
            projects = [row['name'] for row in cursor.fetchall()]
            combo['values'] = projects
        except:
            pass
    
    def add_project(self):
        """Add a new project"""
        project_name = simpledialog.askstring("New Project", "Enter project name:")
        if project_name:
            try:
                self.db.execute("INSERT INTO projects (name) VALUES (?)", (project_name,))
                self.db.commit()
                self.load_projects(self.project_var)
                self.project_var.set(project_name)
            except sqlite3.IntegrityError:
                messagebox.showwarning("Warning", "Project already exists")
    
    def on_recurrence_change(self, event=None):
        """Show/hide recurrence options"""
        recurrence = self.recurrence_var.get()
        if recurrence == "every_n_days":
            self.rec_interval_label.grid()
            self.rec_interval_spin.grid()
            self.rec_end_label.grid()
            self.rec_end_entry.grid()
        elif recurrence != "none":
            self.rec_interval_label.grid_remove()
            self.rec_interval_spin.grid_remove()
            self.rec_end_label.grid()
            self.rec_end_entry.grid()
        else:
            self.rec_interval_label.grid_remove()
            self.rec_interval_spin.grid_remove()
            self.rec_end_label.grid_remove()
            self.rec_end_entry.grid_remove()
    
    def select_due_date(self):
        """Open date picker for due date"""
        from tkinter import simpledialog
        current = self.due_date_entry.get()
        new_date = simpledialog.askstring("Due Date", "Enter due date (YYYY-MM-DD HH:MM):", initialvalue=current)
        if new_date:
            self.due_date_entry.delete(0, tk.END)
            self.due_date_entry.insert(0, new_date)
    
    def load_task(self, task_data):
        """Load existing task data into editor"""
        self.title_entry.insert(0, task_data['title'])
        self.description_text.insert('1.0', task_data.get('description', ''))
        self.type_var.set(task_data.get('type', 'Work'))
        self.priority_var.set(task_data.get('priority', 'Medium'))
        
        if task_data.get('to_do_at'):
            self.due_date_entry.delete(0, tk.END)
            self.due_date_entry.insert(0, task_data['to_do_at'])
        
        self.time_block_var.set(task_data.get('time_block_type', 'day'))
        self.project_var.set(task_data.get('project_name', ''))
        self.tags_entry.insert(0, task_data.get('tags', ''))
        
        if task_data.get('recurrence_rule'):
            self.recurrence_var.set(task_data['recurrence_rule'])
            self.on_recurrence_change()
    
    def save_task(self):
        """Save the task"""
        title = self.title_entry.get().strip()
        if not title:
            messagebox.showwarning("Validation Error", "Title is required")
            return
        
        description = self.description_text.get('1.0', tk.END).strip()
        
        try:
            due_date = self.due_date_entry.get().strip() or None
            recurrence_rule = self.recurrence_var.get() if self.recurrence_var.get() != "none" else None
            recurrence_end = self.rec_end_entry.get().strip() or None
            rec_interval = int(self.rec_interval_spin.get()) if self.rec_interval_spin.get() else None
            
            if self.task_data:
                # Update existing task
                self.db.execute('''
                    UPDATE tasks SET 
                    title=?, description=?, type=?, priority=?, to_do_at=?,
                    time_block_type=?, project_name=?, tags=?, recurrence_rule=?,
                    recurrence_end_date=?
                    WHERE id=?
                ''', (title, description, self.type_var.get(), self.priority_var.get(),
                      due_date, self.time_block_var.get(), self.project_var.get(),
                      self.tags_entry.get(), recurrence_rule, recurrence_end,
                      self.task_data['id']))
            else:
                # Insert new task
                self.db.execute('''
                    INSERT INTO tasks (title, description, type, priority, to_do_at,
                                      time_block_type, project_name, tags, recurrence_rule,
                                      recurrence_end_date, recurrence_count)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (title, description, self.type_var.get(), self.priority_var.get(),
                      due_date, self.time_block_var.get(), self.project_var.get(),
                      self.tags_entry.get(), recurrence_rule, recurrence_end, rec_interval))
            
            self.db.commit()
            
            if self.on_save:
                self.on_save()
            
            self.destroy()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save task: {e}")


class TodoApp:
    """Main To-Do List Manager Application"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("To-Do List Manager")
        self.root.geometry("1400x800")
        self.root.minsize(1200, 700)
        
        # Initialize database
        self.db = DatabaseManager(DB_PATH)
        
        # Load configuration
        self.config = self.load_config()
        
        # Apply saved geometry
        if self.config.get('geometry'):
            self.root.geometry(self.config['geometry'])
        
        # Current filter state
        self.current_filter = "all"
        self.current_type_filter = "all"
        self.current_priority_filter = "all"
        self.search_query = ""
        self.current_week_start = datetime.now() - timedelta(days=datetime.now().weekday())
        
        # Setup UI
        self.setup_styles()
        self.setup_ui()
        self.refresh_task_list()
        self.update_calendar_tasks()
        
        # Bind close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
    
    def setup_styles(self):
        """Setup custom styles"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure colors
        style.configure("selected.TButton", background="#4CAF50", foreground="white")
        style.configure("task.TButton", background="#2196F3", foreground="white")
        style.configure("high.TLabel", foreground="red")
        style.configure("medium.TLabel", foreground="orange")
        style.configure("low.TLabel", foreground="green")
    
    def setup_ui(self):
        """Setup the main UI"""
        # Main container
        main_container = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Left panel - Calendar
        left_panel = ttk.Frame(main_container)
        main_container.add(left_panel, weight=1)
        
        self.calendar = CalendarWidget(left_panel, self.on_calendar_date_select)
        self.calendar.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Right panel - Task list and controls
        right_panel = ttk.Frame(main_container)
        main_container.add(right_panel, weight=3)
        
        # Top section - Filters and search
        top_frame = ttk.Frame(right_panel)
        top_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Search
        ttk.Label(top_frame, text="Search:").pack(side=tk.LEFT, padx=5)
        self.search_entry = ttk.Entry(top_frame, width=30)
        self.search_entry.pack(side=tk.LEFT, padx=5)
        self.search_entry.bind('<KeyRelease>', self.on_search_change)
        
        # Filter by status
        ttk.Label(top_frame, text="Status:").pack(side=tk.LEFT, padx=(20, 5))
        self.status_var = tk.StringVar(value="all")
        status_combo = ttk.Combobox(top_frame, textvariable=self.status_var,
                                    values=["all", "pending", "completed"],
                                    state="readonly", width=10)
        status_combo.pack(side=tk.LEFT, padx=5)
        status_combo.bind('<<ComboboxSelected>>', self.on_filter_change)
        
        # Filter by type
        ttk.Label(top_frame, text="Type:").pack(side=tk.LEFT, padx=(20, 5))
        self.type_var = tk.StringVar(value="all")
        type_combo = ttk.Combobox(top_frame, textvariable=self.type_var,
                                  values=["all", "Work", "Personal", "Shopping", "Health", "Finance", "Other"],
                                  state="readonly", width=10)
        type_combo.pack(side=tk.LEFT, padx=5)
        type_combo.bind('<<ComboboxSelected>>', self.on_filter_change)
        
        # Filter by priority
        ttk.Label(top_frame, text="Priority:").pack(side=tk.LEFT, padx=(20, 5))
        self.priority_var = tk.StringVar(value="all")
        priority_combo = ttk.Combobox(top_frame, textvariable=self.priority_var,
                                      values=["all", "Low", "Medium", "High"],
                                      state="readonly", width=8)
        priority_combo.pack(side=tk.LEFT, padx=5)
        priority_combo.bind('<<ComboboxSelected>>', self.on_filter_change)
        
        # Middle section - Task list
        middle_frame = ttk.Frame(right_panel)
        middle_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Treeview for tasks
        columns = ("id", "title", "type", "priority", "completed", "created_at", "to_do_at", "time_block", "project")
        self.task_tree = ttk.Treeview(middle_frame, columns=columns, show="headings", selectmode="extended")
        
        # Define headings
        self.task_tree.heading("id", text="ID")
        self.task_tree.heading("title", text="Title")
        self.task_tree.heading("type", text="Type")
        self.task_tree.heading("priority", text="Priority")
        self.task_tree.heading("completed", text="Completed")
        self.task_tree.heading("created_at", text="Created At")
        self.task_tree.heading("to_do_at", text="Due Date")
        self.task_tree.heading("time_block", text="Time Block")
        self.task_tree.heading("project", text="Project")
        
        # Define column widths
        self.task_tree.column("id", width=50)
        self.task_tree.column("title", width=250)
        self.task_tree.column("type", width=80)
        self.task_tree.column("priority", width=70)
        self.task_tree.column("completed", width=80)
        self.task_tree.column("created_at", width=120)
        self.task_tree.column("to_do_at", width=120)
        self.task_tree.column("time_block", width=80)
        self.task_tree.column("project", width=100)
        
        # Scrollbars
        tree_scroll_y = ttk.Scrollbar(middle_frame, orient=tk.VERTICAL, command=self.task_tree.yview)
        tree_scroll_x = ttk.Scrollbar(middle_frame, orient=tk.HORIZONTAL, command=self.task_tree.xview)
        self.task_tree.configure(yscrollcommand=tree_scroll_y.set, xscrollcommand=tree_scroll_x.set)
        
        # Grid layout
        self.task_tree.grid(row=0, column=0, sticky="nsew")
        tree_scroll_y.grid(row=0, column=1, sticky="ns")
        tree_scroll_x.grid(row=1, column=0, sticky="ew")
        
        middle_frame.columnconfigure(0, weight=1)
        middle_frame.rowconfigure(0, weight=1)
        
        # Bottom section - Action buttons
        bottom_frame = ttk.Frame(right_panel)
        bottom_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(bottom_frame, text="Add Task", command=self.add_task).pack(side=tk.LEFT, padx=5)
        ttk.Button(bottom_frame, text="Edit Task", command=self.edit_task).pack(side=tk.LEFT, padx=5)
        ttk.Button(bottom_frame, text="Delete Task", command=self.delete_task).pack(side=tk.LEFT, padx=5)
        ttk.Button(bottom_frame, text="Mark Complete", command=self.toggle_complete).pack(side=tk.LEFT, padx=5)
        ttk.Button(bottom_frame, text="Refresh", command=self.refresh_task_list).pack(side=tk.LEFT, padx=5)
        ttk.Button(bottom_frame, text="Export CSV", command=self.export_csv).pack(side=tk.LEFT, padx=5)
        ttk.Button(bottom_frame, text="Export TXT", command=self.export_txt).pack(side=tk.LEFT, padx=5)
        
        # Week navigation
        week_frame = ttk.LabelFrame(right_panel, text="Week Navigation", padding="5")
        week_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(week_frame, text="< Previous Week", command=self.prev_week).pack(side=tk.LEFT, padx=5)
        self.week_label = ttk.Label(week_frame, text="", font=("Arial", 10, "bold"))
        self.week_label.pack(side=tk.LEFT, padx=20)
        ttk.Button(week_frame, text="Next Week >", command=self.next_week).pack(side=tk.LEFT, padx=5)
        ttk.Button(week_frame, text="Current Week", command=self.go_to_current_week).pack(side=tk.LEFT, padx=5)
        
        # Project progress section
        project_frame = ttk.LabelFrame(right_panel, text="Project Progress", padding="5")
        project_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.project_progress_tree = ttk.Treeview(project_frame, columns=("project", "total", "completed", "progress"), 
                                                   show="headings", height=4)
        self.project_progress_tree.heading("project", text="Project")
        self.project_progress_tree.heading("total", text="Total")
        self.project_progress_tree.heading("completed", text="Completed")
        self.project_progress_tree.heading("progress", text="Progress")
        
        self.project_progress_tree.column("project", width=150)
        self.project_progress_tree.column("total", width=60)
        self.project_progress_tree.column("completed", width=80)
        self.project_progress_tree.column("progress", width=100)
        
        self.project_progress_tree.pack(fill=tk.X)
        
        # Status bar
        self.status_bar = ttk.Label(right_panel, text="Ready", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(fill=tk.X, padx=10, pady=2)
        
        # Bind double-click to edit
        self.task_tree.bind('<Double-1>', lambda e: self.edit_task())
        
        # Update week label
        self.update_week_label()
    
    def on_calendar_date_select(self, date):
        """Handle calendar date selection"""
        self.status_bar.config(text=f"Selected date: {date}")
        self.refresh_task_list()
    
    def on_search_change(self, event=None):
        """Handle search input change"""
        self.search_query = self.search_entry.get().strip().lower()
        self.refresh_task_list()
    
    def on_filter_change(self, event=None):
        """Handle filter changes"""
        self.current_filter = self.status_var.get()
        self.current_type_filter = self.type_var.get()
        self.current_priority_filter = self.priority_var.get()
        self.refresh_task_list()
    
    def refresh_task_list(self):
        """Refresh the task list from database"""
        # Clear existing items
        for item in self.task_tree.get_children():
            self.task_tree.delete(item)
        
        # Build query based on filters
        query = "SELECT * FROM tasks WHERE 1=1"
        params = []
        
        # Filter by status
        if self.current_filter == "pending":
            query += " AND completed = 0"
        elif self.current_filter == "completed":
            query += " AND completed = 1"
        
        # Filter by type
        if self.current_type_filter != "all":
            query += " AND type = ?"
            params.append(self.current_type_filter)
        
        # Filter by priority
        if self.current_priority_filter != "all":
            query += " AND priority = ?"
            params.append(self.current_priority_filter)
        
        # Filter by selected date
        if hasattr(self, 'calendar') and self.calendar.selected_date:
            # Show tasks for the selected date and its containing week/month
            selected = self.calendar.selected_date
            query += " AND (DATE(to_do_at) = ? OR time_block_type IN ('week', 'month', 'year'))"
            params.append(selected.isoformat())
        
        # Search filter
        if self.search_query:
            query += " AND (LOWER(title) LIKE ? OR LOWER(description) LIKE ? OR LOWER(tags) LIKE ?)"
            search_param = f"%{self.search_query}%"
            params.extend([search_param, search_param, search_param])
        
        query += " ORDER BY priority DESC, to_do_at ASC, created_at DESC"
        
        try:
            cursor = self.db.execute(query, params)
            tasks = cursor.fetchall()
            
            for task in tasks:
                completed_str = "Yes" if task['completed'] else "No"
                
                # Determine display style based on priority
                tags = ()
                if task['priority'] == "High":
                    tags = ("high.TLabel",)
                elif task['priority'] == "Medium":
                    tags = ("medium.TLabel",)
                else:
                    tags = ("low.TLabel",)
                
                self.task_tree.insert("", tk.END, iid=task['id'],
                                     values=(task['id'], task['title'], task['type'], 
                                            task['priority'], completed_str,
                                            task['created_at'], task['to_do_at'],
                                            task['time_block_type'], task['project_name']),
                                     tags=tags)
            
            self.status_bar.config(text=f"Showing {len(tasks)} task(s)")
            
            # Update project progress
            self.update_project_progress()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load tasks: {e}")
    
    def update_project_progress(self):
        """Update project progress display"""
        # Clear existing items
        for item in self.project_progress_tree.get_children():
            self.project_progress_tree.delete(item)
        
        try:
            cursor = self.db.execute('''
                SELECT project_name, 
                       COUNT(*) as total,
                       SUM(CASE WHEN completed = 1 THEN 1 ELSE 0 END) as completed
                FROM tasks 
                WHERE project_name IS NOT NULL AND project_name != ''
                GROUP BY project_name
            ''')
            
            for row in cursor.fetchall():
                if row['project_name']:
                    progress = (row['completed'] / row['total'] * 100) if row['total'] > 0 else 0
                    self.project_progress_tree.insert("", tk.END,
                                                      values=(row['project_name'], row['total'],
                                                             row['completed'], f"{progress:.1f}%"))
        except Exception as e:
            pass
    
    def update_calendar_tasks(self):
        """Update calendar with days that have tasks"""
        try:
            cursor = self.db.execute("SELECT DATE(to_do_at) as date FROM tasks WHERE to_do_at IS NOT NULL")
            dates = {datetime.strptime(row['date'], '%Y-%m-%d').date() for row in cursor.fetchall() if row['date']}
            self.calendar.set_days_with_tasks(dates)
        except Exception as e:
            pass
    
    def add_task(self):
        """Open task editor to add a new task"""
        editor = TaskEditor(self.root, self.db, on_save_callback=self.refresh_and_update)
    
    def edit_task(self):
        """Edit selected task"""
        selected = self.task_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a task to edit")
            return
        
        if len(selected) > 1:
            messagebox.showwarning("Warning", "Please select only one task to edit")
            return
        
        task_id = int(selected[0])
        
        try:
            cursor = self.db.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
            task_data = dict(cursor.fetchone())
            
            if task_data:
                editor = TaskEditor(self.root, self.db, task_data=task_data, 
                                   on_save_callback=self.refresh_and_update)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load task: {e}")
    
    def delete_task(self):
        """Delete selected task(s)"""
        selected = self.task_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select task(s) to delete")
            return
        
        confirm = messagebox.askyesno("Confirm Delete", 
                                     f"Are you sure you want to delete {len(selected)} task(s)?")
        if not confirm:
            return
        
        try:
            for item in selected:
                task_id = int(item)
                self.db.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
            
            self.db.commit()
            self.refresh_and_update()
            self.status_bar.config(text=f"Deleted {len(selected)} task(s)")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete task(s): {e}")
    
    def toggle_complete(self):
        """Toggle completion status of selected task(s)"""
        selected = self.task_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select task(s)")
            return
        
        try:
            for item in selected:
                task_id = int(item)
                
                # Get current status
                cursor = self.db.execute("SELECT completed FROM tasks WHERE id = ?", (task_id,))
                task = cursor.fetchone()
                
                if task:
                    new_status = 0 if task['completed'] else 1
                    self.db.execute("UPDATE tasks SET completed = ? WHERE id = ?", (new_status, task_id))
            
            self.db.commit()
            self.refresh_and_update()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update task(s): {e}")
    
    def refresh_and_update(self):
        """Refresh task list and update calendar"""
        self.refresh_task_list()
        self.update_calendar_tasks()
    
    def export_csv(self):
        """Export tasks to CSV file"""
        file_path = filedialog.asksaveasfilename(defaultextension=".csv",
                                                 filetypes=[("CSV files", "*.csv")],
                                                 title="Export to CSV")
        if not file_path:
            return
        
        try:
            cursor = self.db.execute("SELECT * FROM tasks")
            tasks = cursor.fetchall()
            
            if tasks:
                fieldnames = tasks[0].keys()
                
                with open(file_path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    for task in tasks:
                        writer.writerow(dict(task))
                
                messagebox.showinfo("Success", f"Exported {len(tasks)} task(s) to {file_path}")
                self.status_bar.config(text=f"Exported to {file_path}")
            else:
                messagebox.showinfo("Info", "No tasks to export")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export: {e}")
    
    def export_txt(self):
        """Export tasks to TXT file"""
        file_path = filedialog.asksaveasfilename(defaultextension=".txt",
                                                 filetypes=[("Text files", "*.txt")],
                                                 title="Export to TXT")
        if not file_path:
            return
        
        try:
            cursor = self.db.execute("SELECT * FROM tasks ORDER BY priority DESC, to_do_at ASC")
            tasks = cursor.fetchall()
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write("TODO LIST EXPORT\n")
                f.write("=" * 50 + "\n\n")
                f.write(f"Exported: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
                f.write(f"Total Tasks: {len(tasks)}\n\n")
                
                # Group by completion status
                pending = [t for t in tasks if not t['completed']]
                completed = [t for t in tasks if t['completed']]
                
                if pending:
                    f.write("PENDING TASKS\n")
                    f.write("-" * 50 + "\n")
                    for i, task in enumerate(pending, 1):
                        f.write(f"{i}. [{task['priority']}] {task['title']}\n")
                        if task['to_do_at']:
                            f.write(f"   Due: {task['to_do_at']}\n")
                        if task['description']:
                            f.write(f"   Description: {task['description']}\n")
                        if task['project_name']:
                            f.write(f"   Project: {task['project_name']}\n")
                        if task['tags']:
                            f.write(f"   Tags: {task['tags']}\n")
                        f.write("\n")
                
                if completed:
                    f.write("\nCOMPLETED TASKS\n")
                    f.write("-" * 50 + "\n")
                    for i, task in enumerate(completed, 1):
                        f.write(f"{i}. [{task['priority']}] {task['title']}\n")
                        if task['to_do_at']:
                            f.write(f"   Due: {task['to_do_at']}\n")
                        f.write("\n")
            
            messagebox.showinfo("Success", f"Exported {len(tasks)} task(s) to {file_path}")
            self.status_bar.config(text=f"Exported to {file_path}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export: {e}")
    
    def prev_week(self):
        """Navigate to previous week"""
        self.current_week_start -= timedelta(weeks=1)
        self.update_week_label()
        self.refresh_task_list()
    
    def next_week(self):
        """Navigate to next week"""
        self.current_week_start += timedelta(weeks=1)
        self.update_week_label()
        self.refresh_task_list()
    
    def go_to_current_week(self):
        """Go to current week"""
        self.current_week_start = datetime.now() - timedelta(days=datetime.now().weekday())
        self.update_week_label()
        self.refresh_task_list()
    
    def update_week_label(self):
        """Update the week label"""
        week_end = self.current_week_start + timedelta(days=6)
        self.week_label.config(
            text=f"{self.current_week_start.strftime('%b %d')} - {week_end.strftime('%b %d, %Y')}"
        )
    
    def load_config(self) -> dict:
        """Load application configuration"""
        if os.path.exists(CONFIG_PATH):
            try:
                with open(CONFIG_PATH, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {}
    
    def save_config(self):
        """Save application configuration"""
        config = {
            'geometry': self.root.geometry(),
            'current_week': self.current_week_start.isoformat()
        }
        
        try:
            with open(CONFIG_PATH, 'w') as f:
                json.dump(config, f)
        except Exception as e:
            print(f"Failed to save config: {e}")
    
    def on_close(self):
        """Handle application close"""
        self.save_config()
        self.db.close()
        self.root.destroy()


def main():
    """Main entry point"""
    root = tk.Tk()
    app = TodoApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
