"""
YouTube Channel & Playlist Manager
- GUI using tkinter
- Features:
  * Create Video objects
  * Create Playlists and add/remove videos
  * Save / Load playlists to/from text files and JSON
  * Create Channel, display playlists, search by name
  * Export/import channel (JSON)
  * Polished GOLD × BLACK visual theme
  * Styled Listboxes, programmatic icons, gradient header, and splash screen

Run: python YouTube_Playlist_Manager.py
Requires: Python 3.x (standard library only)
"""
from dataclasses import dataclass, asdict
import json
import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import time
from typing import List

# ----------------- Data Models -----------------
@dataclass
class Video:
    title: str
    duration: int  # seconds
    views: int

    def __str__(self):
        mins, secs = divmod(self.duration, 60)
        dur = f"{mins}m{secs}s" if mins else f"{secs}s"
        return f"{self.title} — {dur} — {self.views} views"

class Playlist:
    def __init__(self, playListName: str, plID: int):
        self.playListName = playListName
        self.plID = plID
        self.videos: List[Video] = []

    def add_video(self, video: Video):
        self.videos.append(video)

    def remove_video(self, index: int):
        if 0 <= index < len(self.videos):
            del self.videos[index]

    def save_playlist_to_file(self, filename: str):
        # each line is a JSON object for a video
        with open(filename, 'w', encoding='utf-8') as f:
            for v in self.videos:
                line = json.dumps(asdict(v), ensure_ascii=False)
                f.write(line + '\n')

    def load_playlist_from_file(self, filename: str):
        self.videos = []
        with open(filename, 'r', encoding='utf-8') as f:
            for line in f:
                if not line.strip():
                    continue
                data = json.loads(line.strip())
                v = Video(data['title'], int(data['duration']), int(data['views']))
                self.add_video(v)

    def to_dict(self):
        return {"playListName": self.playListName, "plID": self.plID,
                "videos": [asdict(v) for v in self.videos]}

    @staticmethod
    def from_dict(d):
        pl = Playlist(d['playListName'], d['plID'])
        for vd in d.get('videos', []):
            pl.add_video(Video(vd['title'], int(vd['duration']), int(vd['views'])))
        return pl

    def __str__(self):
        return f"{self.playListName} (ID: {self.plID}) — {len(self.videos)} videos"

class Channel:
    def __init__(self, name: str = "My Channel"):
        self.name = name
        self.playlists: List[Playlist] = []

    def add_playlist(self, playlist: Playlist):
        self.playlists.append(playlist)

    def display_playlists(self):
        return [str(p) for p in self.playlists]

    def search_playlist(self, name: str):
        name = name.lower()
        for pl in self.playlists:
            if pl.playListName.lower() == name:
                return pl
        return None

    def to_json(self, filename: str):
        with open(filename, 'w', encoding='utf-8') as f:
            obj = {"name": self.name, "playlists": [p.to_dict() for p in self.playlists]}
            json.dump(obj, f, ensure_ascii=False, indent=2)

    def load_json(self, filename: str):
        with open(filename, 'r', encoding='utf-8') as f:
            obj = json.load(f)
            self.name = obj.get('name', self.name)
            self.playlists = [Playlist.from_dict(d) for d in obj.get('playlists', [])]

# ----------------- UI Helpers -----------------
def create_square_icon(size, fg='#FFD700', bg='#000000', inner=False):
    """Create a simple square PhotoImage used as an icon (pure Tkinter)."""
    img = tk.PhotoImage(width=size, height=size)
    # fill background
    pixels = [[bg]*size for _ in range(size)]
    if inner:
        # draw a smaller golden square inside
        pad = max(1, size//6)
        for y in range(pad, size-pad):
            for x in range(pad, size-pad):
                pixels[y][x] = fg
    else:
        for y in range(size):
            for x in range(size):
                pixels[y][x] = fg
    # put pixels
    for y, row in enumerate(pixels):
        img.put('{' + ' '.join(row) + '}', to=(0,y))
    return img

# Gradient drawing on canvas
def draw_horizontal_gradient(canvas, x1, y1, x2, y2, start_color, end_color, steps=100):
    # start_color/end_color are hex '#RRGGBB'
    def hex_to_rgb(h):
        h = h.lstrip('#')
        return tuple(int(h[i:i+2],16) for i in (0,2,4))
    def rgb_to_hex(r,g,b):
        return f'#{r:02x}{g:02x}{b:02x}'
    sr,sg,sb = hex_to_rgb(start_color)
    er,eg,eb = hex_to_rgb(end_color)
    width = x2 - x1
    for i in range(steps):
        frac = i/(steps-1)
        r = int(sr + (er-sr)*frac)
        g = int(sg + (eg-sg)*frac)
        b = int(sb + (eb-sb)*frac)
        color = rgb_to_hex(r,g,b)
        x = x1 + int(width * i/steps)
        canvas.create_rectangle(x, y1, x + int(width/steps)+1, y2, outline='', fill=color)

# Splash screen
class Splash(tk.Toplevel):
    def __init__(self, parent, text='YouTube Manager'):
        super().__init__(parent)
        self.overrideredirect(True)
        w, h = 520, 200
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = (sw - w)//2
        y = (sh - h)//3
        self.geometry(f"{w}x{h}+{x}+{y}")
        self.canvas = tk.Canvas(self, width=w, height=h, highlightthickness=0)
        self.canvas.pack(fill='both', expand=True)
        # gradient gold header
        draw_horizontal_gradient(self.canvas, 0, 0, w, h, '#000000', '#FFD700', steps=120)
        # title
        self.canvas.create_text(w//2, h//2 - 10, text=text, font=('Segoe UI', 22, 'bold'), fill='#000000')
        # subtitle
        self.canvas.create_text(w//2, h//2 + 30, text='Loading...', font=('Segoe UI', 12), fill='#111111')

# ----------------- GUI -----------------
class App(tk.Tk):
    def _apply_style(self):
        style = ttk.Style()
        try:
            style.theme_use('clam')
        except Exception:
            pass

        # === GOLD × BLACK THEME ===
        bg = '#000000'          # Black background
        gold_text = '#FFD700'   # Pure Gold text
        gold_btn = '#DAA520'    # GoldenRod (button color)
        gold_hover = '#B8860B'  # Darker gold for hover
        field_bg = '#0D0D0D'    # Dark input fields

        # Global widget colors
        style.configure('.', background=bg, foreground=gold_text, fieldbackground=field_bg)

        # Buttons
        style.configure('TButton', background=gold_btn, foreground='black', padding=8)
        style.map('TButton', background=[('active', gold_hover)])

        # Labels
        style.configure('TLabel', background=bg, foreground=gold_text)

        # Entry fields
        style.configure('TEntry', fieldbackground=field_bg, foreground=gold_text)

        # Frame color
        style.configure('TFrame', background=bg)

        # Treeview (if used) style
        style.configure('Treeview', background='#0e0e0e', fieldbackground='#0e0e0e', foreground=gold_text)

        self.configure(bg=bg)

    def __init__(self):
        super().__init__()
        # show splash in separate window then continue
        self.withdraw()
        splash = Splash(self, text='YouTube Playlist Manager')
        self.after(1400, splash.destroy)
        self.after(1450, self._start_app)

    def _start_app(self):
        self._apply_style()
        self.deiconify()
        self.title('YouTube Channel & Playlist Manager')
        self.geometry('1000x680')
        self.resizable(True, True)

        self.channel = Channel('Elsayed Channel')
        self.next_playlist_id = 1

        # icons
        self.icon_add = create_square_icon(16, fg='#FFD700', bg='#000000', inner=True)
        self.icon_save = create_square_icon(16, fg='#DAA520', bg='#000000')
        self.icon_load = create_square_icon(16, fg='#FFD700', bg='#000000')

        self._build_ui()

    def _build_ui(self):
        # top gradient header
        header = tk.Canvas(self, height=90, highlightthickness=0)
        header.pack(fill='x')
        draw_horizontal_gradient(header, 0, 0, self.winfo_screenwidth(), 90, '#000000', '#FFD700', steps=160)
        header.create_text(40, 46, anchor='w', text='YouTube Playlist Manager', font=('Segoe UI', 18, 'bold'), fill='#000000')

        # main container
        container = ttk.Frame(self)
        container.pack(fill='both', expand=True, padx=12, pady=(6,12))

        # Main PanedWindow
        pw = ttk.Panedwindow(container, orient='horizontal')
        pw.pack(fill='both', expand=True)

        # Left: Playlists list and controls
        left = ttk.Frame(pw, width=340)
        pw.add(left, weight=1)

        ttk.Label(left, text='Playlists').pack(anchor='w')
        self.playlist_listbox = tk.Listbox(left, height=22, bg='#0d0d0d', fg='#FFD700', selectbackground='#B8860B', bd=0, highlightthickness=0)
        self.playlist_listbox.pack(fill='both', expand=True, pady=(6,8))
        self.playlist_listbox.bind('<<ListboxSelect>>', self.on_playlist_select)

        pl_controls = ttk.Frame(left)
        pl_controls.pack(fill='x', pady=6)
        self.new_playlist_name = tk.StringVar()
        ttk.Entry(pl_controls, textvariable=self.new_playlist_name, width=18).pack(side='left')
        ttk.Button(pl_controls, image=self.icon_add, text=' New', compound='left', command=self.create_playlist).pack(side='left', padx=6)
        ttk.Button(pl_controls, image=self.icon_load, text=' Load', compound='left', command=self.load_playlist_to_selected).pack(side='left', padx=6)
        ttk.Button(pl_controls, image=self.icon_save, text=' Save', compound='left', command=self.save_selected_playlist).pack(side='left', padx=6)

        # Middle: Videos in selected playlist
        mid = ttk.Frame(pw, width=420)
        pw.add(mid, weight=2)

        ttk.Label(mid, text='Videos in Selected Playlist').pack(anchor='w')
        self.video_listbox = tk.Listbox(mid, height=20, bg='#0d0d0d', fg='#FFD700', selectbackground='#B8860B', bd=0, highlightthickness=0)
        self.video_listbox.pack(fill='both', expand=True, pady=(6,8))

        vid_controls = ttk.Frame(mid)
        vid_controls.pack(fill='x', pady=6)
        ttk.Button(vid_controls, text='Remove Video', command=self.remove_video).pack(side='left')
        ttk.Button(vid_controls, text='Export Playlist to File', command=self.export_playlist_file).pack(side='left', padx=6)

        # Right: Add video form & search
        right = ttk.Frame(pw, width=300)
        pw.add(right, weight=1)

        ttk.Label(right, text='Create / Add Video').pack(anchor='w')
        form = ttk.Frame(right)
        form.pack(fill='x', pady=6)

        ttk.Label(form, text='Title:').grid(row=0, column=0, sticky='w')
        self.title_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.title_var, width=28).grid(row=0, column=1)

        ttk.Label(form, text='Duration (sec):').grid(row=1, column=0, sticky='w')
        self.duration_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.duration_var, width=28).grid(row=1, column=1)

        ttk.Label(form, text='Views:').grid(row=2, column=0, sticky='w')
        self.views_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.views_var, width=28).grid(row=2, column=1)

        ttk.Button(form, text='Add to Selected Playlist', command=self.add_video_to_selected).grid(row=3, column=0, columnspan=2, pady=8)

        # Search area
        ttk.Separator(right).pack(fill='x', pady=8)
        ttk.Label(right, text='Search Playlist').pack(anchor='w')
        self.search_var = tk.StringVar()
        ttk.Entry(right, textvariable=self.search_var).pack(fill='x', pady=(6,8))
        ttk.Button(right, text='Search', command=self.search_playlist).pack()

        # Bottom controls
        bottom = ttk.Frame(container)
        bottom.pack(fill='x', pady=(8,0))

        ttk.Button(bottom, text='Rename Channel', command=self.rename_channel).pack(side='left')
        ttk.Button(bottom, text='Save Channel', command=self.save_channel).pack(side='left', padx=6)
        ttk.Button(bottom, text='Load Channel', command=self.load_channel).pack(side='left')

        # Footer status
        self.status_var = tk.StringVar(value='Ready')
        status = ttk.Label(self, textvariable=self.status_var, relief='sunken', anchor='w')
        status.pack(fill='x', side='bottom')

    # ---------- Channel actions ----------
    def rename_channel(self):
        name = self.search_var.get().strip()
        if name:
            self.channel.name = name
            self.status_var.set(f'Channel renamed to: {name}')
        else:
            messagebox.showwarning('Name required', 'Enter a valid channel name.')

    def save_channel(self):
        filename = filedialog.asksaveasfilename(defaultextension='.json', filetypes=[('JSON files','*.json')])
        if not filename:
            return
        try:
            self.channel.to_json(filename)
            self.status_var.set(f'Channel saved to {os.path.basename(filename)}')
        except Exception as e:
            messagebox.showerror('Save Error', str(e))

    def load_channel(self):
        filename = filedialog.askopenfilename(filetypes=[('JSON files','*.json')])
        if not filename:
            return
        try:
            self.channel.load_json(filename)
            # set next id
            self.next_playlist_id = max([p.plID for p in self.channel.playlists], default=0) + 1
            self.refresh_playlists()
            self.status_var.set(f'Channel loaded from {os.path.basename(filename)}')
        except Exception as e:
            messagebox.showerror('Load Error', str(e))

    # ---------- Playlist actions ----------
    def create_playlist(self):
        name = self.new_playlist_name.get().strip() or f'Playlist {self.next_playlist_id}'
        pl = Playlist(name, self.next_playlist_id)
        self.next_playlist_id += 1
        self.channel.add_playlist(pl)
        self.refresh_playlists()
        self.status_var.set(f'Created playlist: {name}')

    def delete_playlist(self):
        sel = self.playlist_listbox.curselection()
        if not sel:
            messagebox.showinfo('Select playlist', 'Choose a playlist to delete.')
            return
        idx = sel[0]
        del self.channel.playlists[idx]
        self.refresh_playlists()
        self.video_listbox.delete(0, 'end')
        self.status_var.set('Playlist deleted')

    def save_selected_playlist(self):
        sel = self.playlist_listbox.curselection()
        if not sel:
            messagebox.showinfo('Select playlist', 'Select a playlist to save.')
            return
        idx = sel[0]
        pl = self.channel.playlists[idx]
        filename = filedialog.asksaveasfilename(defaultextension='.txt', filetypes=[('Text files','*.txt')], initialfile=f"{pl.playListName}.txt")
        if not filename:
            return
        try:
            pl.save_playlist_to_file(filename)
            self.status_var.set(f'Saved playlist to {os.path.basename(filename)}')
        except Exception as e:
            messagebox.showerror('Save Error', str(e))

    def load_playlist_to_selected(self):
        sel = self.playlist_listbox.curselection()
        if not sel:
            messagebox.showinfo('Select playlist', 'Select a playlist to load into.')
            return
        idx = sel[0]
        pl = self.channel.playlists[idx]
        filename = filedialog.askopenfilename(filetypes=[('Text files','*.txt')])
        if not filename:
            return
        try:
            pl.load_playlist_from_file(filename)
            self.on_playlist_select()
            self.status_var.set(f'Loaded playlist from {os.path.basename(filename)}')
        except Exception as e:
            messagebox.showerror('Load Error', str(e))

    def export_playlist_file(self):
        # same as save selected but simple quick export
        self.save_selected_playlist()

    def refresh_playlists(self):
        self.playlist_listbox.delete(0, 'end')
        for p in self.channel.playlists:
            self.playlist_listbox.insert('end', str(p))

    def on_playlist_select(self, event=None):
        sel = self.playlist_listbox.curselection()
        self.video_listbox.delete(0, 'end')
        if not sel:
            return
        idx = sel[0]
        pl = self.channel.playlists[idx]
        for v in pl.videos:
            self.video_listbox.insert('end', str(v))

    # ---------- Video actions ----------
    def add_video_to_selected(self):
        sel = self.playlist_listbox.curselection()
        if not sel:
            messagebox.showinfo('Select playlist', 'Select a playlist first to add video.')
            return
        try:
            title = self.title_var.get().strip()
            duration = int(self.duration_var.get())
            views = int(self.views_var.get())
            if not title:
                raise ValueError('Title required')
        except Exception as e:
            messagebox.showerror('Invalid data', f'Check input: {e}')
            return
        v = Video(title, duration, views)
        idx = sel[0]
        pl = self.channel.playlists[idx]
        pl.add_video(v)
        self.on_playlist_select()
        self.status_var.set(f'Added video to {pl.playListName}')

    def remove_video(self):
        psel = self.playlist_listbox.curselection()
        vsel = self.video_listbox.curselection()
        if not psel or not vsel:
            messagebox.showinfo('Select video', 'Select a video to remove.')
            return
        pidx = psel[0]
        vidx = vsel[0]
        pl = self.channel.playlists[pidx]
        pl.remove_video(vidx)
        self.on_playlist_select()
        self.status_var.set('Video removed')

    def search_playlist(self):
        q = self.search_var.get().strip()
        if not q:
            messagebox.showinfo('Search', 'Enter a playlist name to search.')
            return
        pl = self.channel.search_playlist(q)
        if pl:
            # select it in listbox
            for i, p in enumerate(self.channel.playlists):
                if p is pl:
                    self.playlist_listbox.selection_clear(0, 'end')
                    self.playlist_listbox.selection_set(i)
                    self.playlist_listbox.see(i)
                    self.on_playlist_select()
                    self.status_var.set(f'Found playlist: {pl.playListName}')
                    return
        messagebox.showinfo('Not found', 'Playlist not found')
        self.status_var.set('Search finished — not found')

# ----------------- Run -----------------
if __name__ == '__main__':
    app = App()
    app.mainloop()