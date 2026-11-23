# 🎵 Plastic Player

Простой и лёгкий музыкальный плеер для Linux, написанный на Python с использованием GTK4 и GStreamer.

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)
![GTK](https://img.shields.io/badge/GTK-4.0-green?logo=gtk)
![License](https://img.shields.io/badge/License-MIT-yellow)

## ✨ Возможности

- 🎧 Воспроизведение аудиофайлов (MP3, FLAC, OGG, WAV и другие форматы)
- 🔊 Регулировка громкости (0% — 200%)
- ⏩ Перемотка трека через прогресс-бар
- 📁 Открытие файлов через диалог выбора
- 🎨 Нативный интерфейс GTK4
- 🐧 Работа на любом Linux-дистрибутиве

## 🚀 Установка

### 1. Клонируйте репозиторий

```bash
git clone https://github.com/toothpasted820-cmyk/Plastic-player.git
cd Plastic-player
```

### 2. Установите зависимости

**Ubuntu / Debian / Pop!_OS:**
```bash
sudo apt install python3-gi python3-gst-1.0 \
    gstreamer1.0-plugins-base gstreamer1.0-plugins-good \
    gstreamer1.0-plugins-bad gstreamer1.0-plugins-ugly
```

**Fedora / RHEL:**
```bash
sudo dnf install python3-gobject gstreamer1-plugins-base \
    gstreamer1-plugins-good gstreamer1-plugins-bad-free \
    gstreamer1-plugins-ugly-free
```

**Arch Linux / Manjaro:**
```bash
sudo pacman -S python-gobject gst-plugins-base gst-plugins-good \
    gst-plugins-bad gst-plugins-ugly
```

### 3. Запустите плеер

```bash
python3 main.py
```

## 📖 Использование

1. Нажмите кнопку **📁 Открыть файл**
2. Выберите аудиофайл на компьютере
3. Используйте кнопки управления:
   - ▶ **Играть** — начать/возобновить воспроизведение
   - ⏸ **Пауза** — поставить на паузу
   - ⏹ **Стоп** — остановить и сбросить позицию
4. Перетаскивайте **ползунок прогресса** для перемотки
5. Регулируйте **громкость** ползунком справа (1.0 = 100%, 2.0 = 200%)

## 🛠 Технологии

- **Python 3** — язык программирования
- **GTK4** — графический интерфейс
- **GStreamer** — мультимедийный фреймворк для воспроизведения аудио
- **PyGObject** — Python-биндинги для GTK и GStreamer

## 🗺 Планы развития

- [ ] 📋 Плейлист с очередью треков
- [ ] 🖼️ Отображение обложек альбомов и метаданных (ID3-теги)
- [ ] ⌨️ Горячие клавиши (Space, стрелки, Ctrl+O)
- [ ] 🎨 Кастомизация интерфейса через CSS
- [ ] 🌐 Интеграция с музыкальными сервисами (Spotify, Яндекс Музыка, VK)
- [ ] 📦 Упаковка в AppImage/Flatpak для удобной установки

## 🤝 Вклад в проект

Проект находится в активной разработке. Если у вас есть идеи или предложения — создавайте Issue или Pull Request!

## 📄 Лицензия

Этот проект распространяется под лицензией MIT. Подробнее см. в файле [LICENSE](LICENSE).

---

**Создано с ❤️ для Linux**
