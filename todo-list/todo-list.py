#!/usr/bin/env python3
import sys
import sqlite3
import os
import gi
import datetime

gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib, Gdk, Pango

class GamifiedTodoWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("Focus Quest")
        self.set_default_size(800, 600)

        # --- Database Setup ---
        self.data_dir = GLib.get_user_data_dir()
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
        self.db_path = os.path.join(self.data_dir, "quest_db.sqlite")
        self.init_db()
        
        # --- State ---
        self.selected_quest = None # Currently viewed quest in Dashboard

        # --- Styling ---
        self.apply_css()
        self.add_css_class("main-window")

        # --- Main Layout ---
        main_hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        self.set_child(main_hbox)

        # 1. Sidebar
        self.sidebar = self.create_sidebar()
        main_hbox.append(self.sidebar)

        # 2. Main Content Stack
        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self.stack.set_hexpand(True)
        main_hbox.append(self.stack)

        # --- Stack Pages ---
        
        # Page A: Quest List (NEW - Shows all active quests)
        self.quest_list_box = self.create_quest_list_ui()
        self.stack.add_named(self.quest_list_box, "quest_list")

        # Page B: Setup
        self.setup_box = self.create_setup_ui()
        self.stack.add_named(self.setup_box, "setup")

        # Page C: Dashboard
        self.dashboard_box = self.create_dashboard_ui()
        self.stack.add_named(self.dashboard_box, "dashboard")
        
        # Page D: History List
        self.history_box = self.create_history_ui()
        self.stack.add_named(self.history_box, "history")

        # Page E: History Details
        self.history_details_box = self.create_history_details_ui()
        self.stack.add_named(self.history_details_box, "history_details")

        # Initial View Logic
        self.refresh_quest_list()
        self.stack.set_visible_child_name("quest_list")

    # ==========================================
    #               DATABASE LOGIC
    # ==========================================

    def init_db(self):
        """Initialize SQLite tables."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('''CREATE TABLE IF NOT EXISTS active_quest (
            id INTEGER PRIMARY KEY,
            name TEXT,
            companion_type TEXT,
            xp INTEGER,
            start_date TEXT
        )''')
        
        c.execute('''CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY,
            quest_id INTEGER,
            history_id INTEGER,
            text TEXT,
            is_done INTEGER
        )''')
        
        try:
            c.execute("ALTER TABLE tasks ADD COLUMN history_id INTEGER")
        except sqlite3.OperationalError:
            pass 
        
        c.execute('''CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY,
            name TEXT,
            companion_type TEXT,
            final_xp INTEGER,
            status TEXT,
            end_date TEXT
        )''')
        
        conn.commit()
        conn.close()

    def get_all_active_quests(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT * FROM active_quest")
        rows = [dict(r) for r in c.fetchall()]
        conn.close()
        return rows

    def load_quest_data(self, quest_id):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        c.execute("SELECT * FROM active_quest WHERE id=?", (quest_id,))
        row = c.fetchone()
        
        data = None
        if row:
            data = dict(row)
            c.execute("SELECT * FROM tasks WHERE quest_id=?", (quest_id,))
            data['tasks'] = [dict(t) for t in c.fetchall()]
            
        conn.close()
        return data

    def create_new_quest_in_db(self, name, companion):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # MULTI-TASK UPDATE: Do NOT delete old quests here.
        
        c.execute("INSERT INTO active_quest (name, companion_type, xp, start_date) VALUES (?, ?, ?, ?)",
                  (name, companion, 0, datetime.datetime.now().isoformat()))
        quest_id = c.lastrowid
        
        conn.commit()
        conn.close()
        return quest_id

    def add_task_db(self, quest_id, text):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("INSERT INTO tasks (quest_id, text, is_done) VALUES (?, ?, 0)", 
                  (quest_id, text))
        task_id = c.lastrowid
        conn.commit()
        conn.close()
        return {"id": task_id, "quest_id": quest_id, "text": text, "is_done": 0}

    def update_task_db(self, task_id, is_done):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("UPDATE tasks SET is_done=? WHERE id=?", (1 if is_done else 0, task_id))
        conn.commit()
        conn.close()

    def update_xp_db(self, quest_id, new_xp):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("UPDATE active_quest SET xp=? WHERE id=?", (new_xp, quest_id))
        conn.commit()
        conn.close()

    def archive_quest(self, quest_id, status):
        """Moves a specific quest to history."""
        quest_data = self.load_quest_data(quest_id)
        if not quest_data: return

        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # 1. Create History Record
        c.execute('''INSERT INTO history (name, companion_type, final_xp, status, end_date) 
                     VALUES (?, ?, ?, ?, ?)''',
                  (quest_data['name'], 
                   quest_data['companion_type'], 
                   quest_data['xp'], 
                   status, 
                   datetime.datetime.now().strftime("%Y-%m-%d %H:%M")))
        history_id = c.lastrowid
        
        # 2. Update Tasks
        c.execute("UPDATE tasks SET history_id=?, quest_id=NULL WHERE quest_id=?", 
                  (history_id, quest_id))
        
        # 3. Delete from active
        c.execute("DELETE FROM active_quest WHERE id=?", (quest_id,))
        
        conn.commit()
        conn.close()

    def get_history_details(self, history_id):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        c.execute("SELECT * FROM history WHERE id=?", (history_id,))
        quest_row = c.fetchone()
        
        c.execute("SELECT * FROM tasks WHERE history_id=?", (history_id,))
        tasks = [dict(t) for t in c.fetchall()]
        
        conn.close()
        
        if quest_row:
            data = dict(quest_row)
            data['tasks'] = tasks
            return data
        return None

    # ==========================================
    #               UI CREATION
    # ==========================================

    def create_sidebar(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.add_css_class("sidebar")
        box.set_size_request(200, -1)

        title = Gtk.Label(label="MENU")
        title.add_css_class("sidebar-title")
        box.append(title)

        self.nav_list = Gtk.ListBox()
        self.nav_list.add_css_class("nav-list")
        self.nav_list.connect("row-activated", self.on_nav_clicked)
        box.append(self.nav_list)

        # Active Quests
        row1 = Gtk.ListBoxRow()
        lbl1 = Gtk.Label(label="⚔️  Active Quests")
        lbl1.set_xalign(0)
        row1.set_child(lbl1)
        row1.view_name = "quest_list"
        self.nav_list.append(row1)

        # History
        row2 = Gtk.ListBoxRow()
        lbl2 = Gtk.Label(label="📜  History")
        lbl2.set_xalign(0)
        row2.set_child(lbl2)
        row2.view_name = "history"
        self.nav_list.append(row2)

        return box

    def create_quest_list_ui(self):
        """Shows list of active quests + New Quest button."""
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        box.set_margin_top(20)
        box.set_margin_bottom(20)
        box.set_margin_start(20)
        box.set_margin_end(20)

        # Header
        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        box.append(header)
        
        lbl = Gtk.Label(label="Your Adventures")
        lbl.add_css_class("setup-title")
        lbl.set_hexpand(True)
        lbl.set_halign(Gtk.Align.START)
        header.append(lbl)

        new_btn = Gtk.Button(label="+ New Quest")
        new_btn.add_css_class("complete-btn") # Reuse green style
        new_btn.connect("clicked", lambda x: self.stack.set_visible_child_name("setup"))
        header.append(new_btn)

        # Scrollable List
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        box.append(scrolled)

        self.active_quests_listbox = Gtk.ListBox()
        self.active_quests_listbox.add_css_class("history-list") # Reuse style
        self.active_quests_listbox.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.active_quests_listbox.connect("row-activated", self.on_active_quest_clicked)
        scrolled.set_child(self.active_quests_listbox)

        return box

    def create_setup_ui(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        box.set_halign(Gtk.Align.CENTER)
        box.set_valign(Gtk.Align.CENTER)
        
        lbl = Gtk.Label(label="Start New Quest")
        lbl.add_css_class("setup-title")
        box.append(lbl)

        self.quest_entry = Gtk.Entry()
        self.quest_entry.set_placeholder_text("What is your main goal?")
        self.quest_entry.set_width_chars(25)
        self.quest_entry.add_css_class("setup-entry")
        box.append(self.quest_entry)

        lbl2 = Gtk.Label(label="Choose Companion:")
        lbl2.add_css_class("setup-subtitle")
        box.append(lbl2)

        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=20)
        hbox.set_halign(Gtk.Align.CENTER)
        box.append(hbox)

        btn_dragon = Gtk.Button(label="🐉\nDragon")
        btn_dragon.add_css_class("companion-btn")
        btn_dragon.connect("clicked", self.on_start_adventure, "dragon")
        hbox.append(btn_dragon)

        btn_tree = Gtk.Button(label="🌳\nTree")
        btn_tree.add_css_class("companion-btn")
        btn_tree.connect("clicked", self.on_start_adventure, "tree")
        hbox.append(btn_tree)

        # Cancel Button
        cancel_btn = Gtk.Button(label="Cancel")
        cancel_btn.add_css_class("reset-btn")
        cancel_btn.connect("clicked", lambda x: self.stack.set_visible_child_name("quest_list"))
        box.append(cancel_btn)

        return box

    def create_dashboard_ui(self):
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        
        # Header (Back button + Game Stats)
        self.header_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        self.header_box.add_css_class("game-header")
        main_box.append(self.header_box)
        
        nav_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        back_btn = Gtk.Button(label="⬅ Quest List")
        back_btn.add_css_class("key-btn-wide")
        back_btn.connect("clicked", lambda x: self.stack.set_visible_child_name("quest_list") or self.refresh_quest_list())
        nav_box.append(back_btn)
        self.header_box.append(nav_box)

        self.companion_label = Gtk.Label(label="🥚")
        self.companion_label.add_css_class("companion-emoji")
        self.header_box.append(self.companion_label)

        self.status_label = Gtk.Label(label="Stage 1")
        self.status_label.add_css_class("status-label")
        self.header_box.append(self.status_label)

        self.progress_bar = Gtk.ProgressBar()
        self.progress_bar.set_show_text(True)
        self.progress_bar.add_css_class("xp-bar")
        self.header_box.append(self.progress_bar)

        info_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        info_box.set_halign(Gtk.Align.CENTER)
        self.header_box.append(info_box)

        self.quest_title = Gtk.Label(label="Main Quest")
        self.quest_title.add_css_class("quest-title")
        info_box.append(self.quest_title)

        # Task List
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        main_box.append(scrolled)

        self.list_box = Gtk.ListBox()
        self.list_box.add_css_class("task-list")
        self.list_box.set_selection_mode(Gtk.SelectionMode.NONE)
        scrolled.set_child(self.list_box)

        # Input Area
        input_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        input_box.add_css_class("input-area")
        main_box.append(input_box)

        kb_btn = Gtk.Button(label="⌨️")
        kb_btn.add_css_class("key-btn")
        kb_btn.set_can_focus(False)
        kb_btn.connect("clicked", self.toggle_keyboard)
        input_box.append(kb_btn)

        self.entry = Gtk.Entry()
        self.entry.set_placeholder_text("Add a sub-task...")
        self.entry.set_hexpand(True)
        self.entry.connect("activate", self.on_add_task)
        
        focus_controller = Gtk.EventControllerFocus()
        focus_controller.connect("enter", self.show_keyboard)
        self.entry.add_controller(focus_controller)

        input_box.append(self.entry)

        add_btn = Gtk.Button(label="+")
        add_btn.add_css_class("add-btn")
        add_btn.connect("clicked", self.on_add_task)
        input_box.append(add_btn)

        # Virtual Keyboard
        self.keyboard_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        self.keyboard_box.add_css_class("keyboard-area")
        self.keyboard_box.set_visible(False)
        main_box.append(self.keyboard_box)
        self.build_virtual_keyboard()

        # Action Buttons
        action_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=20)
        action_box.set_halign(Gtk.Align.CENTER)
        action_box.set_margin_top(10)
        action_box.set_margin_bottom(10)
        self.keyboard_box.append(action_box)

        complete_btn = Gtk.Button(label="✅ Complete Quest")
        complete_btn.add_css_class("complete-btn")
        complete_btn.connect("clicked", self.on_complete_quest)
        action_box.append(complete_btn)

        reset_btn = Gtk.Button(label="🏳️ Give Up")
        reset_btn.add_css_class("reset-btn")
        reset_btn.connect("clicked", self.on_give_up_quest)
        action_box.append(reset_btn)

        return main_box

    def create_history_ui(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_margin_top(20)
        box.set_margin_bottom(20)
        box.set_margin_start(20)
        box.set_margin_end(20)

        lbl = Gtk.Label(label="Quest History")
        lbl.add_css_class("setup-title")
        box.append(lbl)
        
        lbl_hint = Gtk.Label(label="(Click a quest to view tasks)")
        lbl_hint.add_css_class("history-hint")
        box.append(lbl_hint)

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        box.append(scrolled)

        self.history_list_box = Gtk.ListBox()
        self.history_list_box.add_css_class("history-list")
        self.history_list_box.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.history_list_box.connect("row-activated", self.on_history_item_clicked)
        scrolled.set_child(self.history_list_box)
        
        return box

    def create_history_details_ui(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_margin_top(20)
        box.set_margin_bottom(20)
        box.set_margin_start(20)
        box.set_margin_end(20)

        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        box.append(header)

        back_btn = Gtk.Button(label="⬅ Back")
        back_btn.add_css_class("key-btn-wide")
        back_btn.connect("clicked", self.on_back_to_history)
        header.append(back_btn)

        self.details_title = Gtk.Label(label="Quest Details")
        self.details_title.add_css_class("setup-title")
        self.details_title.set_hexpand(True)
        header.append(self.details_title)
        
        self.details_stats = Gtk.Label(label="")
        self.details_stats.add_css_class("status-label")
        box.append(self.details_stats)

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        box.append(scrolled)

        self.details_list_box = Gtk.ListBox()
        self.details_list_box.add_css_class("task-list")
        self.details_list_box.set_selection_mode(Gtk.SelectionMode.NONE)
        scrolled.set_child(self.details_list_box)

        return box

    # ==========================================
    #           LOGIC
    # ==========================================

    def on_nav_clicked(self, listbox, row):
        if row.view_name == "history":
            self.load_history()
            self.stack.set_visible_child_name("history")
        elif row.view_name == "quest_list":
            self.refresh_quest_list()
            self.stack.set_visible_child_name("quest_list")

    # --- Active Quest List Logic ---
    def refresh_quest_list(self):
        # Clear list
        while True:
            row = self.active_quests_listbox.get_row_at_index(0)
            if row is None: break
            self.active_quests_listbox.remove(row)
        
        quests = self.get_all_active_quests()
        if not quests:
            # Show placeholder?
            pass
            
        for q in quests:
            row = Gtk.ListBoxRow()
            row.quest_id = q['id']
            
            box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=15)
            box.add_css_class("history-row") # Reuse card style
            
            # Icon based on companion type
            icon = "🐲" if q['companion_type'] == 'dragon' else "🌳"
            icon_lbl = Gtk.Label(label=icon)
            icon_lbl.add_css_class("companion-emoji")
            # Scale down emoji for list
            icon_lbl.set_markup(f"<span size='xx-large'>{icon}</span>")
            box.append(icon_lbl)
            
            vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            vbox.set_hexpand(True)
            
            name_lbl = Gtk.Label(label=q['name'])
            name_lbl.set_halign(Gtk.Align.START)
            name_lbl.add_css_class("history-name")
            
            xp_lbl = Gtk.Label(label=f"XP: {q['xp']}")
            xp_lbl.set_halign(Gtk.Align.START)
            xp_lbl.add_css_class("history-date")
            
            vbox.append(name_lbl)
            vbox.append(xp_lbl)
            box.append(vbox)
            
            # Arrow
            arrow = Gtk.Label(label="▶")
            box.append(arrow)
            
            row.set_child(box)
            self.active_quests_listbox.append(row)

    def on_active_quest_clicked(self, listbox, row):
        quest_id = row.quest_id
        # Load this quest into dashboard
        self.selected_quest = self.load_quest_data(quest_id)
        self.refresh_dashboard()
        self.stack.set_visible_child_name("dashboard")

    def on_start_adventure(self, btn, type_name):
        goal = self.quest_entry.get_text().strip()
        if not goal: return
        
        new_id = self.create_new_quest_in_db(goal, type_name)
        # Load the new quest directly
        self.selected_quest = self.load_quest_data(new_id)
        self.refresh_dashboard()
        self.stack.set_visible_child_name("dashboard")
        
        self.quest_entry.set_text("")

    # --- Dashboard Logic ---
    def refresh_dashboard(self):
        if not self.selected_quest: return
        
        self.refresh_companion()
        self.load_tasks_to_ui()

    def load_tasks_to_ui(self):
        while True:
            row = self.list_box.get_row_at_index(0)
            if row is None: break
            self.list_box.remove(row)
            
        if self.selected_quest and 'tasks' in self.selected_quest:
            for task in self.selected_quest['tasks']:
                row = self.create_task_row(task)
                self.list_box.append(row)

    def on_add_task(self, widget):
        text = self.entry.get_text().strip()
        if text and self.selected_quest:
            new_task = self.add_task_db(self.selected_quest['id'], text)
            # Add to local state
            self.selected_quest['tasks'].append(new_task)
            
            row = self.create_task_row(new_task)
            self.list_box.append(row)
            self.entry.set_text("")
            self.keyboard_box.set_visible(False)

    def on_task_toggled(self, check, row):
        is_done = check.get_active()
        task_id = row.task_data['id']
        self.update_task_db(task_id, is_done)
        
        # Update local state
        for t in self.selected_quest['tasks']:
            if t['id'] == task_id:
                t['is_done'] = 1 if is_done else 0
        
        current_xp = self.selected_quest['xp']
        if is_done:
            new_xp = current_xp + 25
        else:
            new_xp = max(0, current_xp - 25)
            
        self.update_xp_db(self.selected_quest['id'], new_xp)
        self.selected_quest['xp'] = new_xp
        self.refresh_companion()
        
        box = row.get_child()
        label = box.get_last_child().get_prev_sibling() 
        label.set_attributes(self.get_strike_attrs() if is_done else None)

    def on_complete_quest(self, btn):
        if self.selected_quest:
            self.archive_quest(self.selected_quest['id'], "completed")
            self.selected_quest = None
            self.refresh_quest_list()
            self.stack.set_visible_child_name("quest_list")

    def on_give_up_quest(self, btn):
        if self.selected_quest:
            self.archive_quest(self.selected_quest['id'], "abandoned")
            self.selected_quest = None
            self.refresh_quest_list()
            self.stack.set_visible_child_name("quest_list")

    # --- History Logic ---
    def load_history(self):
        while True:
            row = self.history_list_box.get_row_at_index(0)
            if row is None: break
            self.history_list_box.remove(row)
            
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT * FROM history ORDER BY id DESC")
        rows = c.fetchall()
        conn.close()
        
        for item in rows:
            row = Gtk.ListBoxRow()
            row.history_id = item['id']
            
            box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            box.add_css_class("history-row")
            
            status_icon = "🏆" if item['status'] == 'completed' else "💀"
            icon_lbl = Gtk.Label(label=status_icon)
            box.append(icon_lbl)
            
            vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            name_lbl = Gtk.Label(label=item['name'])
            name_lbl.set_halign(Gtk.Align.START)
            name_lbl.add_css_class("history-name")
            
            date_lbl = Gtk.Label(label=f"{item['end_date']} | XP: {item['final_xp']}")
            date_lbl.set_halign(Gtk.Align.START)
            date_lbl.add_css_class("history-date")
            
            vbox.append(name_lbl)
            vbox.append(date_lbl)
            box.append(vbox)
            
            row.set_child(box)
            self.history_list_box.append(row)

    def on_history_item_clicked(self, listbox, row):
        history_id = row.history_id
        details = self.get_history_details(history_id)
        
        if details:
            self.details_title.set_label(f"Quest: {details['name']}")
            status_icon = "🏆" if details['status'] == 'completed' else "💀"
            self.details_stats.set_label(f"{status_icon} {details['status'].upper()} | Final XP: {details['final_xp']}")
            
            while True:
                r = self.details_list_box.get_row_at_index(0)
                if r is None: break
                self.details_list_box.remove(r)
                
            for task in details['tasks']:
                row = Gtk.ListBoxRow()
                box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
                box.add_css_class("task-row")
                
                check_lbl = Gtk.Label(label="☑" if task['is_done'] else "☐")
                box.append(check_lbl)
                
                label = Gtk.Label(label=task['text'])
                label.set_hexpand(True)
                label.set_halign(Gtk.Align.START)
                if task['is_done']: 
                    label.set_attributes(self.get_strike_attrs())
                box.append(label)
                
                row.set_child(box)
                self.details_list_box.append(row)
                
            self.stack.set_visible_child_name("history_details")

    def on_back_to_history(self, btn):
        self.stack.set_visible_child_name("history")

    # --- Companion Logic ---

    def get_companion_stage(self):
        xp = self.selected_quest['xp'] if self.selected_quest else 0
        ctype = self.selected_quest['companion_type'] if self.selected_quest else 'dragon'
        
        if ctype == "dragon":
            stages = [
                (0, "🥚", "Egg", "css-stage-1"),
                (20, "🐣", "Hatchling", "css-stage-2"),
                (50, "🐲", "Young", "css-stage-3"),
                (90, "🐉", "Ancient", "css-stage-4")
            ]
        else: 
            stages = [
                (0, "🌱", "Seed", "css-stage-1"),
                (20, "🌿", "Sapling", "css-stage-2"),
                (50, "🪴", "Tree", "css-stage-3"),
                (90, "🌳", "Elder Tree", "css-stage-4")
            ]
            
        current = stages[0]
        next_xp = stages[1][0]
        
        for i, stage in enumerate(stages):
            if xp >= stage[0]:
                current = stage
                if i < len(stages) - 1:
                    next_xp = stages[i+1][0]
                else:
                    next_xp = 9999 
        return current, next_xp

    def refresh_companion(self):
        if not self.selected_quest: return
        self.quest_title.set_label(f"Quest: {self.selected_quest['name']}")
        
        stage_info, next_xp = self.get_companion_stage()
        self.companion_label.set_label(stage_info[1])
        self.status_label.set_label(f"{stage_info[2]} (XP: {self.selected_quest['xp']})")
        
        for i in range(1, 5):
            self.companion_label.remove_css_class(f"css-stage-{i}")
        self.companion_label.add_css_class(stage_info[3])

        if next_xp == 9999:
            self.progress_bar.set_fraction(1.0)
            self.progress_bar.set_text("MAX LEVEL")
        else:
            fraction = min(self.selected_quest['xp'] / next_xp, 1.0)
            self.progress_bar.set_fraction(fraction)
            self.progress_bar.set_text(f"{self.selected_quest['xp']} / {next_xp} XP")

    # --- Helper UI Methods ---

    def create_task_row(self, task_data):
        row = Gtk.ListBoxRow()
        row.task_data = task_data
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        box.add_css_class("task-row")
        
        check = Gtk.CheckButton()
        check.set_active(task_data["is_done"])
        check.connect("toggled", self.on_task_toggled, row)
        box.append(check)

        label = Gtk.Label(label=task_data["text"])
        label.set_hexpand(True)
        label.set_halign(Gtk.Align.START)
        if task_data["is_done"]: label.set_attributes(self.get_strike_attrs())
        box.append(label)
        
        row.set_child(box)
        return row

    def get_strike_attrs(self):
        attr_list = Pango.AttrList()
        attr_list.insert(Pango.attr_strikethrough_new(True))
        return attr_list
        
    def build_virtual_keyboard(self):
        rows = ["1234567890", "QWERTYUIOP", "ASDFGHJKL", "ZXCVBNM"]
        for row_chars in rows:
            row_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
            row_box.set_halign(Gtk.Align.CENTER)
            self.keyboard_box.append(row_box)
            for char in row_chars:
                btn = Gtk.Button(label=char)
                btn.add_css_class("key-btn")
                btn.set_can_focus(False) 
                btn.connect("clicked", self.on_key_press, char)
                row_box.append(btn)
        
        bbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        bbox.set_halign(Gtk.Align.CENTER)
        self.keyboard_box.append(bbox)
        
        spc = Gtk.Button(label="SPACE")
        spc.add_css_class("key-btn-wide")
        spc.set_can_focus(False)
        spc.connect("clicked", self.on_key_press, " ")
        bbox.append(spc)

        bs = Gtk.Button(label="⌫")
        bs.add_css_class("key-btn-wide")
        bs.add_css_class("key-alert")
        bs.set_can_focus(False)
        bs.connect("clicked", self.on_key_press, "BACKSPACE")
        bbox.append(bs)

        close = Gtk.Button(label="▼")
        close.add_css_class("key-btn")
        close.set_can_focus(False)
        close.connect("clicked", lambda x: self.keyboard_box.set_visible(False))
        bbox.append(close)

    def show_keyboard(self, controller, direction=None):
        self.keyboard_box.set_visible(True)
    
    def hide_keyboard(self, controller, direction=None):
        pass

    def toggle_keyboard(self, btn):
        self.keyboard_box.set_visible(not self.keyboard_box.get_visible())

    def on_key_press(self, btn, char):
        current = self.entry.get_text()
        if char == "BACKSPACE":
            if len(current) > 0: self.entry.set_text(current[:-1])
        else:
            self.entry.set_text(current + char)
        self.entry.set_position(-1)

    def apply_css(self):
        css_provider = Gtk.CssProvider()
        css = b"""
        .main-window { background-color: #1e1e2e; color: #cdd6f4; }
        
        /* Sidebar */
        .sidebar { background-color: #11111b; padding: 15px; border-right: 1px solid #313244; }
        .sidebar-title { font-weight: 900; color: #89b4fa; margin-bottom: 20px; font-size: 14px; letter-spacing: 2px; }
        .nav-list { background: transparent; }
        .nav-list row { padding: 10px; border-radius: 8px; color: #a6adc8; font-weight: bold; }
        .nav-list row:hover { background: #313244; color: white; }
        
        /* Setup */
        .setup-title { font-size: 28px; font-weight: 800; color: #f5c2e7; margin-bottom: 20px; }
        .setup-entry { font-size: 18px; padding: 10px; border-radius: 10px; background: #313244; color: white; border: 2px solid #89b4fa; }
        .companion-btn { font-size: 16px; padding: 15px; margin: 5px; border-radius: 15px; background: #45475a; color: white; font-weight: bold; }
        .companion-btn:hover { background: #89b4fa; color: #1e1e2e; }

        /* Dashboard */
        .game-header { background: #181825; padding: 20px; border-bottom: 2px solid #313244; }
        .companion-emoji { font-size: 80px; }
        .status-label { font-size: 16px; font-weight: bold; color: #f9e2af; }
        .quest-title { font-size: 20px; font-weight: bold; color: #89b4fa; }
        .xp-bar trough { min-height: 10px; border-radius: 5px; background: #313244; }
        .xp-bar progress { border-radius: 5px; background: #a6e3a1; }
        
        /* Action Buttons */
        .complete-btn { background: #a6e3a1; color: #1e1e2e; font-weight: bold; padding: 10px; border-radius: 8px; }
        .reset-btn { background: #f38ba8; color: #1e1e2e; font-weight: bold; padding: 10px; border-radius: 8px; }
        
        /* History */
        .history-row { background: #313244; padding: 15px; border-radius: 10px; margin: 5px; }
        .history-name { font-weight: bold; font-size: 16px; color: white; }
        .history-date { font-size: 12px; color: #bac2de; }
        .history-hint { color: #6c7086; font-size: 12px; margin-bottom: 10px; }
        
        /* Common */
        .task-list { background: transparent; margin: 10px; }
        .task-row { background: #313244; border-radius: 8px; margin-bottom: 5px; padding: 10px; color: #cdd6f4; }
        .input-area { background: #181825; padding: 15px; }
        entry { background: #313244; color: white; border: none; padding: 5px; border-radius: 5px; }
        .add-btn { background: #89b4fa; color: #1e1e2e; font-weight: bold; border-radius: 5px; }
        .key-btn { font-weight: bold; min-width: 40px; min-height: 40px; background: #45475a; color: white; border-radius: 5px; }
        .key-btn:active { background: #89b4fa; color: black; }
        .key-btn-wide { font-weight: bold; min-width: 80px; min-height: 40px; background: #45475a; color: white; border-radius: 5px; }
        .key-alert { color: #f38ba8; }
        """
        css_provider.load_from_data(css)
        Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(), css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

def on_activate(app):
    win = GamifiedTodoWindow(app)
    win.present()
    win.maximize()

if __name__ == "__main__":
    app = Gtk.Application(application_id='com.pens.TodoList')
    app.connect('activate', on_activate)
    app.run(None)