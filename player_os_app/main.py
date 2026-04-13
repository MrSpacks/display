#!/usr/bin/env python3
"""
PlayerOS - Медиаплеер для Raspberry Pi с LCD дисплеем ST7789
Управление: 4 кнопки (UP, DOWN, SELECT, BACK)
Возможности: Проигрывание музыки, видео, фото через ffplay
"""

import os
import sys
import time

# Добавляем папку проекта в path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import RPi.GPIO as GPIO

from .config import BUTTONS, MAIN_LOOP_SLEEP_VIDEO, MAIN_LOOP_SLEEP_IDLE
from .core_player import PlayerOS


def main():
    """Главная функция приложения"""
    # Импортируем зависимости только в main чтобы избежать проблем при импорте модуля
    try:
        from .display import Display
    except ModuleNotFoundError as e:
        if e.name in ("luma", "luma.core", "luma.lcd"):
            print("\nERROR: Python package 'luma' is not available in the current interpreter.")
            print(f"Current Python: {sys.executable}")
            print("If you installed dependencies into venv, run with venv Python even under sudo:")
            print("  sudo /home/spacks/display/venv/bin/python -m player_os_app.main")
            print("Or install dependencies for this interpreter:")
            print("  python3 -m pip install -r requirements_player_os.txt")
            sys.exit(1)
        raise
    from .input_handler import InputHandler
    
    print("\n" + "="*60)
    print("PlayerOS - Media Player for Raspberry Pi")
    print("="*60)
    print("Initializing hardware...\n")
    
    # ===== ИНИЦИАЛИЗАЦИЯ ДИСПЛЕЯ =====
    print("[1/3] Initializing display...")
    try:
        display = Display()
    except SystemExit:
        # Display уже вывел сообщение об ошибке и вызвал sys.exit()
        raise
    except Exception as e:
        print(f"ERROR: Display initialization failed: {e}")
        print("Make sure you're running with sufficient GPIO permissions (try: sudo python3 -m player_os_app.main)")
        sys.exit(1)
    
    # ===== ИНИЦИАЛИЗАЦИЯ GPIO =====
    print("\n[2/3] Initializing GPIO...")
    try:
        GPIO.setmode(GPIO.BCM)
        print(f"  GPIO mode: BCM")
        
        # Настраиваем пины кнопок как входы с подтягиванием к +3.3V
        for name, pin in BUTTONS.items():
            GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            print(f"  ✓ Button '{name}' on GPIO{pin}")
        
        print("✓ GPIO initialized\n")
        
    except Exception as e:
        print(f"ERROR: GPIO initialization failed: {e}")
        print("Make sure you're running with sufficient GPIO permissions (try: sudo python3 -m player_os_app.main)")
        sys.exit(1)
    
    # ===== СОЗДАНИЕ ЭКЗЕМПЛЯРА ПРИЛОЖЕНИЯ =====
    print("[3/3] Starting application...")
    app = PlayerOS()
    print("✓ Application ready\n")
    
    # ===== ОТСЛЕЖИВАНИЕ НАЖАТИЙ КНОПОК =====
    button_press_times = {name: 0 for name in BUTTONS}  # Время начала нажатия для каждой кнопки
    LONG_PRESS_THRESHOLD = 1.0  # Секунды для определения long-press
    SEEK_OFFSET = 10  # Секунды перемотки при long-press
    
    print("="*60)
    print("Running main loop (press Ctrl+C to stop)...")
    print("="*60 + "\n")
    
    # ===== ГЛАВНЫЙ ЦИКЛ ПРОГРАММЫ =====
    try:
        while True:
            # Во время видео минимизируем системные вызовы, чтобы не просаживать FPS.
            is_video_viewing = app.state == "VIEWING" and app.is_playing and app.video_frame is not None
            if not is_video_viewing:
                app.refresh_bt_connection_status()

            # 1. Отрисовываем текущее состояние на экран
            display.update(app)
            
            # 2. Проверяем каждую кнопку на нажатие
            for name, pin in BUTTONS.items():
                # Читаем текущее состояние GPIO пина
                current_state = GPIO.input(pin) == GPIO.HIGH
                
                # Если кнопка ПЕРЕШЛА в состояние "нажата"
                if app.button_states[name] and not current_state:
                    print(f"Button pressed: {name}")
                    button_press_times[name] = time.time()  # Сохраняем время нажатия
                    # НЕ вызываем handle_click здесь, ждем отпускания кнопки
                
                # Если кнопка ПЕРЕШЛА в состояние "отпущена"
                elif not app.button_states[name] and current_state:
                    print(f"Button released: {name}")
                    press_duration = time.time() - button_press_times[name]
                    
                    # Проверяем был ли это long-press
                    if press_duration >= LONG_PRESS_THRESHOLD:
                        print(f"Long-press detected on {name} ({press_duration:.1f}s)")
                        
                        # Обработка long-press для перемотки во время воспроизведения
                        if app.state == "PLAYING" and app.is_playing:
                            if name == "BACK":
                                # Перемотать назад
                                current_pos = app.get_playback_progress()
                                new_pos = max(0, current_pos - SEEK_OFFSET)
                                print(f"Seeking back: {current_pos:.1f}s -> {new_pos:.1f}s")
                                app.seek_media(new_pos)
                            elif name == "SELECT":
                                # Перемотать вперед
                                current_pos = app.get_playback_progress()
                                if app.current_track_duration and app.current_track_duration > 0:
                                    new_pos = min(app.current_track_duration, current_pos + SEEK_OFFSET)
                                else:
                                    new_pos = current_pos + SEEK_OFFSET
                                print(f"Seeking forward: {current_pos:.1f}s -> {new_pos:.1f}s")
                                app.seek_media(new_pos)
                    else:
                        # Обычное нажатие (short-press)
                        InputHandler.handle_click(app, name)
                
                # Запоминаем текущее состояние для следующей итерации
                app.button_states[name] = current_state
            
            # 3. Проверяем окончание текущего файла
            if app.state == "PLAYING" and app.is_playing:
                if app.ffplay_process and app.ffplay_process.poll() is not None:
                    print(f"Track ended: {app.files[app.selected_idx] if app.files and app.selected_idx < len(app.files) else 'unknown'}")
                    app.play_next()
            
            # 4. Пауза цикла: в режиме видео держим минимальную задержку.
            time.sleep(MAIN_LOOP_SLEEP_VIDEO if is_video_viewing else MAIN_LOOP_SLEEP_IDLE)
    
    # Обработка прерывания (Ctrl+C)
    except KeyboardInterrupt:
        print("\n\nShutdown signal received")
        if app.ffplay_process:
            app.stop_media()
        if hasattr(display, "cleanup"):
            display.cleanup()
        GPIO.cleanup()
        print("GPIO cleaned up")
        print("Goodbye!")




if __name__ == "__main__":
    main()
