#!/usr/bin/env python3
"""Plastic Player — музыкальный плеер с кастомными темами, GIF и настройками"""

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Gst', '1.0')
gi.require_version('GdkPixbuf', '2.0')

from gi.repository import Gtk, Gst, GLib, GdkPixbuf, Gdk
import os
import json
from datetime import datetime

Gst.init(None)

CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".config", "plastic-player")
PLAYLISTS_DIR = os.path.join(CONFIG_DIR, "playlists")
LIBRARY_FILE = os.path.join(CONFIG_DIR, "library.json")
PROFILE_FILE = os.path.join(CONFIG_DIR, "profile.json")
SETTINGS_FILE = os.path.join(CONFIG_DIR, "settings.json")


def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) / 255.0 for i in (0, 2, 4))

def rgb_to_hex(r, g, b):
    return '#{:02x}{:02x}{:02x}'.format(int(r*255), int(g*255), int(b*255))

def generate_theme_css(base_color, theme_type="dark"):
    r, g, b = hex_to_rgb(base_color)
    dark_r, dark_g, dark_b = max(0, r-0.3), max(0, g-0.3), max(0, b-0.3)
    light_r, light_g, light_b = min(1, r+0.2), min(1, g+0.2), min(1, b+0.2)
    highlight_r, highlight_g, highlight_b = min(1, r+0.4), min(1, g+0.4), min(1, b+0.4)
    
    base_hex = base_color
    dark_hex = rgb_to_hex(dark_r, dark_g, dark_b)
    light_hex = rgb_to_hex(light_r, light_g, light_b)
    highlight_hex = rgb_to_hex(highlight_r, highlight_g, highlight_b)
    
    if theme_type == "neon":
        text = light_hex
        glow = f"0 0 8px {base_hex}40"
        btn_bg = f"{base_hex}10"
        btn_hover = f"{base_hex}25"
        selected_bg = f"{base_hex}20"
        
        css = f"""
        window, notebook, notebook > header, notebook > stack, scrolledwindow, viewport, frame, box, listbox, separator, popover {{
            background-color: transparent;
        }}

        window {{ background-color: transparent; color: {text}; }}
        
        notebook > header > tabs > tab {{ 
            background-color: rgba(18, 18, 20, 0.8); 
            color: {text}; border: none; border-radius: 8px 8px 0 0; margin: 0 2px; padding: 8px 16px; 
        }}
        notebook > header > tabs > tab:checked {{ 
            background-color: {base_hex}30; color: {highlight_hex}; border-bottom: 2px solid {base_hex}; 
        }}
        notebook > header > tabs > tab:hover {{ background-color: {base_hex}15; }}
        
        .glass-panel {{ 
            background-color: rgba(18, 18, 20, 0.85); 
            border-radius: 16px; padding: 10px; border: 1px solid rgba(255,255,255,0.08);
        }}
        button {{ 
            background-color: {btn_bg}; border: 1px solid {base_hex}50; border-radius: 6px; 
            color: {text}; transition: all 0.3s ease; 
        }}
        button:hover {{ background-color: {btn_hover}; border-color: {base_hex}; box-shadow: {glow}; }}
        button:active {{ background-color: {base_hex}40; }}
        scale trough {{ background-color: rgba(255,255,255,0.1); border-radius: 4px; min-height: 6px; }}
        scale highlight {{ background-color: {highlight_hex}; border-radius: 4px; box-shadow: 0 0 6px {base_hex}50; }}
        listbox row {{ padding: 8px; border-radius: 6px; margin-bottom: 2px; transition: background-color 0.2s; }}
        listbox row:selected {{ background-color: {selected_bg}; color: {text}; border-left: 3px solid {base_hex}; }}
        label {{ text-shadow: none; color: {text}; }}
        entry {{ background-color: rgba(255,255,255,0.05); border: 1px solid {base_hex}30; border-radius: 6px; color: {text}; }}
        """
    
    elif theme_type == "retro":
        text = "#f4ecd8"
        css = f"""
        window, notebook, notebook > header, notebook > stack, scrolledwindow, viewport, frame, box, listbox, separator, popover {{
            background-color: transparent;
        }}

        window {{ background-color: transparent; color: #5d4037; font-family: 'Courier New', monospace; }}
        
        notebook > header > tabs > tab {{ 
            background-color: rgba(244, 236, 216, 0.9); 
            color: #5d4037; border: 2px solid #5d4037; border-radius: 0; margin: 0 2px; padding: 8px 16px; 
            font-family: 'Courier New', monospace;
        }}
        notebook > header > tabs > tab:checked {{ background-color: #5d4037; color: #f4ecd8; }}
        notebook > header > tabs > tab:hover {{ background-color: rgba(93, 64, 55, 0.3); }}
        
        .glass-panel {{ background-color: rgba(244, 236, 216, 0.95); border-radius: 0; border: 2px solid #5d4037; }}
        button {{ background-color: rgba(93, 64, 55, 0.2); border: 2px solid #5d4037; border-radius: 0; font-family: 'Courier New', monospace; color: #5d4037; }}
        button:hover {{ background-color: rgba(93, 64, 55, 0.4); }}
        scale trough {{ background-color: rgba(93, 64, 55, 0.3); border: 1px solid #5d4037; }}
        scale highlight {{ background-color: {base_hex}; }}
        listbox row:selected {{ background-color: #5d4037; color: #f4ecd8; }}
        label {{ color: #5d4037; }}
        entry {{ background-color: rgba(93, 64, 55, 0.1); border: 2px solid #5d4037; border-radius: 0; color: #5d4037; font-family: 'Courier New', monospace; }}
        """
    
    else:  # dark
        text = "#cdd6f4"
        css = f"""
        window, notebook, notebook > header, notebook > stack, scrolledwindow, viewport, frame, box, listbox, separator, popover {{
            background-color: transparent;
        }}

        window {{ background-color: transparent; color: {text}; }}
        
        notebook > header > tabs > tab {{ 
            background-color: rgba(30, 30, 46, 0.9); 
            color: {text}; border: none; border-radius: 8px 8px 0 0; margin: 0 2px; padding: 8px 16px; 
        }}
        notebook > header > tabs > tab:checked {{ 
            background-color: {base_hex}30; color: {highlight_hex}; border-bottom: 2px solid {base_hex}; 
        }}
        notebook > header > tabs > tab:hover {{ background-color: {base_hex}15; }}
        
        .glass-panel {{ 
            background-color: rgba(30, 30, 46, 0.95); 
            border-radius: 16px; padding: 10px; border: 1px solid rgba(255,255,255,0.08);
        }}
        button {{ 
            background-color: {dark_hex}30; border: none; border-radius: 8px; 
            padding: 8px 16px; font-weight: bold; transition: all 0.2s ease; color: {text};
        }}
        button:hover {{ background-color: {light_hex}30; transform: scale(1.05); }}
        button:active {{ background-color: {base_hex}40; }}
        scale trough {{ background-color: rgba(255,255,255,0.1); border-radius: 4px; min-height: 6px; }}
        scale highlight {{ background-color: {highlight_hex}; border-radius: 4px; }}
        listbox row {{ padding: 8px; border-radius: 6px; transition: background-color 0.2s; }}
        listbox row:selected {{ background-color: {base_hex}40; color: {text}; }}
        label.title {{ font-size: 18px; font-weight: bold; color: {highlight_hex}; }}
        label {{ color: {text}; }}
        entry {{ background-color: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); border-radius: 6px; color: {text}; }}
        """
    
    return css


class PlasticPlayer(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.plastic.player")
        self._updating = False
        self._volume_changing = False
        self.volume_element = None
        self.playlist = []
        self.current_index = -1
        
        self.css_provider = Gtk.CssProvider()
        self.current_theme = "dark"
        self.accent_color = "#89b4fa"
        self.bg_image = None
        
        # Библиотека и профиль
        self.library = {}
        self.profile = {
            "username": "User",
            "total_plays": 0,
            "listening_time": 0,
            "created_at": datetime.now().isoformat()
        }
        
        # Для анимации GIF фона
        self.gif_animation_source = None
        self.current_gif_pixbuf = None
        
        # Для анимации обложки плейлиста
        self.cover_gif_source = None
        self.current_cover_gif = None
        
        os.makedirs(PLAYLISTS_DIR, exist_ok=True)
        self.load_settings()
        self.load_library()
        self.load_profile()

    def do_activate(self):
        self.window = Gtk.ApplicationWindow(application=self)
        self.window.set_title("Plastic Player")
        self.window.set_default_size(1000, 700)
        self.window.set_resizable(True)

        # Аудио плейер
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
        self.load_all_playlists()
        
        self.apply_dynamic_theme()
        self.apply_background()  # Применяем фон при запуске

        if hasattr(self, 'active_playlist') and self.active_playlist and self.active_playlist in self.playlists:
            self.switch_playlist(self.active_playlist)

        self.window.present()
        GLib.timeout_add(500, self.update_progress)

    def build_ui(self):
        # Создаем контейнер для фона (лежит под всем интерфейсом)
        self.bg_picture = Gtk.Picture()
        self.bg_picture.set_content_fit(Gtk.ContentFit.COVER)
        self.bg_picture.set_hexpand(True)
        self.bg_picture.set_vexpand(True)
        
        # Главный контейнер с вкладками
        notebook = Gtk.Notebook()
        notebook.set_vexpand(True)
        notebook.set_hexpand(True)
        
        # === Вкладка 1: Плеер ===
        player_page = self.build_player_page()
        notebook.append_page(player_page, Gtk.Label(label="🎵 Плеер"))
        
        # === Вкладка 2: Библиотека ===
        library_page = self.build_library_page()
        notebook.append_page(library_page, Gtk.Label(label="📚 Библиотека"))
        
        # === Вкладка 3: Профиль ===
        profile_page = self.build_profile_page()
        notebook.append_page(profile_page, Gtk.Label(label="👤 Профиль"))
        
        # === Вкладка 4: Настройки ===
        settings_page = self.build_settings_page()
        notebook.append_page(settings_page, Gtk.Label(label="⚙️ Настройки"))
        
        # Накладываем интерфейс поверх фона через Overlay
        overlay = Gtk.Overlay()
        overlay.set_child(self.bg_picture)
        overlay.add_overlay(notebook)
        
        self.window.set_child(overlay)

    def build_player_page(self):
        """Создаёт страницу плеера с адаптивной версткой"""
        main_scroll = Gtk.ScrolledWindow()
        main_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        
        main_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=20)
        main_box.set_margin_top(20)
        main_box.set_margin_bottom(20)
        main_box.set_margin_start(20)
        main_box.set_margin_end(20)
        main_box.set_vexpand(True)
        main_box.set_hexpand(True)

        # === ЛЕВАЯ ПАНЕЛЬ ===
        playlist_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        playlist_box.set_size_request(280, -1)
        playlist_box.add_css_class("glass-panel")

        # Переключатель плейлистов
        self.playlist_names = []
        pl_string_list = Gtk.StringList.new([])
        self.playlist_dropdown = Gtk.DropDown.new(pl_string_list, None)
        self.playlist_dropdown.connect("notify::selected-item", self.on_playlist_changed)
        playlist_box.append(self.playlist_dropdown)

        btn_new_pl = Gtk.Button(label="➕ Новый плейлист")
        btn_new_pl.connect("clicked", self.on_new_playlist)
        playlist_box.append(btn_new_pl)

        # Кнопка установки обложки плейлиста
        pl_cover_btn = Gtk.Button(label="🖼️ Обложка плейлиста")
        pl_cover_btn.connect("clicked", self.on_set_playlist_cover)
        playlist_box.append(pl_cover_btn)

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
        control_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        control_box.set_hexpand(True)
        control_box.set_vexpand(True)
        control_box.add_css_class("glass-panel")

        # ОБЛОЖКА ТРЕКА / ПЛЕЙЛИСТА
        self.cover_image = Gtk.Picture()
        self.cover_image.set_size_request(200, 200)
        self.cover_image.set_halign(Gtk.Align.CENTER)
        self.cover_image.set_valign(Gtk.Align.CENTER)
        self.cover_image.set_content_fit(Gtk.ContentFit.COVER)
        self.show_cover_placeholder()
        control_box.append(self.cover_image)

        self.title_label = Gtk.Label(label="Нет выбранного трека")
        self.title_label.set_halign(Gtk.Align.CENTER)
        self.title_label.set_wrap(True)
        control_box.append(self.title_label)

        self.progress = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 100, 1)
        self.progress.set_value(0)
        self.progress.set_hexpand(True)
        self.progress.connect("value-changed", self.on_progress_changed)
        control_box.append(self.progress)

        self.time_label = Gtk.Label(label="0:00 / 0:00")
        self.time_label.set_halign(Gtk.Align.CENTER)
        control_box.append(self.time_label)

        controls = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        controls.set_halign(Gtk.Align.CENTER)
        controls.set_margin_top(5)
        self.prev_btn = Gtk.Button(label="⏮")
        self.prev_btn.connect("clicked", self.on_prev)
        controls.append(self.prev_btn)
        self.play_btn = Gtk.Button(label="▶")
        self.play_btn.connect("clicked", self.on_play)
        controls.append(self.play_btn)
        self.pause_btn = Gtk.Button(label="⏸")
        self.pause_btn.connect("clicked", self.on_pause)
        controls.append(self.pause_btn)
        self.stop_btn = Gtk.Button(label="⏹")
        self.stop_btn.connect("clicked", self.on_stop)
        controls.append(self.stop_btn)
        self.next_btn = Gtk.Button(label="⏭")
        self.next_btn.connect("clicked", self.on_next)
        controls.append(self.next_btn)
        control_box.append(controls)

        vol_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        vol_box.set_halign(Gtk.Align.CENTER)
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

        main_box.append(control_box)
        main_scroll.set_child(main_box)
        return main_scroll

    def build_library_page(self):
        """Создаёт страницу библиотеки"""
        lib_scroll = Gtk.ScrolledWindow()
        lib_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        
        lib_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        lib_box.set_margin_top(20)
        lib_box.set_margin_bottom(20)
        lib_box.set_margin_start(20)
        lib_box.set_margin_end(20)
        lib_box.add_css_class("glass-panel")
        
        header = Gtk.Label(label="📚 Моя библиотека")
        header.add_css_class("title")
        header.set_halign(Gtk.Align.START)
        lib_box.append(header)
        
        search_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        self.lib_search = Gtk.Entry()
        self.lib_search.set_placeholder_text("Поиск треков...")
        self.lib_search.set_hexpand(True)
        self.lib_search.connect("changed", self.on_library_search)
        search_box.append(self.lib_search)
        
        add_to_lib_btn = Gtk.Button(label="➕ Добавить файлы")
        add_to_lib_btn.connect("clicked", self.on_add_to_library)
        search_box.append(add_to_lib_btn)
        lib_box.append(search_box)
        
        self.library_list = Gtk.ListBox()
        self.library_list.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.library_list.connect("row-activated", self.on_library_track_activated)
        
        lib_inner_scroll = Gtk.ScrolledWindow()
        lib_inner_scroll.set_child(self.library_list)
        lib_inner_scroll.set_vexpand(True)
        lib_box.append(lib_inner_scroll)
        
        self.library_info = Gtk.Label(label="Треков в библиотеке: 0")
        self.library_info.set_halign(Gtk.Align.CENTER)
        lib_box.append(self.library_info)
        
        self.refresh_library_view()
        lib_scroll.set_child(lib_box)
        return lib_scroll
    
    def build_profile_page(self):
        """Создаёт страницу профиля"""
        profile_scroll = Gtk.ScrolledWindow()
        profile_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        
        profile_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        profile_box.set_margin_top(20)
        profile_box.set_margin_bottom(20)
        profile_box.set_margin_start(20)
        profile_box.set_margin_end(20)
        profile_box.add_css_class("glass-panel")
        
        header = Gtk.Label(label="👤 Мой профиль")
        header.add_css_class("title")
        header.set_halign(Gtk.Align.START)
        profile_box.append(header)
        
        name_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        name_box.append(Gtk.Label(label="Имя:"))
        self.username_entry = Gtk.Entry()
        self.username_entry.set_text(self.profile.get("username", "User"))
        self.username_entry.set_hexpand(True)
        self.username_entry.connect("changed", self.on_username_changed)
        name_box.append(self.username_entry)
        profile_box.append(name_box)
        
        stats_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        
        total_plays = self.profile.get("total_plays", 0)
        listening_time = self.profile.get("listening_time", 0)
        hours = listening_time // 3600
        minutes = (listening_time % 3600) // 60
        
        stats = [
            f"🎵 Всего прослушиваний: {total_plays}",
            f"⏱️ Время прослушивания: {hours}ч {minutes}мин",
            f"📅 Дата регистрации: {self.profile.get('created_at', 'N/A')[:10]}",
            f"🎶 Треков в библиотеке: {len(self.library)}"
        ]
        
        for stat in stats:
            label = Gtk.Label(label=stat)
            label.set_halign(Gtk.Align.START)
            stats_box.append(label)
        
        profile_box.append(stats_box)
        
        reset_btn = Gtk.Button(label="🔄 Сбросить статистику")
        reset_btn.connect("clicked", self.on_reset_stats)
        profile_box.append(reset_btn)
        
        profile_scroll.set_child(profile_box)
        return profile_scroll

    def build_settings_page(self):
        """Создаёт страницу настроек"""
        settings_scroll = Gtk.ScrolledWindow()
        settings_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        
        settings_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        settings_box.set_margin_top(20)
        settings_box.set_margin_bottom(20)
        settings_box.set_margin_start(20)
        settings_box.set_margin_end(20)
        settings_box.add_css_class("glass-panel")
        
        header = Gtk.Label(label="⚙️ Настройки интерфейса")
        header.add_css_class("title")
        header.set_halign(Gtk.Align.START)
        settings_box.append(header)
        
        # Выбор акцентного цвета
        accent_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        accent_box.append(Gtk.Label(label="✨ Акцентный цвет:"))
        self.accent_btn = Gtk.Button()
        self.update_accent_button_color()
        self.accent_btn.connect("clicked", self.on_choose_accent_color)
        accent_box.append(self.accent_btn)
        settings_box.append(accent_box)
        
        # Переключатель тем
        theme_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        theme_box.append(Gtk.Label(label="🎨 Тема оформления:"))
        themes_list = ["dark", "neon", "retro"]
        string_list = Gtk.StringList.new(themes_list)
        self.theme_dropdown = Gtk.DropDown.new(string_list, None)
        idx = themes_list.index(self.current_theme) if self.current_theme in themes_list else 0
        self.theme_dropdown.set_selected(idx)
        self.theme_dropdown.connect("notify::selected-item", self.on_theme_dropdown_changed)
        theme_box.append(self.theme_dropdown)
        settings_box.append(theme_box)
        
        # Кнопка выбора фона
        bg_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        bg_box.append(Gtk.Label(label="🖼️ Фоновое изображение (GIF/IMG):"))
        bg_btn = Gtk.Button(label="Выбрать файл")
        bg_btn.connect("clicked", self.on_choose_bg)
        bg_box.append(bg_btn)
        settings_box.append(bg_box)
        
        # Информация о текущем фоне
        self.bg_info_label = Gtk.Label(label="Фон не установлен")
        self.bg_info_label.set_halign(Gtk.Align.START)
        settings_box.append(self.bg_info_label)
        
        # Кнопка сброса фона
        reset_bg_btn = Gtk.Button(label="🗑️ Убрать фон")
        reset_bg_btn.connect("clicked", self.on_reset_bg)
        settings_box.append(reset_bg_btn)
        
        settings_scroll.set_child(settings_box)
        return settings_scroll

    # ========== БИБЛИОТЕКА ==========
    
    def load_library(self):
        try:
            if os.path.exists(LIBRARY_FILE):
                with open(LIBRARY_FILE, 'r') as f:
                    self.library = json.load(f)
        except Exception as e:
            print(f"Ошибка загрузки библиотеки: {e}")
            self.library = {}
    
    def save_library(self):
        try:
            with open(LIBRARY_FILE, 'w') as f:
                json.dump(self.library, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Ошибка сохранения библиотеки: {e}")
    
    def add_to_library(self, track_path):
        if track_path not in self.library:
            self.library[track_path] = {
                "plays": 0,
                "last_played": None,
                "added_at": datetime.now().isoformat()
            }
            self.save_library()
            self.refresh_library_view()
    
    def refresh_library_view(self):
        while self.library_list.get_first_child():
            child = self.library_list.get_first_child()
            self.library_list.remove(child)
        
        for path, info in sorted(self.library.items()):
            if os.path.isfile(path):
                filename = os.path.basename(path)
                plays = info.get("plays", 0)
                label_text = f"{filename} ({plays} просл.)"
                
                label = Gtk.Label(
                    label=label_text,
                    halign=Gtk.Align.START,
                    margin_top=5, margin_bottom=5, margin_start=5
                )
                row = Gtk.ListBoxRow()
                row.set_child(label)
                row.file_path = path
                self.library_list.append(row)
        
        self.library_info.set_label(f"Треков в библиотеке: {len(self.library)}")
    
    def on_library_search(self, entry):
        query = entry.get_text().lower()
        
        while self.library_list.get_first_child():
            child = self.library_list.get_first_child()
            self.library_list.remove(child)
        
        for path, info in self.library.items():
            if os.path.isfile(path):
                filename = os.path.basename(path).lower()
                if query in filename:
                    plays = info.get("plays", 0)
                    label_text = f"{os.path.basename(path)} ({plays} просл.)"
                    
                    label = Gtk.Label(
                        label=label_text,
                        halign=Gtk.Align.START,
                        margin_top=5, margin_bottom=5, margin_start=5
                    )
                    row = Gtk.ListBoxRow()
                    row.set_child(label)
                    row.file_path = path
                    self.library_list.append(row)
    
    def on_library_track_activated(self, listbox, row):
        path = row.file_path
        if os.path.isfile(path):
            if path not in self.playlist:
                self.playlist.append(path)
                label = Gtk.Label(
                    label=os.path.basename(path),
                    halign=Gtk.Align.START,
                    margin_top=5, margin_bottom=5, margin_start=5
                )
                new_row = Gtk.ListBoxRow()
                new_row.set_child(label)
                new_row.file_path = path
                self.playlist_list.append(new_row)
                self.update_playlist_info()
            
            index = self.playlist.index(path)
            self.play_index(index)
    
    def on_add_to_library(self, button):
        dialog = Gtk.FileDialog()
        dialog.set_title("Добавить в библиотеку")
        audio_filter = Gtk.FileFilter()
        audio_filter.set_name("Аудио файлы")
        audio_filter.add_mime_type("audio/*")
        dialog.set_default_filter(audio_filter)
        dialog.open_multiple(self.window, None, self.on_library_files_selected)
    
    def on_library_files_selected(self, dialog, result):
        try:
            files = dialog.open_multiple_finish(result)
            if files:
                added = 0
                for file in files:
                    path = file.get_path()
                    if path and os.path.isfile(path):
                        self.add_to_library(path)
                        added += 1
                print(f"✅ Добавлено {added} треков в библиотеку")
        except Exception as e:
            print(f"Ошибка при добавлении файлов: {e}")

    # ========== ПРОФИЛЬ ==========
    
    def load_profile(self):
        try:
            if os.path.exists(PROFILE_FILE):
                with open(PROFILE_FILE, 'r') as f:
                    self.profile = json.load(f)
        except Exception as e:
            print(f"Ошибка загрузки профиля: {e}")
    
    def save_profile(self):
        try:
            with open(PROFILE_FILE, 'w') as f:
                json.dump(self.profile, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Ошибка сохранения профиля: {e}")
    
    def update_play_stats(self, track_path):
        if track_path in self.library:
            self.library[track_path]["plays"] = self.library[track_path].get("plays", 0) + 1
            self.library[track_path]["last_played"] = datetime.now().isoformat()
            self.save_library()
        
        self.profile["total_plays"] = self.profile.get("total_plays", 0) + 1
        self.save_profile()
        
        if hasattr(self, 'library_list'):
            self.refresh_library_view()
    
    def on_username_changed(self, entry):
        self.profile["username"] = entry.get_text()
        self.save_profile()
    
    def on_reset_stats(self, button):
        self.profile["total_plays"] = 0
        self.profile["listening_time"] = 0
        self.save_profile()
        
        for path in self.library:
            self.library[path]["plays"] = 0
            self.library[path]["last_played"] = None
        self.save_library()
        
        self.refresh_library_view()
        print("✅ Статистика сброшена")

    # ========== НАСТРОЙКИ И ТЕМЫ ==========

    def on_choose_bg(self, button):
        dialog = Gtk.FileDialog()
        dialog.set_title("Выберите фоновое изображение или GIF")
        img_filter = Gtk.FileFilter()
        img_filter.set_name("Изображения и GIF")
        img_filter.add_mime_type("image/*")
        img_filter.add_pattern("*.gif")
        img_filter.add_pattern("*.webp")
        img_filter.add_pattern("*.apng")
        dialog.set_default_filter(img_filter)
        dialog.open(self.window, None, self.on_bg_selected)

    def on_bg_selected(self, dialog, result):
        try:
            file = dialog.open_finish(result)
            if file:
                self.bg_image = file.get_path()
                self.apply_background()
                self.apply_dynamic_theme()
                self.save_settings()
                self.bg_info_label.set_label(f"Текущий фон: {os.path.basename(self.bg_image)}")
                print(f"✅ Фон установлен: {os.path.basename(self.bg_image)}")
        except GLib.Error as e:
            if "Dismissed by user" not in str(e):
                print(f"Ошибка выбора фона: {e}")
        except Exception as e:
            print(f"Ошибка выбора фона: {e}")

    def on_reset_bg(self, button):
        self.bg_image = None
        self.apply_background()
        self.apply_dynamic_theme()
        self.save_settings()
        print("✅ Фон сброшен")

    def get_theme_bg_color(self):
        colors = {"dark": "#1e1e2e", "neon": "#121214", "retro": "#f4ecd8"}
        return colors.get(self.current_theme, "#1e1e2e")

    def set_solid_background(self):
        """Сплошная заливка цветом темы (когда фоновая картинка не задана)"""
        color_hex = self.get_theme_bg_color().lstrip('#')
        pixel = (int(color_hex, 16) << 8) | 0xFF
        pixbuf = GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB, True, 8, 8, 8)
        pixbuf.fill(pixel)
        self.bg_picture.set_paintable(Gdk.Texture.new_for_pixbuf(pixbuf))

    def apply_background(self):
        """Применяет фоновое изображение/GIF (или сплошную заливку темы)"""
        # Останавливаем предыдущую анимацию фона
        if self.gif_animation_source:
            GLib.source_remove(self.gif_animation_source)
            self.gif_animation_source = None
            self.current_gif_pixbuf = None

        if not self.bg_image or not os.path.exists(self.bg_image):
            self.set_solid_background()
            if hasattr(self, 'bg_info_label'):
                self.bg_info_label.set_label("Фон не установлен (сплошная заливка темы)")
            return

        if hasattr(self, 'bg_info_label'):
            self.bg_info_label.set_label(f"Текущий фон: {os.path.basename(self.bg_image)}")

        try:
            ext = os.path.splitext(self.bg_image)[1].lower()
            if ext in ['.gif', '.webp', '.apng']:
                # Загружаем как анимацию
                self.current_gif_pixbuf = GdkPixbuf.PixbufAnimation.new_from_file(self.bg_image)
                if self.current_gif_pixbuf and self.current_gif_pixbuf.is_static_image():
                    static_pixbuf = self.current_gif_pixbuf.get_static_image()
                    texture = Gdk.Texture.new_for_pixbuf(static_pixbuf)
                    self.bg_picture.set_paintable(texture)
                    return

                # Запускаем таймер для обновления кадров
                self.gif_animation_source = GLib.timeout_add(
                    40,  # ~25 FPS
                    self.update_gif_frame,
                    self.bg_picture
                )
            else:
                texture = Gdk.Texture.new_from_filename(self.bg_image)
                self.bg_picture.set_paintable(texture)
        except Exception as e:
            print(f"Ошибка установки фона: {e}")
            self.set_solid_background()

    def update_gif_frame(self, picture_widget):
        """Обновляет кадр анимации GIF (фон)"""
        if not self.current_gif_pixbuf:
            self.gif_animation_source = None
            return False

        try:
            # ВАЖНО: get_iter() требует GLib.TimeVal, а не int.
            # Передаём "сейчас": так как тикаем каждые 40 мс, кадры идут по порядку.
            iter_obj = self.current_gif_pixbuf.get_iter(GLib.get_current_time())
            if iter_obj:
                frame_pixbuf = iter_obj.get_pixbuf()
                if frame_pixbuf:
                    texture = Gdk.Texture.new_for_pixbuf(frame_pixbuf)
                    picture_widget.set_paintable(texture)
            return True
        except Exception as e:
            print(f"Ошибка обновления кадра GIF: {e}")
            self.gif_animation_source = None
            return False

    def update_accent_button_color(self):
        provider = Gtk.CssProvider()
        css = f"button {{ background-color: {self.accent_color}; border-radius: 50%; min-width: 24px; min-height: 24px; }}"
        provider.load_from_data(css.encode())
        display = Gdk.Display.get_default()
        Gtk.StyleContext.add_provider_for_display(display, provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

    def apply_dynamic_theme(self):
        css_string = generate_theme_css(self.accent_color, self.current_theme)
        self.css_provider.load_from_data(css_string.encode())
        display = Gdk.Display.get_default()
        Gtk.StyleContext.add_provider_for_display(
            display, 
            self.css_provider, 
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def on_theme_dropdown_changed(self, dropdown, pspec):
        selected = dropdown.get_selected()
        themes = ["dark", "neon", "retro"]
        if 0 <= selected < len(themes):
            self.current_theme = themes[selected]
            self.apply_dynamic_theme()
            self.apply_background()
            self.save_settings()

    def on_choose_accent_color(self, button):
        dialog = Gtk.ColorDialog()
        dialog.set_title("Выберите акцентный цвет")
        rgba = Gdk.RGBA()
        rgba.parse(self.accent_color)
        dialog.choose_rgba(self.window, rgba, None, self.on_color_selected)

    def on_color_selected(self, dialog, result):
        try:
            rgba = dialog.choose_rgba_finish(result)
            if rgba:
                new_color = "#{:02x}{:02x}{:02x}".format(
                    int(rgba.red * 255), 
                    int(rgba.green * 255), 
                    int(rgba.blue * 255)
                )
                self.accent_color = new_color
                self.update_accent_button_color()
                self.apply_dynamic_theme()
                self.save_settings()
        except Exception as e:
            print(f"Ошибка выбора цвета: {e}")

    # ========== ОБЛОЖКИ ПЛЕЙЛИСТОВ И ТРЕКОВ ==========

    def show_cover_placeholder(self):
        pixbuf = GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB, True, 8, 200, 200)
        pixbuf.fill(0x404040FF)
        texture = Gdk.Texture.new_for_pixbuf(pixbuf)
        self.cover_image.set_paintable(texture)

    def update_cover(self, track_path=None):
        """Обновляет обложку: либо трек, либо плейлист"""
        # Останавливаем предыдущую анимацию если была
        if self.cover_gif_source:
            GLib.source_remove(self.cover_gif_source)
            self.cover_gif_source = None
            self.current_cover_gif = None

        cover_to_show = None
        
        # 1. Приоритет у обложки плейлиста
        if hasattr(self, 'active_playlist') and self.active_playlist:
            pl_cover = self.get_playlist_cover(self.active_playlist)
            if pl_cover and os.path.exists(pl_cover):
                cover_to_show = pl_cover

        # 2. Если нет обложки плейлиста, ищем обложку трека
        if not cover_to_show and track_path:
            cover_to_show = self.find_cover_for_track(track_path)

        # 3. Отображаем найденное или заглушку
        if cover_to_show:
            try:
                ext = os.path.splitext(cover_to_show)[1].lower()
                # Проверяем, является ли файл анимированным
                if ext in ['.gif', '.webp', '.apng']:
                    anim = GdkPixbuf.PixbufAnimation.new_from_file(cover_to_show)
                    if anim and not anim.is_static_image():
                        # Запускаем специальную анимацию для обложки
                        self.start_gif_animation_for_cover(anim)
                        return
                
                # Если обычная картинка или статичный GIF
                pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(cover_to_show, 200, 200, True)
                texture = Gdk.Texture.new_for_pixbuf(pixbuf)
                self.cover_image.set_paintable(texture)
            except Exception as e:
                print(f"Ошибка загрузки обложки {cover_to_show}: {e}")
                self.show_cover_placeholder()
        else:
            self.show_cover_placeholder()

    def start_gif_animation_for_cover(self, animation):
        """Запускает цикл обновления кадров для обложки плеера"""
        self.current_cover_gif = animation
        
        # Обновляем каждые 40мс (~25 FPS)
        self.cover_gif_source = GLib.timeout_add(
            40, 
            self.update_cover_gif_frame, 
            self.cover_image
        )

    def update_cover_gif_frame(self, picture_widget):
        """Обновляет текущий кадр анимации обложки"""
        if not self.current_cover_gif:
            self.cover_gif_source = None
            return False

        try:
            iter_obj = self.current_cover_gif.get_iter(GLib.get_current_time())
            if iter_obj:
                frame_pixbuf = iter_obj.get_pixbuf()
                if frame_pixbuf:
                    # Масштабируем под размер виджета
                    scaled = frame_pixbuf.scale_simple(200, 200, GdkPixbuf.InterpType.BILINEAR)
                    if scaled:
                        texture = Gdk.Texture.new_for_pixbuf(scaled)
                        picture_widget.set_paintable(texture)
            return True  # Продолжаем анимацию
        except Exception as e:
            print(f"Ошибка кадра обложки: {e}")
            self.cover_gif_source = None
            return False  # Останавливаем при ошибке

    def get_playlist_cover(self, playlist_name):
        """Получает путь к обложке плейлиста из настроек"""
        try:
            settings_file = os.path.join(PLAYLISTS_DIR, f"{playlist_name}_cover.txt")
            if os.path.exists(settings_file):
                with open(settings_file, 'r') as f:
                    return f.read().strip()
        except Exception:
            pass
        return None

    def on_set_playlist_cover(self, button):
        """Установка обложки для текущего плейлиста"""
        if not hasattr(self, 'active_playlist') or not self.active_playlist:
            print("Сначала выберите или создайте плейлист")
            return
            
        dialog = Gtk.FileDialog()
        dialog.set_title("Выберите обложку для плейлиста (GIF/IMG)")
        img_filter = Gtk.FileFilter()
        img_filter.set_name("Изображения и GIF")
        img_filter.add_mime_type("image/*")
        img_filter.add_pattern("*.gif")
        img_filter.add_pattern("*.webp")
        img_filter.add_pattern("*.apng")
        dialog.set_default_filter(img_filter)
        dialog.open(self.window, None, self.on_playlist_cover_selected)

    def on_playlist_cover_selected(self, dialog, result):
        try:
            file = dialog.open_finish(result)
            if file and hasattr(self, 'active_playlist'):
                cover_path = file.get_path()
                settings_file = os.path.join(PLAYLISTS_DIR, f"{self.active_playlist}_cover.txt")
                with open(settings_file, 'w') as f:
                    f.write(cover_path)
                self.update_cover()
                print(f"✅ Обложка плейлиста '{self.active_playlist}' установлена")
        except Exception as e:
            print(f"Ошибка установки обложки плейлиста: {e}")

    def find_cover_for_track(self, track_path):
        folder = os.path.dirname(track_path)
        if not folder: return None
        cover_names = ["cover.jpg", "cover.png", "folder.jpg", "folder.png",
                       "front.jpg", "front.png", "Cover.jpg", "Cover.png",
                       "Folder.jpg", "Folder.png", "Front.jpg", "Front.png",
                       "COVER.jpg", "COVER.png", "cover.gif", "folder.gif"]
        for name in cover_names:
            path = os.path.join(folder, name)
            if os.path.isfile(path): return path
        return None

    # ========== УПРАВЛЕНИЕ ПЛЕЙЛИСТАМИ ==========

    def load_settings(self):
        try:
            if os.path.exists(SETTINGS_FILE):
                with open(SETTINGS_FILE, 'r') as f:
                    settings = json.load(f)
                    self.active_playlist = settings.get("active_playlist", "")
                    self.current_theme = settings.get("theme", "dark")
                    self.accent_color = settings.get("accent_color", "#89b4fa")
                    self.bg_image = settings.get("bg_image", None)
        except Exception as e:
            print(f"Ошибка загрузки настроек: {e}")

    def save_settings(self):
        try:
            settings = {
                "active_playlist": self.active_playlist,
                "theme": self.current_theme,
                "accent_color": self.accent_color,
                "bg_image": self.bg_image
            }
            with open(SETTINGS_FILE, 'w') as f:
                json.dump(settings, f)
        except Exception as e:
            print(f"Ошибка сохранения настроек: {e}")

    def load_all_playlists(self):
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
        model = Gtk.StringList.new(self.playlist_names)
        self.playlist_dropdown.set_model(model)

    def on_playlist_changed(self, dropdown, pspec):
        selected = dropdown.get_selected()
        if 0 <= selected < len(self.playlist_names):
            name = self.playlist_names[selected]
            self.switch_playlist(name)

    def switch_playlist(self, name):
        if name not in self.playlists:
            return
        self.player.set_state(Gst.State.NULL)
        self.current_index = -1
        self.title_label.set_label("Нет выбранного трека")
        self.playlist.clear()
        while self.playlist_list.get_first_child():
            child = self.playlist_list.get_first_child()
            self.playlist_list.remove(child)
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
        self.update_cover()  # Обновляем обложку плейлиста
        self.save_settings()

    def on_new_playlist(self, button):
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
                model = Gtk.StringList.new(self.playlist_names)
                self.playlist_dropdown.set_model(model)
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
        except Exception: pass

    def seek_backward(self):
        try:
            position = self.player.query_position(Gst.Format.TIME)[1]
            new_pos = max(position - 10 * Gst.SECOND, 0)
            self.player.seek_simple(Gst.Format.TIME, Gst.SeekFlags.FLUSH, new_pos)
        except Exception: pass

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
                        self.add_to_library(path)
                        
            if added > 0:
                self.update_playlist_info()
                if self.current_index == -1 and self.playlist:
                    first_new = len(self.playlist) - added
                    self.play_index(first_new)
        except Exception as e:
            print(f"Ошибка при перетаскивании: {e}")

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
                    if not line or line.startswith('#'): continue
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
                        self.add_to_library(track_path)
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
                        self.add_to_library(path)
                        
                self.update_playlist_info()
                if self.current_index == -1 and self.playlist:
                    self.play_index(0)
        except Exception as e:
            print(f"Ошибка при выборе файлов: {e}")

    def on_remove_track(self, button):
        row = self.playlist_list.get_selected_row()
        if row is None: return
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
        if index < 0 or index >= len(self.playlist): return
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
        self.update_cover(path)  # Обновляем обложку трека
        self.highlight_current_track()
        self.update_play_stats(path)

    def highlight_current_track(self):
        row = self.playlist_list.get_row_at_index(self.current_index)
        if row: self.playlist_list.select_row(row)

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
        if not self.playlist: return
        new_index = self.current_index - 1
        if new_index < 0: new_index = len(self.playlist) - 1
        self.play_index(new_index)

    def on_next(self, button):
        if not self.playlist: return
        new_index = self.current_index + 1
        if new_index >= len(self.playlist): new_index = 0
        self.play_index(new_index)

    def on_volume_changed(self, scale):
        if self._volume_changing: return
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
                    
                    self.profile["listening_time"] = self.profile.get("listening_time", 0) + 1
                    if self.profile["listening_time"] % 60 == 0:
                        self.save_profile()
            except Exception: pass
        return True

    def format_time(self, seconds):
        mins = seconds // 60
        secs = seconds % 60
        return f"{mins}:{secs:02d}"

    def on_progress_changed(self, scale):
        if self._updating: return
        try:
            duration = self.player.query_duration(Gst.Format.TIME)[1]
            if duration > 0:
                value = scale.get_value()
                new_pos = int((value / 100) * duration)
                self.player.seek_simple(Gst.Format.TIME, Gst.SeekFlags.FLUSH, new_pos)
        except Exception: pass

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