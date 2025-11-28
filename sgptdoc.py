import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
import uuid
from pathlib import Path

# --- 🎨 SETTINGS --- #
APP_NAME = "NotePad"

# Get Documents folder path
DOCUMENTS_FOLDER = Path.home() / "Documents"
NOTES_FOLDER = DOCUMENTS_FOLDER / "StickyNotes"
DATA_FILE = NOTES_FOLDER / "stickynotes_data.json"

# Colors: (Background, Accent, Text, Hover)
COLOR_THEMES = {
    "Yellow": ("#fff475", "#fff9c4", "#202124", "#fff176"),
    "Green":  ("#ccff90", "#e6ffc1", "#202124", "#b3ff8f"),
    "Pink":   ("#fdcfe8", "#ffeef8", "#202124", "#ffcce6"),
    "Purple": ("#d7aefb", "#ecd4ff", "#202124", "#d0a5ff"),
    "Blue":   ("#cbf0f8", "#e5faff", "#202124", "#b3e9ff"),
    "Gray":   ("#e6e6e6", "#f2f2f2", "#202124", "#d9d9d9"),
}

DEFAULT_THEME = "Yellow"
SMALL_SIZE = (280, 300)
BIG_SIZE = (500, 450)


class NoteManager:
    def __init__(self):
        self.root = tk.Tk()
        self.root.withdraw()

        # Create notes folder if it doesn't exist
        self.create_notes_folder()

        self.open_windows = []
        self.load_notes()

        if not self.open_windows:
            self.create_new_note()

        self.root.mainloop()

    def create_notes_folder(self):
        """Create the StickyNotes folder in Documents if it doesn't exist"""
        try:
            NOTES_FOLDER.mkdir(exist_ok=True)
            print(f"Notes folder created at: {NOTES_FOLDER}")
        except Exception as e:
            print(f"Error creating notes folder: {e}")

    def create_new_note(self, note_data=None):
        new_window = NoteWindow(self, note_data)
        self.open_windows.append(new_window)

    def delete_note(self, window_instance):
        if window_instance in self.open_windows:
            self.open_windows.remove(window_instance)
            self.save_all_notes()
            window_instance.destroy()
            if not self.open_windows:
                self.root.destroy()

    def save_all_notes(self):
        """Save all notes data to JSON file in Documents/StickyNotes folder"""
        all_data = []
        for window in self.open_windows:
            all_data.append(window.get_data())

        try:
            with open(DATA_FILE, 'w', encoding='utf-8') as f:
                json.dump(all_data, f, indent=4, ensure_ascii=False)
            print(f"Notes saved to: {DATA_FILE}")
        except Exception as e:
            print(f"Error saving notes: {e}")
            # Fallback: try to save in current directory
            try:
                with open("stickynotes_backup.json", 'w', encoding='utf-8') as f:
                    json.dump(all_data, f, indent=4, ensure_ascii=False)
                print("Backup saved to current directory")
            except Exception as e2:
                print(f"Backup also failed: {e2}")

    def load_notes(self):
        """Load notes from JSON file in Documents/StickyNotes folder"""
        if DATA_FILE.exists():
            try:
                with open(DATA_FILE, 'r', encoding='utf-8') as f:
                    data_list = json.load(f)
                    if isinstance(data_list, list):
                        for note_data in data_list:
                            self.create_new_note(note_data)
                print(f"Notes loaded from: {DATA_FILE}")
            except Exception as e:
                print(f"Error loading notes: {e}")
                # Try to load from backup
                try:
                    backup_file = Path("stickynotes_backup.json")
                    if backup_file.exists():
                        with open(backup_file, 'r', encoding='utf-8') as f:
                            data_list = json.load(f)
                            if isinstance(data_list, list):
                                for note_data in data_list:
                                    self.create_new_note(note_data)
                        print("Notes loaded from backup")
                except Exception as e2:
                    print(f"Backup load also failed: {e2}")


class HoverButton(tk.Button):
    """Enhanced Button with hover effects"""

    def __init__(self, master, **kwargs):
        self.hover_bg = kwargs.pop('hover_bg', None)
        self.default_bg = kwargs.get('bg', '#f0f0f0')

        super().__init__(master, **kwargs)

        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)

        # Style for flat appearance
        self.config(relief="flat", bd=1, cursor="hand2",
                    activebackground=self.default_bg)

    def on_enter(self, event):
        if self.hover_bg:
            self.config(bg=self.hover_bg)

    def on_leave(self, event):
        self.config(bg=self.default_bg)


class NoteWindow(tk.Toplevel):
    def __init__(self, manager, data=None):
        super().__init__()
        self.manager = manager
        self.overrideredirect(False)
        self.attributes("-topmost", True)
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.title("Sticky Note")

        self.uid = "S" + str(uuid.uuid4()).replace("-", "")

        # Load Data
        if data is None:
            data = {}
        self.note_id = data.get("id", str(uuid.uuid4()))
        self.current_theme = data.get("theme", DEFAULT_THEME)
        self.notes_content = data.get("notes", "")
        self.todo_items = data.get("todo", [])
        x, y = data.get("pos", (50, 50))
        w, h = data.get("size", SMALL_SIZE)
        self.geometry(f"{w}x{h}+{x}+{y}")
        self.is_expanded = (w > SMALL_SIZE[0] + 50)

        # Initial Colors
        self.bg_color, self.accent_color, self.text_color, self.hover_color = COLOR_THEMES[
            self.current_theme]
        self.config(bg=self.bg_color)

        # --- ENHANCED CUSTOM TOP BAR ---
        self.top_bar = tk.Frame(self, bg=self.bg_color, height=35)
        self.top_bar.pack(side="top", fill="x")
        self.top_bar.pack_propagate(False)

        # Add a subtle shadow line under top bar
        self.shadow_line = tk.Frame(self, height=1, bg=self.accent_color)
        self.shadow_line.pack(side="top", fill="x")

        self.setup_enhanced_menus()

        # --- NOTEBOOK ---
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(expand=True, fill="both", padx=0, pady=0)

        self.create_note_page()
        self.create_todo_page()

        # Apply Theme
        self.apply_theme(self.current_theme)

        # Insert initial content after theme is applied
        if self.notes_content:
            self.text_area.insert("1.0", self.notes_content)

        # Bindings for auto-save
        self.bind("<Double-Button-1>", self.toggle_size)
        self.bind("<FocusOut>", self.auto_save)
        # Save when window is moved/resized
        self.bind("<Configure>", self.auto_save)

        # Auto-save when content changes
        self.text_area.bind("<KeyRelease>", self.auto_save)

        self.animating = False

    def auto_save(self, event=None):
        """Auto-save when user makes changes"""
        self.manager.save_all_notes()

    def setup_enhanced_menus(self):
        # File Menu Button with hover effects
        self.mb_file = HoverButton(self.top_bar, text="📁 File",
                                   command=self.show_file_menu,
                                   bg=self.bg_color, fg=self.text_color,
                                   hover_bg=self.hover_color,
                                   font=("Segoe UI", 9, "bold"))
        self.mb_file.pack(side="left", padx=(10, 0), pady=5)

        # Color Menu Button
        self.mb_color = HoverButton(self.top_bar, text="🎨 Color",
                                    command=self.show_color_menu,
                                    bg=self.bg_color, fg=self.text_color,
                                    hover_bg=self.hover_color,
                                    font=("Segoe UI", 9, "bold"))
        self.mb_color.pack(side="left", padx=(5, 0), pady=5)

        # Remove the standalone export button from top bar
        # Add resize button
        self.resize_btn = HoverButton(self.top_bar, text="⛶ Resize",
                                      command=self.toggle_size,
                                      bg=self.bg_color, fg=self.text_color,
                                      hover_bg=self.hover_color,
                                      font=("Segoe UI", 9))
        self.resize_btn.pack(side="right", padx=(0, 10), pady=5)

        # Create menus (initially hidden)
        self.file_menu = tk.Menu(self, tearoff=0, bg=self.accent_color, fg=self.text_color,
                                 font=("Segoe UI", 9), bd=1, relief="solid")
        self.file_menu.add_command(
            label="➕ New Note", command=self.manager.create_new_note)
        self.file_menu.add_separator()
        self.file_menu.add_command(
            label="💾 Export This Note", command=self.export_note)
        self.file_menu.add_command(
            label="📂 Open Notes Folder", command=self.open_notes_folder)
        self.file_menu.add_separator()
        self.file_menu.add_command(
            label="🗑 Delete Note", command=self.delete_self)

        self.color_menu = tk.Menu(self, tearoff=0, bg=self.accent_color, fg=self.text_color,
                                  font=("Segoe UI", 9), bd=1, relief="solid")
        for t_name in COLOR_THEMES:
            bg_color = COLOR_THEMES[t_name][0]
            self.color_menu.add_command(
                label=f"● {t_name}",
                command=lambda t=t_name: self.apply_theme(t),
                background=bg_color,
                activebackground=COLOR_THEMES[t_name][3]
            )

    def show_file_menu(self):
        try:
            self.file_menu.tk_popup(
                self.mb_file.winfo_rootx(),
                self.mb_file.winfo_rooty() + self.mb_file.winfo_height()
            )
        finally:
            self.file_menu.grab_release()

    def show_color_menu(self):
        try:
            self.color_menu.tk_popup(
                self.mb_color.winfo_rootx(),
                self.mb_color.winfo_rooty() + self.mb_color.winfo_height()
            )
        finally:
            self.color_menu.grab_release()

    def export_note(self):
        """Export individual note to a separate JSON file"""
        try:
            # Create individual note file name
            note_filename = f"note_{self.note_id[:8]}.json"
            note_filepath = NOTES_FOLDER / note_filename

            note_data = self.get_data()

            with open(note_filepath, 'w', encoding='utf-8') as f:
                json.dump(note_data, f, indent=4, ensure_ascii=False)

            messagebox.showinfo("Export Successful",
                                f"Note exported to:\n{note_filepath}")
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export note: {e}")

    def open_notes_folder(self):
        """Open the StickyNotes folder in file explorer"""
        try:
            os.startfile(NOTES_FOLDER)  # Windows
        except:
            try:
                import subprocess
                subprocess.run(['open', NOTES_FOLDER])  # macOS
            except:
                try:
                    subprocess.run(['xdg-open', NOTES_FOLDER])  # Linux
                except:
                    messagebox.showinfo("Notes Folder",
                                        f"Notes are saved in:\n{NOTES_FOLDER}")

    def apply_theme(self, theme_name):
        self.current_theme = theme_name
        self.bg_color, self.accent_color, self.text_color, self.hover_color = COLOR_THEMES[
            theme_name]

        # Update all UI elements
        self.config(bg=self.bg_color)
        self.top_bar.config(bg=self.bg_color)
        self.shadow_line.config(bg=self.accent_color)

        # Update hover buttons
        for btn in [self.mb_file, self.mb_color, self.resize_btn]:
            btn.config(bg=self.bg_color, fg=self.text_color)
            btn.hover_bg = self.hover_color
            btn.default_bg = self.bg_color

        # Update menus
        self.file_menu.config(bg=self.accent_color, fg=self.text_color)
        self.color_menu.config(bg=self.accent_color, fg=self.text_color)

        for i, t_name in enumerate(COLOR_THEMES):
            bg_color = COLOR_THEMES[t_name][0]
            self.color_menu.entryconfig(i,
                                        background=bg_color,
                                        activebackground=COLOR_THEMES[t_name][3])

        # Notebook Style
        style = ttk.Style()
        style.theme_use('clam')
        nb_style = f"{self.uid}.TNotebook"
        tab_style = f"{self.uid}.TNotebook.Tab"

        style.configure(nb_style, background=self.bg_color, borderwidth=0)
        style.configure(tab_style,
                        background=self.accent_color,
                        foreground=self.text_color,
                        padding=[20, 8],
                        borderwidth=0,
                        focuscolor=self.bg_color,
                        font=("Segoe UI", 9, "bold"))
        style.map(tab_style,
                  background=[('selected', self.bg_color)],
                  foreground=[('selected', self.text_color)])
        self.notebook.config(style=nb_style)

        # Update Content Widgets
        if hasattr(self, 'note_frame'):
            self.note_frame.config(bg=self.bg_color)
        if hasattr(self, 'text_area'):
            self.text_area.config(bg=self.bg_color, fg=self.text_color,
                                  insertbackground=self.text_color)

        # Update To-Do section - COMPLETELY recreate the todo list items with new colors
        if hasattr(self, 'todo_frame'):
            self.todo_frame.config(bg=self.bg_color)
        if hasattr(self, 'todo_list'):
            # Get current items
            current_items = list(self.todo_list.get(0, tk.END))
            # Clear and recreate the listbox with proper colors
            self.todo_list.config(bg=self.bg_color, fg=self.text_color,
                                  selectbackground=self.hover_color,
                                  selectforeground=self.text_color)
            # Clear all items and reinsert them to apply new colors
            self.todo_list.delete(0, tk.END)
            for item in current_items:
                self.todo_list.insert(tk.END, item)

        if hasattr(self, 'todo_right_frame'):
            self.todo_right_frame.config(bg=self.bg_color)
        if hasattr(self, 'todo_entry'):
            self.todo_entry.config(bg=self.accent_color, fg=self.text_color,
                                   insertbackground=self.text_color)
        if hasattr(self, 'add_btn'):
            self.add_btn.config(bg=self.accent_color, fg=self.text_color)
            self.add_btn.hover_bg = self.hover_color
            self.add_btn.default_bg = self.accent_color
        if hasattr(self, 'done_btn'):
            self.done_btn.config(bg=self.accent_color, fg=self.text_color)
            self.done_btn.hover_bg = self.hover_color
            self.done_btn.default_bg = self.accent_color

        # Save after theme change
        self.manager.save_all_notes()

    def create_note_page(self):
        self.note_frame = tk.Frame(self.notebook, bg=self.bg_color)
        self.notebook.add(self.note_frame, text="📝 Notes")

        text_container = tk.Frame(self.note_frame, bg=self.bg_color)
        text_container.pack(expand=True, fill="both", padx=10, pady=10)

        self.text_area = tk.Text(text_container, wrap="word", bd=0,
                                 font=("Segoe UI", 11), padx=12, pady=12,
                                 bg=self.bg_color, fg=self.text_color,
                                 selectbackground=self.hover_color,
                                 relief="flat",
                                 highlightbackground=self.accent_color,
                                 highlightcolor=self.accent_color,
                                 highlightthickness=1)
        self.text_area.pack(expand=True, fill="both")

    def create_todo_page(self):
        self.todo_frame = tk.Frame(self.notebook, bg=self.bg_color)
        self.notebook.add(self.todo_frame, text="✅ To-Do")

        main_container = tk.Frame(self.todo_frame, bg=self.bg_color)
        main_container.pack(expand=True, fill="both", padx=10, pady=10)

        # Left side - Todo list WITHOUT scrollbar
        list_container = tk.Frame(main_container, bg=self.bg_color)
        list_container.pack(side="left", expand=True, fill="both")

        # Todo list - SIMPLIFIED without borders and scrollbar
        self.todo_list = tk.Listbox(list_container, bd=0,
                                    font=("Segoe UI", 11), activestyle='none',
                                    bg=self.bg_color, fg=self.text_color,
                                    selectbackground=self.hover_color,
                                    relief="flat",
                                    highlightthickness=0)  # Remove border

        # NO SCROLLBAR - Simple packing
        self.todo_list.pack(side="left", expand=True, fill="both")

        for item in self.todo_items:
            self.todo_list.insert(tk.END, item)

        # Right side - Controls
        self.todo_right_frame = tk.Frame(main_container, bg=self.bg_color)
        self.todo_right_frame.pack(side="right", fill="y", padx=(10, 0))

        # Enhanced entry with placeholder - SIMPLIFIED border
        self.todo_entry = tk.Entry(self.todo_right_frame, width=18, bd=0,
                                   highlightthickness=0, relief="flat",  # Remove border
                                   bg=self.accent_color, fg=self.text_color,
                                   font=("Segoe UI", 10),
                                   insertbackground=self.text_color)
        self.todo_entry.insert(0, "New task...")
        self.todo_entry.config(fg="#666666")
        self.todo_entry.bind("<FocusIn>", lambda e: self.clear_placeholder())
        self.todo_entry.bind(
            "<FocusOut>", lambda e: self.restore_placeholder())
        # Enter key to add task
        self.todo_entry.bind("<Return>", lambda e: self.add_todo())
        self.todo_entry.pack(pady=(0, 8))

        # Enhanced buttons
        self.add_btn = HoverButton(self.todo_right_frame, text="➕ Add",
                                   command=self.add_todo,
                                   bg=self.accent_color, fg=self.text_color,
                                   hover_bg=self.hover_color,
                                   font=("Segoe UI", 9, "bold"),
                                   width=12, height=1)
        self.add_btn.pack(pady=4, fill="x")

        self.done_btn = HoverButton(self.todo_right_frame, text="✅ Done",
                                    command=self.delete_todo_item,
                                    bg=self.accent_color, fg=self.text_color,
                                    hover_bg=self.hover_color,
                                    font=("Segoe UI", 9, "bold"),
                                    width=12, height=1)
        self.done_btn.pack(pady=4, fill="x")

    def clear_placeholder(self):
        if self.todo_entry.get() == "New task...":
            self.todo_entry.delete(0, tk.END)
            self.todo_entry.config(fg=self.text_color)

    def restore_placeholder(self):
        if not self.todo_entry.get().strip():
            self.todo_entry.insert(0, "New task...")
            self.todo_entry.config(fg="#666666")

    def add_todo(self):
        item = self.todo_entry.get().strip()
        if item and item != "New task...":
            self.todo_list.insert(tk.END, "● " + item)
            self.todo_entry.delete(0, tk.END)
            self.restore_placeholder()
            self.manager.save_all_notes()  # Auto-save after adding task

    def delete_todo_item(self):
        for i in reversed(self.todo_list.curselection()):
            self.todo_list.delete(i)
        self.manager.save_all_notes()  # Auto-save after deleting task

    def delete_self(self):
        if messagebox.askyesno(APP_NAME, "Delete this note permanently?"):
            self.manager.delete_note(self)

    def toggle_size(self, event=None):
        if self.animating:
            return

        self.animating = True
        if self.is_expanded:
            self.geometry(f"{SMALL_SIZE[0]}x{SMALL_SIZE[1]}")
        else:
            self.geometry(f"{BIG_SIZE[0]}x{BIG_SIZE[1]}")
        self.is_expanded = not self.is_expanded
        self.animating = False
        self.manager.save_all_notes()  # Auto-save after resizing

    def get_data(self):
        return {
            "id": self.note_id,
            "theme": self.current_theme,
            "notes": self.text_area.get("1.0", tk.END).strip(),
            "todo": list(self.todo_list.get(0, tk.END)),
            "pos": (self.winfo_x(), self.winfo_y()),
            "size": (self.winfo_width(), self.winfo_height())
        }

    def on_close(self):
        self.manager.save_all_notes()  # Auto-save when closing
        self.destroy()
        if self in self.manager.open_windows:
            self.manager.open_windows.remove(self)
        if not self.manager.open_windows:
            self.manager.root.destroy()


if __name__ == "__main__":
    NoteManager()
