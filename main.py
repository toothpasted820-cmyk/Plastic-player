#!/usr/bin/env python3
"""Plastic Player — музыкальный плеер для Linux с плейлистом и обложками"""

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Gst', '1.0')
gi.require_version('GdkPixbuf', '2.0')

from gi.repository import Gtk, Gst, GLib, GdkPixbuf
import os

Gst.init(None)


class PlasticPlayer(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.plastic.player")
        self._updating = False
        self._volume_changing = False
        self.volume_element = None
        self.playlist = []
        self.current_index = -1
        self.cover_image = None

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
        self.window.present()

        GLib.timeout_add(500, self.update_progress)

    def build_ui(self):
        main_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        self.window.set_child(main_box)

        # === ЛЕВАЯ ПАНЕЛЬ: ПЛЕЙЛИСТ ===
        playlist_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        playlist_box.set_margin_top(10)
        playlist_box.set_margin_bottom(10)
        playlist_box.set_margin_start(10)
        playlist_box.set_margin_end(5)
        playlist_box.set_size_request(300, -1)

        playlist_header = Gtk.Label(label="📋 Плейлист")
        playlist_header.set_halign(Gtk.Align.START)
        playlist_box.append(playlist_header)

        self.playlist_list = Gtk.ListBox()
        self.playlist_list.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.playlist_list.connect("row-activated", self.on_track_activated)

        scroll = Gtk.ScrolledWindow()
        scroll.set_child(self.playlist_list)
        scroll.set_vexpand(True)
        playlist_box.append(scroll)

        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        btn_box.set_margin_top(5)

        add_btn = Gtk.Button(label="➕ Добавить")
        add_btn.connect("clicked", self.on_add_files)
        btn_box.append(add_btn)

        remove_btn = Gtk.Button(label="🗑 Удалить")
        remove_btn.connect("clicked", self.on_remove_track)
        btn_box.append(remove_btn)

        playlist_box.append(btn_box)
        main_box.append(playlist_box)

        # === ПРАВАЯ ПАНЕЛЬ: УПРАВЛЕНИЕ ===
        control_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        control_box.set_margin_top(20)
        control_box.set_margin_bottom(20)
        control_box.set_margin_start(20)
        control_box.set_margin_end(20)
        control_box.set_hexpand(True)
        main_box.append(control_box)

        # Обложка альбома
        self.cover_image = Gtk.Image()
        self.cover_image.set_size_request(200, 200)
        self.cover_image.set_halign(Gtk.Align.CENTER)
        self.cover_image.set_valign(Gtk.Align.CENTER)
        self.show_cover_placeholder()
        control_box.append(self.cover_image)

        self.title_label = Gtk.Label(label="Нет выбранного трека")
        self.title_label.set_halign(Gtk.Align.CENTER)
        control_box.append(self.title_label)

        self.progress = Gtk.Scale.new_with_range(
            Gtk.Orientation.HORIZONTAL, 0, 100, 1
        )
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

        self.volume_scale = Gtk.Scale.new_with_range(
            Gtk.Orientation.HORIZONTAL, 0.0, 2.0, 0.05
        )
        self.volume_scale.set_value(1.0)
        self.volume_scale.set_hexpand(False)
        self.volume_scale.set_size_request(150, -1)
        self.volume_scale.connect("value-changed", self.on_volume_changed)
        vol_box.append(self.volume_scale)

        control_box.append(vol_box)

        self.playlist_info = Gtk.Label(label="Треков: 0")
        self.playlist_info.set_halign(Gtk.Align.CENTER)
        control_box.append(self.playlist_info)

    # ========== РАБОТА С ОБЛОЖКАМИ ==========

    def find_cover_for_track(self, track_path):
        """Ищет файл обложки в папке трека"""
        folder = os.path.dirname(track_path)
        if not folder:
            return None

        cover_names = [
            "cover.jpg", "cover.png",
            "folder.jpg", "folder.png",
            "front.jpg", "front.png",
            "Cover.jpg", "Cover.png",
            "Folder.jpg", "Folder.png",
            "Front.jpg", "Front.png",
            "COVER.jpg", "COVER.png",
        ]

        for name in cover_names:
            path = os.path.join(folder, name)
            if os.path.isfile(path):
                return path

        return None

    def show_cover_placeholder(self):
        """Показывает серый квадрат-заглушку"""
        # Позиционные аргументы: colorspace, has_alpha, bits_per_sample, width, height
        pixbuf = GdkPixbuf.Pixbuf.new(
            GdkPixbuf.Colorspace.RGB,
            True,
            8,
            200,
            200
        )
        pixbuf.fill(0x808080FF)
        self.cover_image.set_from_pixbuf(pixbuf)

    def update_cover(self, track_path):
        """Обновляет обложку для текущего трека"""
        if not track_path:
            self.show_cover_placeholder()
            return

        cover_path = self.find_cover_for_track(track_path)

        if cover_path:
            try:
                # Позиционные аргументы: filename, width, height, preserve_aspect_ratio
                pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
                    cover_path,
                    200,
                    200,
                    True
                )
                self.cover_image.set_from_pixbuf(pixbuf)
            except Exception as e:
                print(f"Не удалось загрузить обложку {cover_path}: {e}")
                self.show_cover_placeholder()
        else:
            self.show_cover_placeholder()

    # ========== ПЛЕЙЛИСТ ==========

    def on_add_files(self, button):
        dialog = Gtk.FileDialog()
        dialog.set_title("Добавить аудиофайлы")

        audio_filter = Gtk.FileFilter()
        audio_filter.set_name("Аудио файлы")
        audio_filter.add_mime_type("audio/*")
        dialog.set_default_filter(audio_filter)

        dialog.open_multiple(self.window, None, self.on_files_selected)

    def on_files_selected(self, dialog, result):
        try:
            files = dialog.open_multiple_finish(result)
            if files:
                for file in files:
                    path = file.get_path()
                    if path and path not in self.playlist:
                        self.playlist.append(path)
                        label = Gtk.Label(
                            label=os.path.basename(path),
                            halign=Gtk.Align.START,
                            margin_top=5,
                            margin_bottom=5,
                            margin_start=5
                        )
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
        """Запуск трека по индексу"""
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

    # ========== УПРАВЛЕНИЕ ==========

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
                self.player.seek_simple(
                    Gst.Format.TIME, Gst.SeekFlags.FLUSH, new_pos
                )
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