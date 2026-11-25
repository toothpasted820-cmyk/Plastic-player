#!/usr/bin/env python3
"""Plastic Player — музыкальный плеер для Linux с сохранением плейлистов"""

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Gst', '1.0')
gi.require_version('GdkPixbuf', '2.0')

from gi.repository import Gtk, Gst, GLib, GdkPixbuf, Gdk
import os
import json

Gst.init(None)

CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".config", "plastic-player")
PLAYLISTS_DIR = os.path.join(CONFIG_DIR, "playlists")
SETTINGS_FILE = os.path.join(CONFIG_DIR, "settings.json")


class PlasticPlayer(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.plastic.player")
        self._updating = False
        self._volume_changing = False
        self.volume_element = None
        self.playlist = []
        self.current_index = -1
        self.cover_image = None
        self.playlists = {}
        self.active_playlist = ""

        os.makedirs(PLAYLISTS_DIR, exist_ok=True)
        self.load_settings()
        # load_all_playlists() вызывается ПОСЛЕ build_ui() в do_activate()

    def do_activate(self):
        self.window = Gtk.ApplicationWindow(application=self)
        self.window.set_title("Plastic Player")
        self.window.set_default_size(800, 500)

        self.player = Gst.ElementFactory.make("playbin", "player")

        audio_sink = Gst.ElementFactory.make("autoaudiosink", "audio_sink")
        volume_elem = Gst.ElementFactory.make("volume", "volume_elem")
        volume_elem.set_property("volume", 1.0)

        audio_bin = Gst.Bin.new("audio_bin")
        audio_bin.add(volume_elem)
        audio_bin.add(audio_sink)
        volume_elem.link(audio_sink)

        sink_pad = volume_elem.get_static_pad("sink")
        ghost_pad = Gst.GhostPad.new("sink", sink_pad)
        audio_bin.add_pad(ghost_pad)

        self.player.set_property("audio-sink", audio_bin)
        self.volume_element = volume_elem

        bus = self.player.get_bus()
        bus.add_signal_watch()
        bus.connect("message::eos", self.on_eos)
        bus.connect("message::error", self.on_error)

        self.build_ui()
        self.setup_hotkeys()
        self.setup_drag_drop()

        # Загружаем плейлисты ПОСЛЕ создания UI
        self.load_all_playlists()

        if self.active_playlist and self.active_playlist in self.playlists:
            self.switch_playlist(self.active_playlist)

        self.window.present()
        GLib.timeout_add(500, self.update_progress)

    def build_ui(self):
        main_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        self.window.set_child(main_box)

        # === ЛЕВАЯ ПАНЕЛЬ ===
        playlist_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        playlist_box.set_margin_top(10)
        playlist_box.set_margin_bottom(10)
        playlist_box.set_margin_start(10)
        playlist_box.set_margin_end(5)
        playlist_box.set_size_request(300, -1)

        # Переключатель плейлистов (DropDown вместо ComboBoxText)
        self.playlist_names = []  # список имён плейлистов
        string_list = Gtk.StringList.new([])
        self.playlist_dropdown = Gtk.DropDown.new(string_list, None)
        self.playlist_dropdown.connect("notify::selected-item", self.on_playlist_changed)
        playlist_box.append(self.playlist_dropdown)

        btn_new_pl = Gtk.Button(label="➕ Новый плейлист")
        btn_new_pl.connect("clicked", self.on_new_playlist)
        playlist_box.append(btn_new_pl)

        playlist_header = Gtk.Label(label="📋 Треки")
        playlist_header.set_halign(Gtk.Align.START)
        playlist_box.append(playlist_header)

        self.playlist_list = Gtk.ListBox()
        self.playlist_list.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.playlist_list.connect("row-activated", self.on_track_activated)

        scroll = Gtk.ScrolledWindow()
        scroll.set_child(self.playlist_list)
        scroll.set_vexpand(True)
        playlist_box.append(scroll)

        btn_box1 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        btn_box1.set_margin_top(5)
        add_btn = Gtk.Button(label="➕ Треки")
        add_btn.connect("clicked", self.on_add_files)
        btn_box1.append(add_btn)
        m3u_btn = Gtk.Button(label="📂 M3U")
        m3u_btn.connect("clicked", self.on_open_m3u)
        btn_box1.append(m3u_btn)
        playlist_box.append(btn_box1)

        btn_box2 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        remove_btn = Gtk.Button(label="🗑 Удалить")
        remove_btn.connect("clicked", self.on_remove_track)
        btn_box2.append(remove_btn)
        save_btn = Gtk.Button(label="💾 Сохранить")
        save_btn.connect("clicked", self.on_save_current_playlist)
        btn_box2.append(save_btn)
        playlist_box.append(btn_box2)

        main_box.append(playlist_box)

        # === ПРАВАЯ ПАНЕЛЬ ===
        control_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        control_box.set_margin_top(20)
        control_box.set_margin_bottom(20)
        control_box.set_margin_start(20)
        control_box.set_margin_end(20)
        control_box.set_hexpand(True)
        main_box.append(control_box)

        # Обложка через Gtk.Picture + Gdk.Texture
        self.cover_image = Gtk.Picture()
        self.cover_image.set_size_request(200, 200)
        self.cover_image.set_halign(Gtk.Align.CENTER)
        self.cover_image.set_valign(Gtk.Align.CENTER)
        self.show_cover_placeholder()
        control_box.append(self.cover_image)

        self.title_label = Gtk.Label(label="Нет выбранного трека")
        self.title_label.set_halign(Gtk.Align.CENTER)
        control_box.append(self.title_label)

        self.progress = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 100, 1)
        self.progress.set_value(0)
        self.progress.connect("value-changed", self.on_progress_changed)
        control_box.append(self.progress)

        self.time_label = Gtk.Label(label="0:00 / 0:00")
        self.time_label.set_halign(Gtk.Align.CENTER)
        control_box.append(self.time_label)

        controls = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        controls.set_halign(Gtk.Align.CENTER)
        controls.set_margin_top(10)
        self.prev_btn = Gtk.Button(label="⏮ Назад")
        self.prev_btn.connect("clicked", self.on_prev)
        controls.append(self.prev_btn)
        self.play_btn = Gtk.Button(label="▶ Играть")
        self.play_btn.connect("clicked", self.on_play)
        controls.append(self.play_btn)
        self.pause_btn = Gtk.Button(label="⏸ Пауза")
        self.pause_btn.connect("clicked", self.on_pause)
        controls.append(self.pause_btn)
        self.stop_btn = Gtk.Button(label="⏹ Стоп")
        self.stop_btn.connect("clicked", self.on_stop)
        controls.append(self.stop_btn)
        self.next_btn = Gtk.Button(label="⏭ Вперёд")
        self.next_btn.connect("clicked", self.on_next)
        controls.append(self.next_btn)
        control_box.append(controls)

        vol_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        vol_box.set_halign(Gtk.Align.CENTER)
        vol_box.set_margin_top(10)
        vol_box.append(Gtk.Label(label="Громкость:"))
        self.volume_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0.0, 2.0, 0.05)
        self.volume_scale.set_value(1.0)
        self.volume_scale.set_hexpand(False)
        self.volume_scale.set_size_request(150, -1)
        self.volume_scale.set_can_focus(False)
        self.volume_scale.connect("value-changed", self.on_volume_changed)
        vol_box.append(self.volume_scale)
        control_box.append(vol_box)

        self.playlist_info = Gtk.Label(label="Треков: 0")
        self.playlist_info.set_halign(Gtk.Align.CENTER)
        control_box.append(self.playlist_info)

    # ========== УПРАВЛЕНИЕ ПЛЕЙЛИСТАМИ ==========

    def load_settings(self):
        try:
            if os.path.exists(SETTINGS_FILE):
                with open(SETTINGS_FILE, 'r') as f:
                    settings = json.load(f)
                    self.active_playlist = settings.get("active_playlist", "")
        except Exception as e:
            print(f"Ошибка загрузки настроек: {e}")

    def save_settings(self):
        try:
            settings = {"active_playlist": self.active_playlist}
            with open(SETTINGS_FILE, 'w') as f:
                json.dump(settings, f)
        except Exception as e:
            print(f"Ошибка сохранения настроек: {e}")

    def load_all_playlists(self):
        """Загружает все плейлисты из папки playlists/"""
        self.playlists = {}
        self.playlist_names = []

        if not os.path.exists(PLAYLISTS_DIR):
            return

        for filename in sorted(os.listdir(PLAYLISTS_DIR)):
            if filename.endswith(".json"):
                name = filename[:-5]
                filepath = os.path.join(PLAYLISTS_DIR, filename)
                try:
                    with open(filepath, 'r') as f:
                        tracks = json.load(f)
                        self.playlists[name] = tracks
                        self.playlist_names.append(name)
                except Exception as e:
                    print(f"Ошибка загрузки плейлиста {name}: {e}")

        # Обновляем DropDown
        model = Gtk.StringList.new(self.playlist_names)
        self.playlist_dropdown.set_model(model)

    def on_playlist_changed(self, dropdown, pspec):
        """Переключение между сохранёнными плейлистами"""
        selected = dropdown.get_selected()
        if selected >= 0 and selected < len(self.playlist_names):
            name = self.playlist_names[selected]
            self.switch_playlist(name)

    def switch_playlist(self, name):
        """Загружает выбранный плейлист в интерфейс"""
        if name not in self.playlists:
            return

        # Останавливаем текущее воспроизведение
        self.player.set_state(Gst.State.NULL)
        self.current_index = -1
        self.title_label.set_label("Нет выбранного трека")
        self.show_cover_placeholder()

        # Очищаем список
        self.playlist.clear()
        while self.playlist_list.get_first_child():
            child = self.playlist_list.get_first_child()
            self.playlist_list.remove(child)

        # Заполняем новыми треками
        for path in self.playlists[name]:
            if os.path.isfile(path):
                self.playlist.append(path)
                label = Gtk.Label(
                    label=os.path.basename(path),
                    halign=Gtk.Align.START,
                    margin_top=5, margin_bottom=5, margin_start=5
                )
                row = Gtk.ListBoxRow()
                row.set_child(label)
                row.file_path = path
                self.playlist_list.append(row)

        self.active_playlist = name
        self.update_playlist_info()
        self.save_settings()

    def on_new_playlist(self, button):
        """Создание нового пустого плейлиста"""
        win = Gtk.Window(transient_for=self.window, modal=True)
        win.set_title("Новый плейлист")
        win.set_default_size(300, 100)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_margin_top(10)
        box.set_margin_bottom(10)
        box.set_margin_start(10)
        box.set_margin_end(10)

        entry = Gtk.Entry()
        entry.set_placeholder_text("Название плейлиста...")
        box.append(entry)

        btns = Gtk.Box(spacing=5)
        btn_ok = Gtk.Button(label="Создать")
        btn_cancel = Gtk.Button(label="Отмена")
        btns.append(btn_ok)
        btns.append(btn_cancel)
        box.append(btns)

        win.set_child(box)

        def create_pl(*_):
            name = entry.get_text().strip()
            if name and name not in self.playlists:
                self.playlists[name] = []
                self.playlist_names.append(name)
                # Обновляем модель DropDown
                model = Gtk.StringList.new(self.playlist_names)
                self.playlist_dropdown.set_model(model)
                # Выбираем новый плейлист
                self.playlist_dropdown.set_selected(len(self.playlist_names) - 1)
                self.switch_playlist(name)
            win.destroy()

        def cancel(*_):
            win.destroy()

        btn_ok.connect("clicked", create_pl)
        btn_cancel.connect("clicked", cancel)
        entry.connect("activate", create_pl)

        win.present()

    def on_save_current_playlist(self, button):
        """Сохраняет текущий плейлист в файл"""
        if not self.active_playlist:
            print("Сначала создайте или выберите плейлист")
            return

        filepath = os.path.join(PLAYLISTS_DIR, f"{self.active_playlist}.json")
        try:
            with open(filepath, 'w') as f:
                json.dump(self.playlist, f, ensure_ascii=False, indent=2)
            print(f"Плейлист '{self.active_playlist}' сохранён ({len(self.playlist)} треков)")
        except Exception as e:
            print(f"Ошибка сохранения: {e}")

    # ========== ГОРЯЧИЕ КЛАВИШИ ==========

    def setup_hotkeys(self):
        controller = Gtk.ShortcutController()
        controller.set_scope(Gtk.ShortcutScope.LOCAL)
        self.window.add_controller(controller)
        shortcuts = [
            ("space", lambda *_: self.toggle_play()),
            ("<Control>o", lambda *_: self.on_add_files(None)),
            ("<Control>m", lambda *_: self.on_open_m3u(None)),
            ("<Control>s", lambda *_: self.on_save_current_playlist(None)),
            ("Right", lambda *_: self.seek_forward()),
            ("Left", lambda *_: self.seek_backward()),
            ("Up", lambda *_: self.change_volume(0.05)),
            ("Down", lambda *_: self.change_volume(-0.05)),
            ("Delete", lambda *_: self.on_remove_track(None)),
            ("n", lambda *_: self.on_next(None)),
            ("p", lambda *_: self.on_prev(None)),
        ]
        for key, callback in shortcuts:
            shortcut = Gtk.Shortcut.new(
                trigger=Gtk.ShortcutTrigger.parse_string(key),
                action=Gtk.CallbackAction.new(callback)
            )
            controller.add_shortcut(shortcut)

    def toggle_play(self):
        state = self.player.get_state(0)[1]
        if state == Gst.State.PLAYING:
            self.player.set_state(Gst.State.PAUSED)
        else:
            if self.playlist and self.current_index == -1:
                self.play_index(0)
            else:
                self.player.set_state(Gst.State.PLAYING)

    def seek_forward(self):
        try:
            duration = self.player.query_duration(Gst.Format.TIME)[1]
            position = self.player.query_position(Gst.Format.TIME)[1]
            new_pos = min(position + 10 * Gst.SECOND, duration)
            self.player.seek_simple(Gst.Format.TIME, Gst.SeekFlags.FLUSH, new_pos)
        except Exception:
            pass

    def seek_backward(self):
        try:
            position = self.player.query_position(Gst.Format.TIME)[1]
            new_pos = max(position - 10 * Gst.SECOND, 0)
            self.player.seek_simple(Gst.Format.TIME, Gst.SeekFlags.FLUSH, new_pos)
        except Exception:
            pass

    def change_volume(self, delta):
        if self.volume_element:
            current = self.volume_element.get_property("volume")
            new_vol = max(0.0, min(2.0, current + delta))
            self.volume_element.set_property("volume", new_vol)
            self._volume_changing = True
            self.volume_scale.set_value(new_vol)
            self._volume_changing = False

    # ========== DRAG & DROP ==========

    def setup_drag_drop(self):
        drop_target = Gtk.DropTarget.new(Gdk.FileList, Gdk.DragAction.COPY)
        drop_target.connect("drop", self.on_file_drop)
        self.window.add_controller(drop_target)

    def on_file_drop(self, target, value, x, y):
        try:
            file_list = value
            added = 0
            for gfile in file_list:
                path = gfile.get_path()
                if path and os.path.isfile(path) and path not in self.playlist:
                    ext = os.path.splitext(path)[1].lower()
                    if ext in ['.mp3', '.flac', '.ogg', '.wav', '.m4a', '.opus']:
                        self.playlist.append(path)
                        label = Gtk.Label(
                            label=os.path.basename(path),
                            halign=Gtk.Align.START,
                            margin_top=5, margin_bottom=5, margin_start=5
                        )
                        row = Gtk.ListBoxRow()
                        row.set_child(label)
                        row.file_path = path
                        self.playlist_list.append(row)
                        added += 1
            if added > 0:
                self.update_playlist_info()
                if self.current_index == -1 and self.playlist:
                    first_new = len(self.playlist) - added
                    self.play_index(first_new)
        except Exception as e:
            print(f"Ошибка при перетаскивании: {e}")

    # ========== ОБЛОЖКИ ==========

    def find_cover_for_track(self, track_path):
        folder = os.path.dirname(track_path)
        if not folder:
            return None
        cover_names = ["cover.jpg", "cover.png", "folder.jpg", "folder.png",
                       "front.jpg", "front.png", "Cover.jpg", "Cover.png",
                       "Folder.jpg", "Folder.png", "Front.jpg", "Front.png",
                       "COVER.jpg", "COVER.png"]
        for name in cover_names:
            path = os.path.join(folder, name)
            if os.path.isfile(path):
                return path
        return None

    def show_cover_placeholder(self):
        pixbuf = GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB, True, 8, 200, 200)
        pixbuf.fill(0x808080FF)
        texture = Gdk.Texture.new_for_pixbuf(pixbuf)
        self.cover_image.set_paintable(texture)

    def update_cover(self, track_path):
        if not track_path:
            self.show_cover_placeholder()
            return
        cover_path = self.find_cover_for_track(track_path)
        if cover_path:
            try:
                pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(cover_path, 200, 200, True)
                texture = Gdk.Texture.new_for_pixbuf(pixbuf)
                self.cover_image.set_paintable(texture)
            except Exception as e:
                print(f"Не удалось загрузить обложку {cover_path}: {e}")
                self.show_cover_placeholder()
        else:
            self.show_cover_placeholder()

    # ========== ПЛЕЙЛИСТ И M3U ==========

    def on_add_files(self, button):
        dialog = Gtk.FileDialog()
        dialog.set_title("Добавить аудиофайлы")
        audio_filter = Gtk.FileFilter()
        audio_filter.set_name("Аудио файлы")
        audio_filter.add_mime_type("audio/*")
        dialog.set_default_filter(audio_filter)
        dialog.open_multiple(self.window, None, self.on_files_selected)

    def on_open_m3u(self, button):
        dialog = Gtk.FileDialog()
        dialog.set_title("Открыть плейлист M3U")
        m3u_filter = Gtk.FileFilter()
        m3u_filter.set_name("Плейлисты M3U (*.m3u, *.m3u8)")
        m3u_filter.add_pattern("*.m3u")
        m3u_filter.add_pattern("*.m3u8")
        dialog.set_default_filter(m3u_filter)
        dialog.open(self.window, None, self.on_m3u_selected)

    def on_m3u_selected(self, dialog, result):
        try:
            file = dialog.open_finish(result)
            if file:
                m3u_path = file.get_path()
                added_count = self.parse_m3u(m3u_path)
                if added_count > 0:
                    self.update_playlist_info()
                    if self.current_index == -1 and self.playlist:
                        first_new_index = len(self.playlist) - added_count
                        self.play_index(first_new_index)
                else:
                    print("В плейлисте не найдено доступных локальных треков.")
        except Exception as e:
            print(f"Ошибка при открытии плейлиста: {e}")

    def parse_m3u(self, m3u_path):
        m3u_dir = os.path.dirname(m3u_path)
        added_count = 0
        try:
            with open(m3u_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    track_path = line if os.path.isabs(line) else os.path.join(m3u_dir, line)
                    if os.path.isfile(track_path) and track_path not in self.playlist:
                        self.playlist.append(track_path)
                        label = Gtk.Label(label=os.path.basename(track_path),
                                          halign=Gtk.Align.START,
                                          margin_top=5, margin_bottom=5, margin_start=5)
                        row = Gtk.ListBoxRow()
                        row.set_child(label)
                        row.file_path = track_path
                        self.playlist_list.append(row)
                        added_count += 1
        except Exception as e:
            print(f"Ошибка чтения файла {m3u_path}: {e}")
        return added_count

    def on_files_selected(self, dialog, result):
        try:
            files = dialog.open_multiple_finish(result)
            if files:
                for file in files:
                    path = file.get_path()
                    if path and path not in self.playlist:
                        self.playlist.append(path)
                        label = Gtk.Label(label=os.path.basename(path),
                                          halign=Gtk.Align.START,
                                          margin_top=5, margin_bottom=5, margin_start=5)
                        row = Gtk.ListBoxRow()
                        row.set_child(label)
                        row.file_path = path
                        self.playlist_list.append(row)
                self.update_playlist_info()
                if self.current_index == -1 and self.playlist:
                    self.play_index(0)
        except Exception as e:
            print(f"Ошибка при выборе файлов: {e}")

    def on_remove_track(self, button):
        row = self.playlist_list.get_selected_row()
        if row is None:
            return
        index = row.get_index()
        if 0 <= index < len(self.playlist):
            if index == self.current_index:
                self.player.set_state(Gst.State.NULL)
                self.title_label.set_label("Нет выбранного трека")
                self.current_index = -1
                self.show_cover_placeholder()
            self.playlist.pop(index)
            self.playlist_list.remove(row)
            self.update_playlist_info()
            if index < self.current_index:
                self.current_index -= 1

    def on_track_activated(self, listbox, row):
        index = row.get_index()
        if 0 <= index < len(self.playlist):
            self.play_index(index)

    def play_index(self, index):
        if index < 0 or index >= len(self.playlist):
            return
        self.current_index = index
        path = self.playlist[index]
        if not os.path.exists(path):
            print(f"Файл не найден: {path}")
            return
        self.player.set_state(Gst.State.NULL)
        uri = GLib.filename_to_uri(path, None)
        self.player.set_property("uri", uri)
        self.player.set_state(Gst.State.PLAYING)
        self.title_label.set_label(os.path.basename(path))
        self.update_cover(path)
        self.highlight_current_track()

    def highlight_current_track(self):
        row = self.playlist_list.get_row_at_index(self.current_index)
        if row:
            self.playlist_list.select_row(row)

    def update_playlist_info(self):
        count = len(self.playlist)
        self.playlist_info.set_label(f"Треков: {count}")

    # ========== УПРАВЛЕНИЕ ВОСПРОИЗВЕДЕНИЕМ ==========

    def on_play(self, button):
        if self.playlist and self.current_index == -1:
            self.play_index(0)
        else:
            self.player.set_state(Gst.State.PLAYING)

    def on_pause(self, button):
        self.player.set_state(Gst.State.PAUSED)

    def on_stop(self, button):
        self.player.set_state(Gst.State.NULL)
        self.progress.set_value(0)
        self.time_label.set_label("0:00 / 0:00")

    def on_prev(self, button):
        if not self.playlist:
            return
        new_index = self.current_index - 1
        if new_index < 0:
            new_index = len(self.playlist) - 1
        self.play_index(new_index)

    def on_next(self, button):
        if not self.playlist:
            return
        new_index = self.current_index + 1
        if new_index >= len(self.playlist):
            new_index = 0
        self.play_index(new_index)

    def on_volume_changed(self, scale):
        if self._volume_changing:
            return
        if self.volume_element:
            self.volume_element.set_property("volume", scale.get_value())

    def update_progress(self):
        state = self.player.get_state(0)[1]
        if state == Gst.State.PLAYING:
            try:
                position = self.player.query_position(Gst.Format.TIME)[1]
                duration = self.player.query_duration(Gst.Format.TIME)[1]
                if duration > 0:
                    progress = (position / duration) * 100
                    self._updating = True
                    self.progress.set_value(progress)
                    self._updating = False
                    pos_sec = position // Gst.SECOND
                    dur_sec = duration // Gst.SECOND
                    self.time_label.set_label(
                        f"{self.format_time(pos_sec)} / {self.format_time(dur_sec)}"
                    )
            except Exception:
                pass
        return True

    def format_time(self, seconds):
        mins = seconds // 60
        secs = seconds % 60
        return f"{mins}:{secs:02d}"

    def on_progress_changed(self, scale):
        if self._updating:
            return
        try:
            duration = self.player.query_duration(Gst.Format.TIME)[1]
            if duration > 0:
                value = scale.get_value()
                new_pos = int((value / 100) * duration)
                self.player.seek_simple(Gst.Format.TIME, Gst.SeekFlags.FLUSH, new_pos)
        except Exception:
            pass

    def on_eos(self, bus, message):
        if self.playlist and self.current_index >= 0:
            next_index = self.current_index + 1
            if next_index < len(self.playlist):
                self.play_index(next_index)
            else:
                self.player.set_state(Gst.State.NULL)
                self.progress.set_value(0)
                self.title_label.set_label("Плейлист завершён")
                self.show_cover_placeholder()
        else:
            self.player.set_state(Gst.State.NULL)
            self.progress.set_value(0)

    def on_error(self, bus, message):
        err, debug = message.parse_error()
        print(f"Ошибка GStreamer: {err.message}")


if __name__ == "__main__":
    app = PlasticPlayer()
    app.run(None)