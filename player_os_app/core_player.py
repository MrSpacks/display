"""
Главный класс медиаплеера PlayerOS
"""

import os
import subprocess
import shutil
import signal

import time
from .config import BASE_PATH, BUTTONS, FOLDERS, DEFAULT_VOLUME, FONTS, VOLUME_DISPLAY_DURATION
from .utils import get_files, get_file_type, stop_ffplay

# Опциональные импорты
try:
    import vlc
except ImportError:
    vlc = None

try:
    from PIL import ImageFont, Image
except ImportError:
    ImageFont = None
    Image = None

import threading


def check_ffplay_availability():
    """Проверить, доступен ли ffplay в системе"""
    result = subprocess.run(['which', 'ffplay'], capture_output=True)
    return result.returncode == 0


class PlayerOS:
    """
    Главный класс медиаплеера
    Управляет состояниями (меню, браузер файлов, воспроизведение)
    и отрисовкой интерфейса на экран
    """

    def __init__(self):
        """
        Инициализация приложения
        - Установка начального состояния (главное меню)
        - Создание экземпляра VLC плеера
        - Загрузка шрифтов для дисплея
        """

        # ===== СОСТОЯНИЕ ПРИЛОЖЕНИЯ =====
        self.state = "MAIN_MENU"  # Текущее состояние
        self.selected_idx = 0  # Индекс выбранного пункта
        self.current_folder = ""  # Текущая открытая папка
        self.files = []  # Список файлов в текущей папке
        self.status_message = "Ready"
        self.audio_output_mode = "jack"  # jack | bluetooth
        self.bt_devices = []  # [{'mac': str, 'name': str}]
        self.connected_bt_mac = None
        self.connected_bt_name = ""
        self.bt_connected = False
        self.last_bt_status_check = 0.0

        # ===== ГРОМКОСТЬ =====
        self.volume = DEFAULT_VOLUME
        self.volume_display_time = 0  # Время последнего изменения громкости

        # ===== ПРОИГРЫВАНИЕ ЧЕРЕЗ FFPLAY =====
        self.ffplay_process = None  # Текущий процесс ffplay
        self.audio_process = None  # Отдельный аудиопроцесс (для видео)
        self.is_playing = False  # Флаг проигрывания
        self.is_paused = False  # Флаг паузы воспроизведения
        self.video_target_fps = 24  # Целевая частота кадров для экрана

        # ===== ДЛЯ ПРОСМОТРА ВИДЕО (ДЕКОДИРОВАНИЕ В PYTHON) =====
        self.video_frame = None          # Текущий кадр видео
        self.video_reader_thread = None  # Поток для чтения видеокадров
        self.stop_video_reader = False   # Флаг для остановки потока

        # ===== ОТСЛЕЖИВАНИЕ НАЖАТИЙ КНОПОК =====
        self.button_states = {name: True for name in BUTTONS}  # True = не нажата

        # ===== ДЛЯ ПРОСМОТРА ФОТО =====
        self.current_image = None  # Текущее загруженное изображение

        # ===== VLC ПЛЕЕР (если установлен) =====
        if vlc:
            self.vlc = vlc.Instance('--no-xlib --quiet')
            self.player = self.vlc.media_player_new()
        else:
            self.vlc = None
            self.player = None

        # ===== ШРИФТЫ ДЛЯ ЭКРАНА =====
        if ImageFont:
            try:
                self.font = ImageFont.truetype(
                    FONTS['regular']['path'],
                    FONTS['regular']['size']
                )
                self.big_font = ImageFont.truetype(
                    FONTS['bold']['path'],
                    FONTS['bold']['size']
                )
            except FileNotFoundError:
                self.font = ImageFont.load_default()
                self.big_font = ImageFont.load_default()
        else:
            self.font = None
            self.big_font = None

    def get_files(self, folder):
        """Получить список файлов в папке"""
        return get_files(folder)

    def get_settings_items(self):
        """Сформировать пункты меню настроек"""
        output_label = "3.5mm Jack" if self.audio_output_mode == "jack" else "Bluetooth"
        return [
            f"Audio Output: {output_label}",
            "Bluetooth: Scan devices",
            "Bluetooth: Disconnect",
        ]

    def _run_cmd(self, cmd):
        """Выполнить команду и вернуть (ok, stdout, stderr)."""
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode == 0, result.stdout.strip(), result.stderr.strip()

    def _is_named_bt_device(self, name, mac):
        """Проверить, что имя устройства не является пустышкой."""
        if not name:
            return False

        n = name.strip()
        if not n:
            return False

        lowered = n.lower()
        if lowered in ("unknown", "(unknown)", "n/a"):
            return False

        return n != mac

    def refresh_bt_connection_status(self, force=False):
        """Обновить статус подключенного Bluetooth устройства."""
        if shutil.which("bluetoothctl") is None:
            self.bt_connected = False
            self.connected_bt_mac = None
            self.connected_bt_name = ""
            return False

        now = time.time()
        if not force and (now - self.last_bt_status_check) < 2.0:
            return self.bt_connected

        self.last_bt_status_check = now
        ok, out, _ = self._run_cmd(["bluetoothctl", "devices", "Connected"])
        if not ok or not out.strip():
            self.bt_connected = False
            self.connected_bt_mac = None
            self.connected_bt_name = ""
            return False

        for line in out.splitlines():
            if not line.startswith("Device "):
                continue

            parts = line.split(maxsplit=2)
            if len(parts) >= 2:
                self.bt_connected = True
                self.connected_bt_mac = parts[1]
                self.connected_bt_name = parts[2] if len(parts) >= 3 else parts[1]
                return True

        self.bt_connected = False
        self.connected_bt_mac = None
        self.connected_bt_name = ""
        return False

    def _find_pulse_sink(self, needle):
        """Найти PulseAudio/PipeWire sink по подстроке."""
        if shutil.which("pactl") is None:
            return None

        ok, out, _ = self._run_cmd(["pactl", "list", "short", "sinks"])
        if not ok:
            return None

        needle = needle.lower()
        for line in out.splitlines():
            parts = line.split()
            if len(parts) >= 2 and needle in parts[1].lower():
                return parts[1]
        return None

    def apply_audio_output(self, mode):
        """Переключить аудиовыход: jack или bluetooth."""
        if mode not in ("jack", "bluetooth"):
            self.status_message = "Audio: unknown mode"
            return False

        if mode == "jack":
            switched = False

            analog_sink = self._find_pulse_sink("analog-stereo")
            if analog_sink:
                self._run_cmd(["pactl", "set-default-sink", analog_sink])
                switched = True

            if shutil.which("amixer"):
                ok, _, _ = self._run_cmd(["amixer", "cset", "numid=3", "1"])
                switched = switched or ok

            self.audio_output_mode = "jack"
            self.status_message = "Audio output: 3.5mm Jack" if switched else "Jack selected (check mixer)"
            return switched

        bt_sink = self._find_pulse_sink("bluez_output")
        if bt_sink:
            self._run_cmd(["pactl", "set-default-sink", bt_sink])
            self.audio_output_mode = "bluetooth"
            self.status_message = "Audio output: Bluetooth"
            return True

        self.audio_output_mode = "bluetooth"
        self.status_message = "No BT audio sink"
        return False

    def scan_bluetooth_devices(self, timeout_sec=8):
        """Поиск Bluetooth устройств через bluetoothctl."""
        if shutil.which("bluetoothctl") is None:
            self.status_message = "bluetoothctl not found"
            self.bt_devices = []
            return []

        self._run_cmd(["bluetoothctl", "--timeout", str(timeout_sec), "scan", "on"])
        ok, out, _ = self._run_cmd(["bluetoothctl", "devices"])
        devices = []

        if ok:
            for line in out.splitlines():
                # Формат: Device XX:XX:XX:XX:XX:XX Device Name
                if not line.startswith("Device "):
                    continue
                parts = line.split(maxsplit=2)
                if len(parts) >= 2:
                    mac = parts[1]
                    name = parts[2] if len(parts) >= 3 else mac
                    devices.append({"mac": mac, "name": name})

        # Сначала устройства с осмысленным названием, затем безымянные/по MAC.
        devices.sort(key=lambda d: (0 if self._is_named_bt_device(d["name"], d["mac"]) else 1, d["name"].lower(), d["mac"]))

        self.bt_devices = devices
        self.refresh_bt_connection_status(force=True)
        self.status_message = f"BT found: {len(devices)}"
        return devices

    def connect_bt_device(self, mac):
        """Подключить Bluetooth устройство по MAC адресу."""
        if shutil.which("bluetoothctl") is None:
            self.status_message = "bluetoothctl not found"
            return False

        self._run_cmd(["bluetoothctl", "trust", mac])
        ok_pair, _, _ = self._run_cmd(["bluetoothctl", "pair", mac])
        ok_conn, out, err = self._run_cmd(["bluetoothctl", "connect", mac])

        success = ok_conn and bool("successful" in out.lower() or "connection successful" in out.lower() or out)
        if success:
            self.refresh_bt_connection_status(force=True)
            if not self.bt_connected:
                self.connected_bt_mac = mac
                self.connected_bt_name = mac
                self.bt_connected = True
            self.apply_audio_output("bluetooth")
            if self.connected_bt_name:
                self.status_message = f"BT connected: {self.connected_bt_name}"
            else:
                self.status_message = f"BT connected: {mac}"
            return True

        if ok_pair and not ok_conn:
            self.status_message = f"Pair OK, connect failed: {mac}"
        else:
            self.status_message = f"BT connect failed: {err or out or mac}"
        return False

    def disconnect_bt_device(self):
        """Отключить текущее Bluetooth устройство."""
        if shutil.which("bluetoothctl") is None:
            self.status_message = "bluetoothctl not found"
            return False

        target = self.connected_bt_mac
        if target is None:
            ok, out, _ = self._run_cmd(["bluetoothctl", "devices", "Connected"])
            if ok:
                for line in out.splitlines():
                    parts = line.split(maxsplit=2)
                    if len(parts) >= 2 and parts[0] == "Device":
                        target = parts[1]
                        break

        if target:
            ok, out, err = self._run_cmd(["bluetoothctl", "disconnect", target])
            if ok:
                self.bt_connected = False
                self.connected_bt_mac = None
                self.connected_bt_name = ""
                self.status_message = f"BT disconnected: {target}"
                return True
            self.status_message = f"BT disconnect failed: {err or out}"
            return False

        self.status_message = "No BT device connected"
        return False

    def draw(self, draw):
        """
        Отрисовать текущий экран в зависимости от состояния приложения
        
        Args:
            draw: Canvas объект для рисования
        """
        # Реализация отрисовки в отдельном модуле
        pass

    def handle_click(self, btn):
        """
        Обработать нажатие кнопки
        
        Args:
            btn (str): Название нажатой кнопки
        """
        pass

    def play_media(self):
        """Начать воспроизведение выбранного файла через ffplay"""
        file_path = os.path.join(
            BASE_PATH,
            self.current_folder.lower(),
            self.files[self.selected_idx]
        )
        print(f"DEBUG: play_media() - File: {file_path}")
        print(f"DEBUG: File exists: {os.path.exists(file_path)}")
        
        try:
            self.stop_media()

            # Громкость от 0 до 1.0 для ffplay фильтра
            volume_value = self.volume / 100.0
            cmd = [
                "ffplay",
                "-nodisp",
                "-autoexit",
                "-hide_banner",
                "-loglevel", "error",
                "-af", f"volume={volume_value}",  # Audio filter для регулировки громкости
                file_path
            ]
            print(f"DEBUG: Command: {' '.join(cmd)}")
            
            self.ffplay_process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            self.is_playing = True
            self.is_paused = False
            self.state = "PLAYING"
            print(f"Playing: {self.files[self.selected_idx]}")
        except Exception as e:
            print(f"Ошибка при воспроизведении: {e}")
            self.is_playing = False

    def play_next(self):
        """Проигрыватель следующий файл в плейлисте"""
        if self.files and self.selected_idx < len(self.files) - 1:
            self.selected_idx += 1
            self.play_media()
        else:
            self.is_playing = False
            self.state = "FILE_BROWSER"

    def stop_media(self):
        """Остановить воспроизведение"""
        self.stop_video_reader = True  # Остановить поток видео
        if self.video_reader_thread and self.video_reader_thread.is_alive():
            self.video_reader_thread.join(timeout=1)  # Ждем завершения потока
        self.video_reader_thread = None
        self.ffplay_process = stop_ffplay(self.ffplay_process)
        self.audio_process = stop_ffplay(self.audio_process)
        self.is_playing = False
        self.is_paused = False
        self.video_frame = None

    def toggle_pause(self):
        """Поставить на паузу/снять с паузы текущее воспроизведение."""
        if not self.is_playing:
            return False

        targets = [p for p in (self.ffplay_process, self.audio_process) if p and p.poll() is None]
        if not targets:
            return False

        sig = signal.SIGCONT if self.is_paused else signal.SIGSTOP
        for proc in targets:
            proc.send_signal(sig)

        self.is_paused = not self.is_paused
        return True

    def view_photo(self):
        """Загрузить и отобразить фото на полный экран"""
        from PIL import Image
        
        file_path = os.path.join(
            BASE_PATH,
            self.current_folder.lower(),
            self.files[self.selected_idx]
        )
        try:
            img = Image.open(file_path)
            img.thumbnail((320, 240), Image.Resampling.LANCZOS)
            self.current_image = img
            self.state = "VIEWING"
        except Exception as e:
            print(f"Ошибка при загрузке фото: {e}")

    def view_video(self):
        """Запустить просмотр видео, декодировав его ffmpeg'ом"""
        file_path = os.path.join(
            BASE_PATH,
            self.current_folder.lower(),
            self.files[self.selected_idx]
        )
        
        if not os.path.exists(file_path):
            print(f"ERROR: Video file not found: {file_path}")
            self.is_playing = False
            return
        
        print(f"DEBUG: view_video() - File: {file_path}")
        
        try:
            self.stop_media()

            volume_scale = self.volume / 100.0

            # Отдельный аудиопроцесс, чтобы видео шло в Python, а звук - в ALSA/Pulse.
            audio_cmd = [
                "ffplay",
                "-nodisp",
                "-autoexit",
                "-vn",
                "-hide_banner",
                "-loglevel", "error",
                "-af", f"volume={volume_scale}",
                file_path
            ]
            print(f"DEBUG: Audio command: {' '.join(audio_cmd)}")
            self.audio_process = subprocess.Popen(
                audio_cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            # ffmpeg команда для декодирования видео в RGB24 пиксели
            # Масштабируем в 320x240, формат RGB24, выводим в пайп
            cmd = [
                "ffmpeg",
                "-re",                             # Декодировать в реальном времени для синхронизации со звуком
                "-i", file_path,
                "-an",                             # Аудио декодирует отдельный ffplay
                "-threads", "2",
                "-vf", f"fps={self.video_target_fps},scale=320:240:flags=fast_bilinear",
                "-pix_fmt", "rgb24",              # RGB24 формат пикселей
                "-f", "rawvideo",                 # Сырой видео формат
                "-loglevel", "error",             # Минимум логирования
                "-"                               # Вывод в stdout
            ]
            
            print(f"DEBUG: Command: {' '.join(cmd)}")
            
            self.ffplay_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                bufsize=320 * 240 * 3  # RGB24 = 3 байта на пиксель
            )
            
            self.is_playing = True
            self.is_paused = False
            self.state = "VIEWING"
            print(f"Playing video: {self.files[self.selected_idx]}")
            
            # Запускаем поток для чтения видеокадров
            self.stop_video_reader = False
            self.video_reader_thread = threading.Thread(
                target=self._read_video_frames,
                daemon=True
            )
            self.video_reader_thread.start()
            
        except Exception as e:
            print(f"Ошибка при запуске видео: {e}")
            self.is_playing = False

    def _read_video_frames(self):
        """Читать видеокадры из ffmpeg в отдельном потоке"""
        try:
            frame_data = bytearray(320 * 240 * 3)  # RGB24: 3 байта на пиксель
            frame_size = len(frame_data)
            
            while not self.stop_video_reader and self.ffplay_process and self.is_playing:
                # Читаем один кадр (320x240x3 байтов)
                bytes_read = self.ffplay_process.stdout.readinto(frame_data)
                
                if not bytes_read or bytes_read != frame_size:
                    # Конец видео
                    print("DEBUG: End of video stream")
                    self.is_playing = False
                    break
                
                # Преобразуем сырые пиксели в PIL Image без лишней промежуточной копии.
                img = Image.frombytes('RGB', (320, 240), frame_data)
                self.video_frame = img
                
        except Exception as e:
            print(f"DEBUG: Video reader error: {e}")
            self.is_playing = False
        finally:
            if self.ffplay_process:
                self.ffplay_process.terminate()
            if self.audio_process:
                self.audio_process.terminate()

    def connect_bt(self):
        """Подключить Bluetooth устройство"""
        self.scan_bluetooth_devices()
