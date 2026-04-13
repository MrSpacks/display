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

from .config import BUTTONS
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
                    InputHandler.handle_click(app, name)
                
                # Запоминаем текущее состояние для следующей итерации
                app.button_states[name] = current_state
            
            # 3. Проверяем окончание текущего файла
            if app.state == "PLAYING" and app.is_playing:
                if app.ffplay_process and app.ffplay_process.poll() is not None:
                    print("Track ended, playing next...")
                    app.play_next()
            
            # 4. Пауза цикла: в режиме видео держим минимальную задержку.
            time.sleep(0.003 if is_video_viewing else 0.05)
    
    # Обработка прерывания (Ctrl+C)
    except KeyboardInterrupt:
        print("\n\nShutdown signal received")
        if app.ffplay_process:
            app.stop_media()
        GPIO.cleanup()
        print("GPIO cleaned up")
        print("Goodbye!")




if __name__ == "__main__":
    main()
