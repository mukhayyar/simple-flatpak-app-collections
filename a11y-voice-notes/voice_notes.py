#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Gst', '1.0')
from gi.repository import Gtk, GLib, Gst
import os, time, threading, json

Gst.init(None)

NOTES_FILE = os.path.expanduser("~/.local/share/voice-notes/notes.json")

def ensure_dir():
    os.makedirs(os.path.dirname(NOTES_FILE), exist_ok=True)

def load_notes():
    ensure_dir()
    try:
        with open(NOTES_FILE) as f:
            return json.load(f)
    except Exception:
        return []

def save_notes(notes):
    ensure_dir()
    with open(NOTES_FILE, 'w') as f:
        json.dump(notes, f, indent=2)

class VoiceNotesWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("Voice Notes")
        self.set_default_size(800, 580)
        self.notes = load_notes()
        self.recording = False
        self.playing = False
        self.rec_pipeline = None
        self.play_pipeline = None
        self.rec_start = 0
        self.rec_timer = None
        self.build_ui()

    def build_ui(self):
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        vbox.set_margin_top(8); vbox.set_margin_bottom(8)
        vbox.set_margin_start(8); vbox.set_margin_end(8)
        self.set_child(vbox)

        vbox.append(Gtk.Label(label="Voice Notes", css_classes=["title"]))

        hpaned = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
        vbox.append(hpaned)

        # Left: notes list
        left = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        left.set_size_request(260, -1)
        left.set_margin_top(4); left.set_margin_start(4)
        left.set_margin_end(4); left.set_margin_bottom(4)

        left.append(Gtk.Label(label="Recordings", css_classes=["heading"]))

        scroll = Gtk.ScrolledWindow()
        scroll.set_vexpand(True)
        self.notes_store = Gtk.ListStore(str, str, str)  # id, title, date
        self.notes_view = Gtk.TreeView(model=self.notes_store)
        self.notes_view.set_headers_visible(True)
        for i, title in enumerate(["Title", "Date"]):
            col = Gtk.TreeViewColumn(title, Gtk.CellRendererText(), text=i+1)
            col.set_resizable(True)
            self.notes_view.append_column(col)
        self.notes_view.get_selection().connect("changed", self.on_note_selected)
        scroll.set_child(self.notes_view)
        left.append(scroll)

        list_btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        del_btn = Gtk.Button(label="Delete")
        del_btn.connect("clicked", self.on_delete)
        del_btn.add_css_class("destructive-action")
        list_btn_box.append(del_btn)
        left.append(list_btn_box)

        hpaned.set_start_child(left)

        # Right: recorder + player
        right = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        right.set_margin_top(4); right.set_margin_start(4)
        right.set_margin_end(4); right.set_margin_bottom(4)

        # Recording
        rec_frame = Gtk.Frame(label="Record New Note")
        rec_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        rec_box.set_margin_top(8); rec_box.set_margin_start(12)
        rec_box.set_margin_end(12); rec_box.set_margin_bottom(8)

        title_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        title_box.append(Gtk.Label(label="Title:"))
        self.title_entry = Gtk.Entry()
        self.title_entry.set_placeholder_text("Note title...")
        self.title_entry.set_hexpand(True)
        title_box.append(self.title_entry)
        rec_box.append(title_box)

        self.rec_label = Gtk.Label(label="Ready to record")
        self.rec_label.set_markup("<span font='20'>🎙 Ready</span>")
        rec_box.append(self.rec_label)

        self.rec_timer_label = Gtk.Label(label="00:00")
        self.rec_timer_label.set_markup("<span font='24' weight='bold'>00:00</span>")
        rec_box.append(self.rec_timer_label)

        self.level_bar = Gtk.LevelBar()
        self.level_bar.set_min_value(0)
        self.level_bar.set_max_value(1)
        self.level_bar.set_value(0)
        rec_box.append(self.level_bar)

        rec_btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        rec_btn_box.set_halign(Gtk.Align.CENTER)
        self.rec_btn = Gtk.Button(label="⏺ Record")
        self.rec_btn.set_size_request(100, 40)
        self.rec_btn.add_css_class("suggested-action")
        self.rec_btn.connect("clicked", self.on_record_toggle)
        rec_btn_box.append(self.rec_btn)
        rec_box.append(rec_btn_box)
        rec_frame.set_child(rec_box)
        right.append(rec_frame)

        # Playback
        play_frame = Gtk.Frame(label="Playback")
        play_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        play_box.set_margin_top(8); play_box.set_margin_start(12)
        play_box.set_margin_end(12); play_box.set_margin_bottom(8)

        self.play_title = Gtk.Label(label="No note selected")
        play_box.append(self.play_title)

        play_btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        play_btn_box.set_halign(Gtk.Align.CENTER)
        self.play_btn = Gtk.Button(label="▶ Play")
        self.play_btn.connect("clicked", self.on_play)
        self.play_btn.set_sensitive(False)
        play_btn_box.append(self.play_btn)
        stop_btn = Gtk.Button(label="■ Stop")
        stop_btn.connect("clicked", self.on_stop_play)
        play_btn_box.append(stop_btn)
        play_box.append(play_btn_box)

        # Notes / transcript
        play_box.append(Gtk.Label(label="Notes:", xalign=0))
        self.notes_text = Gtk.TextView()
        self.notes_text.set_wrap_mode(Gtk.WrapMode.WORD)
        notes_scroll = Gtk.ScrolledWindow()
        notes_scroll.set_min_content_height(100)
        notes_scroll.set_vexpand(True)
        notes_scroll.set_child(self.notes_text)
        play_box.append(notes_scroll)

        save_notes_btn = Gtk.Button(label="Save Notes")
        save_notes_btn.connect("clicked", self.on_save_notes)
        play_box.append(save_notes_btn)
        play_frame.set_child(play_box)
        right.append(play_frame)

        hpaned.set_end_child(right)

        self.status_label = Gtk.Label(label="", xalign=0)
        vbox.append(self.status_label)

        self.populate_list()

    def get_rec_dir(self):
        d = os.path.expanduser("~/.local/share/voice-notes")
        os.makedirs(d, exist_ok=True)
        return d

    def populate_list(self):
        self.notes_store.clear()
        for note in self.notes:
            self.notes_store.append([note['id'], note['title'], note['date']])

    def on_note_selected(self, selection):
        model, iter_ = selection.get_selected()
        if not iter_:
            return
        note_id = model.get_value(iter_, 0)
        note = next((n for n in self.notes if n['id'] == note_id), None)
        if note:
            self.play_title.set_text(note['title'])
            self.notes_text.get_buffer().set_text(note.get('text_notes', ''))
            self.play_btn.set_sensitive(True)
            self._selected_note = note
        else:
            self._selected_note = None

    def on_record_toggle(self, btn):
        if self.recording:
            self.stop_recording()
        else:
            self.start_recording()

    def start_recording(self):
        title = self.title_entry.get_text().strip() or f"Note {time.strftime('%H%M%S')}"
        note_id = f"note_{int(time.time())}"
        path = os.path.join(self.get_rec_dir(), f"{note_id}.ogg")
        try:
            pipeline_str = (
                f"autoaudiosrc ! audioconvert ! audioresample ! "
                f"vorbisenc ! oggmux ! filesink location={path}"
            )
            self.rec_pipeline = Gst.parse_launch(pipeline_str)
            self.rec_pipeline.set_state(Gst.State.PLAYING)
            self.recording = True
            self.rec_start = time.time()
            self._rec_path = path
            self._rec_title = title
            self._rec_id = note_id
            self.rec_btn.set_label("⏹ Stop")
            self.rec_btn.remove_css_class("suggested-action")
            self.rec_btn.add_css_class("destructive-action")
            self.rec_timer = GLib.timeout_add(500, self.update_rec_timer)
            self.status_label.set_text(f"Recording to: {path}")
        except Exception as e:
            self.status_label.set_text(f"Recording error: {e}")

    def stop_recording(self):
        self.recording = False
        if self.rec_timer:
            GLib.source_remove(self.rec_timer)
            self.rec_timer = None
        if self.rec_pipeline:
            self.rec_pipeline.send_event(Gst.Event.new_eos())
            GLib.timeout_add(500, self._finalize_recording)

    def _finalize_recording(self):
        if self.rec_pipeline:
            self.rec_pipeline.set_state(Gst.State.NULL)
            self.rec_pipeline = None
        duration = int(time.time() - self.rec_start)
        note = {
            'id': self._rec_id,
            'title': self._rec_title,
            'path': self._rec_path,
            'date': time.strftime('%Y-%m-%d %H:%M'),
            'duration': duration,
            'text_notes': '',
        }
        self.notes.append(note)
        save_notes(self.notes)
        self.populate_list()
        self.rec_btn.set_label("⏺ Record")
        self.rec_btn.remove_css_class("destructive-action")
        self.rec_btn.add_css_class("suggested-action")
        self.rec_timer_label.set_markup("<span font='24' weight='bold'>00:00</span>")
        self.status_label.set_text(f"Saved: {self._rec_title} ({duration}s)")
        return False

    def update_rec_timer(self):
        if not self.recording:
            return False
        elapsed = int(time.time() - self.rec_start)
        m, s = divmod(elapsed, 60)
        self.rec_timer_label.set_markup(f"<span font='24' weight='bold' color='red'>{m:02d}:{s:02d}</span>")
        return True

    def on_play(self, btn):
        if not hasattr(self, '_selected_note') or not self._selected_note:
            return
        path = self._selected_note.get('path', '')
        if not os.path.exists(path):
            self.status_label.set_text(f"File not found: {path}")
            return
        self.on_stop_play(None)
        try:
            pipeline_str = f"filesrc location={path} ! oggdemux ! vorbisdec ! audioconvert ! autoaudiosink"
            self.play_pipeline = Gst.parse_launch(pipeline_str)
            bus = self.play_pipeline.get_bus()
            bus.add_signal_watch()
            bus.connect("message::eos", lambda b, m: self.on_stop_play(None))
            self.play_pipeline.set_state(Gst.State.PLAYING)
            self.status_label.set_text(f"Playing: {self._selected_note['title']}")
        except Exception as e:
            self.status_label.set_text(f"Playback error: {e}")

    def on_stop_play(self, btn):
        if self.play_pipeline:
            self.play_pipeline.set_state(Gst.State.NULL)
            self.play_pipeline = None
        self.status_label.set_text("Stopped")

    def on_save_notes(self, btn):
        if not hasattr(self, '_selected_note') or not self._selected_note:
            return
        buf = self.notes_text.get_buffer()
        text = buf.get_text(buf.get_start_iter(), buf.get_end_iter(), False)
        for note in self.notes:
            if note['id'] == self._selected_note['id']:
                note['text_notes'] = text
                break
        save_notes(self.notes)
        self.status_label.set_text("Notes saved")

    def on_delete(self, btn):
        model, iter_ = self.notes_view.get_selection().get_selected()
        if not iter_:
            return
        note_id = model.get_value(iter_, 0)
        note = next((n for n in self.notes if n['id'] == note_id), None)
        if note:
            path = note.get('path', '')
            if path and os.path.exists(path):
                try:
                    os.remove(path)
                except Exception:
                    pass
            self.notes = [n for n in self.notes if n['id'] != note_id]
            save_notes(self.notes)
            self.populate_list()
            self.play_btn.set_sensitive(False)
            self.status_label.set_text("Note deleted")

class VoiceNotesApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.pens.VoiceNotes")
    def do_activate(self):
        win = VoiceNotesWindow(self); win.present()

def main():
    app = VoiceNotesApp(); app.run(None)

if __name__ == "__main__":
    main()
