"""
Управление дисплеем и отрисовкой
"""

import time
import sys
from PIL import Image, ImageDraw

from luma.core.interface.serial import spi
from luma.lcd.device import st7789
from luma.core.render import canvas

from .config import DISPLAY_CONFIG, FOLDERS, VOLUME_BAR, VOLUME_DISPLAY_DURATION, BACKLIGHT
from .utils import get_file_icon, compute_progress_fill_rect

try:
    import RPi.GPIO as GPIO
except ImportError:
    GPIO = None


class Display:
    """Класс для управления дисплеем"""

    def __init__(self):
        """Инициализация дисплея ST7789"""
        self.backlight_pwm = None

        try:
            print("Initializing SPI interface...")
            spi_speed_hz = DISPLAY_CONFIG.get('spi_speed_hz', 32000000)
            serial = spi(
                port=DISPLAY_CONFIG['port'],
                device=DISPLAY_CONFIG['device'],
                gpio_DC=DISPLAY_CONFIG['gpio_DC'],
                gpio_RST=DISPLAY_CONFIG['gpio_RST'],
                bus_speed_hz=spi_speed_hz
            )
            print(f"✓ SPI interface initialized ({spi_speed_hz} Hz)")
            
            print("Initializing ST7789 device...")
            self.device = st7789(
                serial,
                width=DISPLAY_CONFIG['width'],
                height=DISPLAY_CONFIG['height'],
                rotate=DISPLAY_CONFIG['rotate']
            )
            print(f"✓ Display initialized: {DISPLAY_CONFIG['width']}x{DISPLAY_CONFIG['height']}")
            
            # Инверсия цветов (если нужно)
            self.device.command(0x21)

            # Опциональная инициализация подсветки, если BL/LED подключен к GPIO.
            self._init_backlight()
            print("✓ Display ready")
            
        except PermissionError as e:
            print(f"\n✗ ERROR: Permission denied - {e}")
            print("  This usually means GPIO requires higher privileges.")
            print("  Try running with sudo: sudo python3 -m player_os_app.main")
            sys.exit(1)
        except Exception as e:
            print(f"\n✗ ERROR: Display initialization failed")
            print(f"  Error: {type(e).__name__}: {e}")
            print("  Check GPIO pins in config.py")
            sys.exit(1)

    def _init_backlight(self):
        """Настроить подсветку по BACKLIGHT конфигу."""
        if not BACKLIGHT.get("enabled", False):
            return

        if GPIO is None:
            print("WARNING: RPi.GPIO is unavailable, backlight control disabled")
            return

        pin = int(BACKLIGHT.get("gpio", 18))
        pwm_hz = int(BACKLIGHT.get("pwm_hz", 1000))
        brightness = int(BACKLIGHT.get("brightness_percent", 100))
        active_high = bool(BACKLIGHT.get("active_high", True))
        brightness = max(0, min(100, brightness))

        GPIO.setup(pin, GPIO.OUT)

        if pwm_hz > 0:
            self.backlight_pwm = GPIO.PWM(pin, pwm_hz)
            duty = brightness if active_high else (100 - brightness)
            self.backlight_pwm.start(duty)
            print(f"✓ Backlight PWM: GPIO{pin}, {brightness}%")
        else:
            on = GPIO.HIGH if (brightness > 0) == active_high else GPIO.LOW
            GPIO.output(pin, on)
            print(f"✓ Backlight GPIO{pin}: {'ON' if brightness > 0 else 'OFF'}")

    def cleanup(self):
        """Освободить ресурсы дисплея."""
        if self.backlight_pwm:
            self.backlight_pwm.stop()
            self.backlight_pwm = None

    def update(self, app):
        """Обновить дисплей в зависимости от состояния приложения"""
        def visible_window(total, selected, max_visible):
            """Вернуть диапазон [start, end) для прокрутки списка."""
            if total <= 0:
                return 0, 0
            if total <= max_visible:
                return 0, total

            start = max(0, selected - (max_visible // 2))
            end = start + max_visible
            if end > total:
                end = total
                start = end - max_visible
            return start, end

        if app.state == "VIEWING" and (app.video_frame or app.current_image):
            # Для полноцветных кадров используем прямой вывод PIL изображения на устройство.
            if app.video_frame:
                img = app.video_frame
                if img.mode != "RGB":
                    img = img.convert("RGB")
                self.device.display(img)
                return
            else:
                frame = Image.new("RGB", (self.device.width, self.device.height), "black")
                img = app.current_image
                if img.mode != "RGB":
                    img = img.convert("RGB")

                img_width, img_height = img.size
                x = (self.device.width - img_width) // 2
                y = 20 + ((self.device.height - 20 - img_height) // 2)

                painter = ImageDraw.Draw(frame)
                painter.rectangle([0, 0, self.device.width, 20], fill="black")
                painter.text((10, 5), "Viewing Image", fill="cyan", font=app.font)
                frame.paste(img, (x, y))

                self.device.display(frame)
            return

        with canvas(self.device) as draw:
            if app.state == "MAIN_MENU":
                # ===== ГЛАВНОЕ МЕНЮ =====
                # Сдвинули заголовок вниз на 20px для видимости на дисплее
                draw.text((30, 40), "--- MEDIA PLAYER ---", fill="yellow", font=app.big_font)
                for i, item in enumerate(FOLDERS):
                    color = "white"
                    # Сдвинули меню вниз относительно заголовка (60px)
                    y_pos = 80 + i * 30  # 35px - это расстояние между пунктами меню
                    if i == app.selected_idx:
                        draw.rectangle([10, y_pos, 310, y_pos + 28], outline="red", width=2) # 
                        color = "red"
                    # Добавили иконку папки перед названием
                    icon = '⚙' if item == "Settings" else '▣'
                    draw.text((20, y_pos), f"{icon} {item}", fill=color, font=app.font)

            elif app.state == "SETTINGS_MENU":
                # ===== МЕНЮ НАСТРОЕК =====
                draw.text((30, 35), "Settings", fill="yellow", font=app.big_font)

                bt_line = "BT: disconnected"
                if app.bt_connected:
                    bt_line = f"BT: connected {app.connected_bt_name[:16]}"
                draw.text((10, 65), bt_line, fill="green" if app.bt_connected else "gray", font=app.font)

                items = app.get_settings_items()
                start, end = visible_window(len(items), app.selected_idx, max_visible=4)

                for row, i in enumerate(range(start, end)):
                    item = items[i]
                    y_pos = 100 + row * 30
                    color = "white"
                    if i == app.selected_idx:
                        draw.rectangle([8, y_pos - 2, 312, y_pos + 24], outline="orange", width=2)
                        color = "orange"
                    draw.text((16, y_pos), item[:34], fill=color, font=app.font)

                if start > 0:
                    draw.text((294, 40), "▲", fill="gray", font=app.font)
                if end < len(items):
                    draw.text((294, 188), "▼", fill="gray", font=app.font)

                draw.text((10, 210), app.status_message[:40], fill="cyan", font=app.font)

            elif app.state == "BT_DEVICES":
                # ===== СПИСОК BLUETOOTH УСТРОЙСТВ =====
                draw.text((30, 40), "BT devices (SELECT connect)", fill="yellow", font=app.font)

                if not app.bt_devices:
                    draw.text((10, 70), "No devices found", fill="white", font=app.font)
                    draw.text((10, 100), "BACK to Settings", fill="gray", font=app.font)
                else:
                    start, end = visible_window(len(app.bt_devices), app.selected_idx, max_visible=5)
                    for row, i in enumerate(range(start, end)):
                        dev = app.bt_devices[i]
                        y_pos = 75 + row * 32
                        color = "white"
                        if i == app.selected_idx:
                            draw.rectangle([6, y_pos - 2, 314, y_pos + 24], outline="green", width=2)
                            color = "green"
                        marker = "*" if app.connected_bt_mac == dev['mac'] else " "
                        label = f"{marker} {dev['name'][:16]} {dev['mac'][-5:]}"
                        draw.text((12, y_pos), label, fill=color, font=app.font)

                    if start > 0:
                        draw.text((294, 40), "▲", fill="gray", font=app.font)
                    if end < len(app.bt_devices):
                        draw.text((294, 188), "▼", fill="gray", font=app.font)

                draw.text((10, 210), app.status_message[:40], fill="cyan", font=app.font)

            elif app.state == "FILE_BROWSER":
                # ===== БРАУЗЕР ФАЙЛОВ =====
                breadcrumb = app.current_folder
                if app.current_path:
                    breadcrumb = f"{app.current_folder}/{app.current_path}"

                # Чтобы заголовок всегда был виден, ограничиваем длину.
                if len(breadcrumb) > 24:
                    breadcrumb = "..." + breadcrumb[-21:]
                draw.text((10, 34), f"Folder: {breadcrumb}", fill="cyan", font=app.big_font)

                # На реальном ST7789 используем плотный список: 5 строк без обрезки снизу.
                start, end = visible_window(len(app.files), app.selected_idx, max_visible=5)
                for row, i in enumerate(range(start, end)):
                    item_name = app.files[i]
                    color = "white"
                    y_pos = 62 + row * 28
                    if i == app.selected_idx:
                        draw.rectangle([5, y_pos, 315, y_pos + 26], outline="green", width=2)

                    if y_pos <= 220:
                        is_dir = app.is_directory(item_name, app.current_folder, app.current_path)
                        icon = get_file_icon(item_name, is_directory=is_dir)
                        filename_display = item_name[:25]
                        draw.text((12, y_pos + 3), f"{icon} {filename_display}", fill=color, font=app.font)

                if start > 0:
                    draw.text((294, 55), "▲", fill="gray", font=app.font)
                if end < len(app.files):
                    draw.text((294, 210), "▼", fill="gray", font=app.font)

            elif app.state == "PLAYING":
                # ===== ЭКРАН ВОСПРОИЗВЕДЕНИЯ =====
                # Сдвинули информацию вниз на 20px от верхнего края
                draw.text((30, 40), "Now Playing:", fill="yellow", font=app.font)
                draw.text((20, 70), app.files[app.selected_idx][:20], fill="white", font=app.font)
                
                if app.is_paused:
                    status = "Paused"
                elif app.ffplay_process and app.ffplay_process.poll() is None:
                    status = "Playing"
                else:
                    status = "Ended"
                    app.is_playing = False
                
                draw.text((30, 100), status, fill="green", font=app.font)

                # Показывать полосу громкости только если недавно была нажата кнопка
                show_volume_bar = (time.time() - app.volume_display_time) < VOLUME_DISPLAY_DURATION
                
                if show_volume_bar:
                    # Полоса громкости (видна 2 секунды после нажатия)
                    bar = VOLUME_BAR
                    draw.rectangle([bar['x'], bar['y'], bar['x'] + bar['width'], bar['y'] + bar['height']],
                                 outline="white", fill="black", width=1)
                    
                    filled_height = int((app.volume / 100.0) * bar['height'])
                    if filled_height > 0:
                        fill_y = bar['y'] + bar['height'] - filled_height
                        draw.rectangle([bar['x'] + 2, fill_y, bar['x'] + bar['width'] - 2, bar['y'] + bar['height'] - 2],
                                     fill="green")
                    
                    draw.text((bar['x'] - 20, bar['y'] + bar['height'] + 10), f"{app.volume}%",
                             fill="white", font=app.font)
                
                # ===== ПРОГРЕСС-БАР И ВРЕМЯ =====
                # Получить текущее время воспроизведения
                current_time = app.get_playback_progress()
                total_time = app.current_track_duration
                
                # Вычислить процент
                if total_time > 0:
                    progress_percent = min(100, (current_time / total_time) * 100)
                else:
                    progress_percent = 0
                
                # Размеры прогресс-бара
                progress_bar_y = 130
                progress_bar_height = 8
                progress_bar_width = 280
                progress_bar_x = 20
                
                # Нарисовать фон прогресс-бара
                draw.rectangle([progress_bar_x, progress_bar_y, progress_bar_x + progress_bar_width, 
                               progress_bar_y + progress_bar_height],
                              outline="white", fill="black", width=1)
                
                # Нарисовать заполненную часть
                fill_rect = compute_progress_fill_rect(
                    progress_bar_x,
                    progress_bar_y,
                    progress_bar_width,
                    progress_bar_height,
                    progress_percent,
                    padding=2,
                )
                if fill_rect:
                    draw.rectangle(fill_rect, fill="cyan")
                
                # Форматировать время
                current_time = min(current_time, total_time) if total_time > 0 else current_time
                if hasattr(app, "format_playback_time"):
                    time_text = f"{app.format_playback_time(current_time)} / {app.format_playback_time(total_time)}"
                else:
                    mins_cur = int(current_time) // 60
                    secs_cur = int(current_time) % 60
                    mins_total = int(total_time) // 60
                    secs_total = int(total_time) % 60
                    time_text = f"{mins_cur}:{secs_cur:02d} / {mins_total}:{secs_total:02d}"
                draw.text((30, 145), f"{progress_percent:.0f}%  {time_text}", fill="white", font=app.font)
                
                draw.text((15, 180), "▲ ▼ Vol     ◀ <<      ▶ >>     || ▶", fill="grey", font=app.font)

            elif app.state == "VIEWING":
                # ===== РЕЖИМ ПРОСМОТРА (ФОТО/ВИДЕО) =====
                if app.is_playing:
                    draw.rectangle([0, 0, 320, 240], fill="black")
                    title = "Paused Video" if app.is_paused else "Playing Video..."
                    draw.text((30, 50), title, fill="white", font=app.big_font)
                    draw.text((30, 80), "Press BACK to stop", fill="gray", font=app.font)
                else:
                    draw.rectangle([0, 0, 320, 240], fill="black")
                    draw.text((30, 50), "Loading...", fill="white", font=app.big_font)
