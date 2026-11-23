#!/usr/bin/env python3
"""Plastic Player — простой музыкальный плеер для Linux"""

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Gst', '1.0')

from gi.repository import Gtk, Gst, GLib
import os

Gst.init(None)


class PlasticPlayer(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.plastic.player")
        self._updating = False       # защита от рекурсии прогресса
        self._volume_changing = False # защита от рекурсии громкости
        self.volume_element = None

    def do_activate(self):
        self.window = Gtk.ApplicationWindow(application=self)
        self.window.set_title("Plastic Player")
        self.window.set_default_size(500, 300)

        self.player = Gst.ElementFactory.make("playbin", "player")

        # Встраиваем элемент громкости прямо в аудио-цепочку
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
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        main_box.set_margin_top(20)
        main_box.set_margin_bottom(20)
        main_box.set_margin_start(20)
        main_box.set_margin_end(20)
        self.window.set_child(main_box)

        self.title_label = Gtk.Label(label="Нет выбранного трека")
        main_box.append(self.title_label)

        self.progress = Gtk.Scale.new_with_range(
            Gtk.Orientation.HORIZONTAL, 0, 100, 1
        )
        self.progress.set_value(0)
        self.progress.connect("value-changed", self.on_progress_changed)
        main_box.append(self.progress)

        self.time_label = Gtk.Label(label="0:00 / 0:00")
        main_box.append(self.time_label)

        controls = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        controls.set_halign(Gtk.Align.CENTER)

        self.play_btn = Gtk.Button(label="▶ Играть")
        self.play_btn.connect("clicked", self.on_play)
        controls.append(self.play_btn)

        self.pause_btn = Gtk.Button(label="⏸ Пауза")
        self.pause_btn.connect("clicked", self.on_pause)
        controls.append(self.pause_btn)

        self.stop_btn = Gtk.Button(label="⏹ Стоп")
        self.stop_btn.connect("clicked", self.on_stop)
        controls.append(self.stop_btn)

        open_btn = Gtk.Button(label="📁 Открыть файл")
        open_btn.connect("clicked", self.on_open_file)
        controls.append(open_btn)

        main_box.append(controls)

        vol_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        vol_box.append(Gtk.Label(label="Громкость:"))

        self.volume_scale = Gtk.Scale.new_with_range(
            Gtk.Orientation.HORIZONTAL, 0.0, 2.0, 0.05
        )
        self.volume_scale.set_value(1.0)
        self.volume_scale.set_hexpand(True)
        self.volume_scale.connect("value-changed", self.on_volume_changed)
        vol_box.append(self.volume_scale)

        main_box.append(vol_box)

    def on_open_file(self, button):
        dialog = Gtk.FileDialog()
        dialog.set_title("Выберите аудиофайл")

        audio_filter = Gtk.FileFilter()
        audio_filter.set_name("Аудио файлы")
        audio_filter.add_mime_type("audio/*")
        dialog.set_default_filter(audio_filter)

        dialog.open(self.window, None, self.on_file_selected)

    def on_file_selected(self, dialog, result):
        try:
            file = dialog.open_finish(result)
            if file:
                self.play_file(file.get_path())
        except Exception as e:
            print(f"Ошибка: {e}")

    def play_file(self, path):
        self.player.set_state(Gst.State.NULL)
        self.player.set_property("uri", f"file://{path}")
        self.player.set_state(Gst.State.PLAYING)
        self.title_label.set_label(os.path.basename(path))

    def on_play(self, button):
        self.player.set_state(Gst.State.PLAYING)

    def on_pause(self, button):
        self.player.set_state(Gst.State.PAUSED)

    def on_stop(self, button):
        self.player.set_state(Gst.State.NULL)
        self.progress.set_value(0)
        self.time_label.set_label("0:00 / 0:00")

    # === ИСПРАВЛЕНО: value теперь берём через get_value() ===
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
                    # Ставим флаг, чтобы программное движение ползунка
                    # НЕ вызвало перемотку в on_progress_changed
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

    # === ИСПРАВЛЕНО: value теперь берём через get_value() ===
    def on_progress_changed(self, scale):
        if self._updating:
            return  # это программное обновление от таймера — игнорируем
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
        self.player.set_state(Gst.State.NULL)
        self.progress.set_value(0)

    def on_error(self, bus, message):
        err, debug = message.parse_error()
        print(f"Ошибка GStreamer: {err.message}")


if __name__ == "__main__":
    app = PlasticPlayer()
    app.run(None)