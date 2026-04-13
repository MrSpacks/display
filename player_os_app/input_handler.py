"""
Обработка входа (кнопок)
Zpracování vstupu (tlačítek)
"""

import time

from .config import FOLDERS, BUTTONS
from .utils import get_file_type


class InputHandler:
    """Класс для обработки нажатий кнопок
    Třída pro zpracování stisknutí tlačítek"""

    @staticmethod
    def handle_click(app, btn):
        """
        Обработать нажатие кнопки
        Zpracovat stisknutí tlačítka
        
        Args:
            app: Экземпляр PlayerOS
            btn (str): Название нажатой кнопки
        """
        def current_list_limit():
            if app.state == "MAIN_MENU":
                return len(FOLDERS)
            if app.state == "FILE_BROWSER":
                return len(app.files)
            if app.state == "SETTINGS_MENU":
                return len(app.get_settings_items())
            if app.state == "BT_DEVICES":
                return len(app.bt_devices)
            return 0

        def browse_photo(delta):
            """Листать фото в текущей папке, пропуская не-фото файлы.
            Listovat fotky v aktuální složce, přeskakovat soubory, které nejsou fotky."""
            if not app.files:
                return False

            total = len(app.files)
            idx = app.selected_idx
            for _ in range(total):
                idx = (idx + delta) % total
                if get_file_type(app.files[idx]) == 'photo':
                    app.selected_idx = idx
                    app.view_photo()
                    return True
            return False

        # ===== КНОПКА UP =====
        # ===== TLAČÍTKO UP =====
        if btn == 'UP':
            if app.state == "PLAYING" and not app.video_frame:
                # Во время проигрывания МУЗЫКИ - увеличиваем громкость
                # Během přehrávání HUDBY - zvyšujeme hlasitost
                app.volume = min(100, app.volume + 10)
                app.volume_display_time = time.time()  # Показать полосу громкости
                                                       # Zobrazit pruh hlasitosti
                print(f"Volume: {app.volume}%")
                # Перезапустить с новой громкостью
                # Restartovat s novou hlasitostí
                app.play_media()
            elif app.state == "VIEWING":
                if app.current_image is not None:
                    browse_photo(-1)
                else:
                    # Во время просмотра видео оставляем управление громкостью
                    # Během přehrávání videa ponecháváme ovládání hlasitosti
                    app.volume = min(100, app.volume + 10)
                    app.volume_display_time = time.time()
                    print(f"Volume: {app.volume}%")
            else:
                # В других режимах - листаем вверх
                # V ostatních režimech - listujeme nahoru
                app.selected_idx = max(0, app.selected_idx - 1)

        # ===== КНОПКА DOWN =====
        # ===== TLAČÍTKO DOWN =====
        elif btn == 'DOWN':
            if app.state == "PLAYING" and not app.video_frame:
                # Во время проигрывания МУЗЫКИ - уменьшаем громкость
                # Během přehrávání HUDBY - snižujeme hlasitost
                app.volume = max(0, app.volume - 10)
                app.volume_display_time = time.time()  # Показать полосу громкости
                                                       # Zobrazit pruh hlasitosti
                print(f"Volume: {app.volume}%")
                # Перезапустить с новой громкостью
                # Restartovat s novou hlasitostí
                app.play_media()
            elif app.state == "VIEWING":
                if app.current_image is not None:
                    browse_photo(1)
                else:
                    # Во время просмотра видео оставляем управление громкостью
                    # Během přehrávání videa ponecháváme ovládání hlasitosti
                    app.volume = max(0, app.volume - 10)
                    app.volume_display_time = time.time()
                    print(f"Volume: {app.volume}%")
            else:
                # В других режимах - листаем вниз
                # V ostatních režimech - listujeme dolů
                limit = current_list_limit()
                if limit > 0:
                    app.selected_idx = min(limit - 1, app.selected_idx + 1)

        # ===== КНОПКА BACK =====
        # ===== TLAČÍTKO BACK =====
        elif btn == 'BACK':
            if app.state == "VIEWING":
                app.stop_media()
                app.current_image = None
                app.state = "FILE_BROWSER"
            elif app.state == "FILE_BROWSER":
                app.state = "MAIN_MENU"
                app.selected_idx = 0
            elif app.state == "BT_DEVICES":
                app.state = "SETTINGS_MENU"
                app.selected_idx = 0
            elif app.state == "SETTINGS_MENU":
                app.state = "MAIN_MENU"
                app.selected_idx = 0
            elif app.state == "PLAYING":
                app.stop_media()
                app.state = "FILE_BROWSER"
            elif app.state == "BT_MENU":
                app.state = "MAIN_MENU"

        # ===== КНОПКА SELECT =====
        # ===== TLAČÍTKO SELECT =====
        elif btn == 'SELECT':
            # _____ В главном меню _____
            # _____ V hlavním menu _____
            if app.state == "MAIN_MENU":
                choice = FOLDERS[app.selected_idx]

                if choice == "Settings":
                    app.state = "SETTINGS_MENU"
                    app.selected_idx = 0
                else:
                    app.current_folder = choice
                    app.files = app.get_files(choice)
                    app.selected_idx = 0
                    app.state = "FILE_BROWSER"

            elif app.state == "SETTINGS_MENU":
                settings_idx = app.selected_idx

                if settings_idx == 0:
                    next_mode = "bluetooth" if app.audio_output_mode == "jack" else "jack"
                    app.apply_audio_output(next_mode)
                elif settings_idx == 1:
                    app.scan_bluetooth_devices()
                    app.state = "BT_DEVICES"
                    app.selected_idx = 0
                elif settings_idx == 2:
                    app.disconnect_bt_device()

            elif app.state == "BT_DEVICES":
                if app.bt_devices:
                    device = app.bt_devices[app.selected_idx]
                    app.connect_bt_device(device["mac"])
                    app.state = "SETTINGS_MENU"
                    app.selected_idx = 0

            elif app.state == "VIEWING":
                # Для видео в режиме просмотра SELECT = пауза/продолжить.
                if app.current_image is None and app.is_playing:
                    app.toggle_pause()

            # _____ В браузере файлов _____
            # _____ V prohlížeči souborů _____
            elif app.state == "FILE_BROWSER":
                if app.files:
                    file_name = app.files[app.selected_idx]
                    file_type = get_file_type(file_name)

                    if file_type == 'photo':
                        app.view_photo()
                    elif file_type == 'video':
                        app.view_video()
                        app.state = "VIEWING"  # Переходим в режим просмотра
                                               # Přecházíme do režimu prohlížení
                    else:  # music и другие
                        app.play_media()

            # _____ Во время воспроизведения _____
            # _____ Během přehrávání _____
            elif app.state == "PLAYING":
                app.toggle_pause()
