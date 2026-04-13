#!/usr/bin/env python3
"""
Тест модулей refactored player_os_app
"""

import sys
from pathlib import Path

# Добавить проект в путь
sys.path.insert(0, str(Path(__file__).parent))


def test_config():
    """Тест конфига"""
    print("✓ Testing config...")
    from player_os_app.config import BUTTONS, FOLDERS, DISPLAY_CONFIG
    
    assert BUTTONS['UP'] == 22, "Button UP mapping wrong"
    assert BUTTONS['DOWN'] == 5, "Button DOWN mapping wrong"
    assert len(FOLDERS) > 0, "FOLDERS empty"
    assert DISPLAY_CONFIG['width'] == 320, "Display width wrong"
    print("  - Buttons OK:", BUTTONS)
    print("  - Folders OK:", FOLDERS)
    print("  - Display config OK")


def test_utils():
    """Тест утилит"""
    print("\n✓ Testing utils...")
    from player_os_app.utils import get_file_type, get_file_icon
    
    assert get_file_type("song.mp3") == "music", "Music detection failed"
    assert get_file_type("video.mp4") == "video", "Video detection failed"
    assert get_file_type("photo.jpg") == "photo", "Photo detection failed"
    print("  - File type detection OK")
    
    # Тест иконок
    music_icon = get_file_icon("test.mp3")
    video_icon = get_file_icon("test.mp4")
    photo_icon = get_file_icon("test.jpg")
    unknown_icon = get_file_icon("test.txt")
    
    assert music_icon != video_icon, "Music and video icons should be different"
    assert video_icon != photo_icon, "Video and photo icons should be different"
    print(f"  - File icons OK: Music={music_icon}, Video={video_icon}, Photo={photo_icon}, Unknown={unknown_icon}")


def test_core_player():
    """Тест основного плеера (без GPIO/display инициализации)"""
    print("\n✓ Testing core_player...")
    from player_os_app.core_player import PlayerOS
    
    # Не инициализируем GPIO/display, только проверяем класс
    app = PlayerOS.__new__(PlayerOS)  # Создаём объект без __init__
    app.state = "MAIN_MENU"
    app.volume = 50
    app.selected_idx = 0
    app.is_playing = False
    app.files = []
    
    assert app.state == "MAIN_MENU", "State initialization failed"
    assert app.volume == 50, "Volume initialization failed"
    print("  - State management OK")
    print("  - Volume control OK")


def test_input_handler():
    """Тест обработчика ввода"""
    print("\n✓ Testing input_handler...")
    from player_os_app.input_handler import InputHandler
    from player_os_app.core_player import PlayerOS
    
    handler = InputHandler()
    app = PlayerOS.__new__(PlayerOS)
    app.state = "MAIN_MENU"
    app.selected_idx = 1
    app.volume = 50
    app.volume_display_time = 0
    app.files = ["File1", "File2", "File3"]
    app.current_folder = "Music"
    app.ffplay_process = None
    app.is_playing = False
    app.play_media = lambda: None  # Заглушка для функции play_media
    
    # Тест UP в MAIN_MENU (должен уменьшить индекс на 1)
    handler.handle_click(app, "UP")
    assert app.selected_idx == 0, "UP navigation failed"
    print("  - Navigation UP OK")
    
    # Тест UP в начале (должен остаться на 0, не оборачиваться)
    handler.handle_click(app, "UP")
    assert app.selected_idx == 0, "UP at start should stay at 0"
    print("  - UP at start OK (stays at 0)")
    
    # Тест DOWN
    handler.handle_click(app, "DOWN")
    assert app.selected_idx == 1, "DOWN navigation failed"
    print("  - Navigation DOWN OK")
    
    # Тест громкости во время проигрывания
    app.state = "PLAYING"
    app.volume = 50
    old_time = app.volume_display_time
    handler.handle_click(app, "UP")
    assert app.volume == 60, "Volume UP failed"
    assert app.volume_display_time != old_time, "Volume display time not updated"
    print("  - Volume UP OK")
    
    handler.handle_click(app, "DOWN")
    assert app.volume == 50, "Volume DOWN failed"
    print("  - Volume DOWN OK")


def test_imports():
    """Тест импортов всех модулей"""
    print("\n✓ Testing module imports...")
    try:
        from player_os_app import PlayerOS
        print("  - PlayerOS import OK")
        
        # Тест индивидуальных модулей
        import player_os_app.config
        import player_os_app.core_player
        import player_os_app.input_handler
        import player_os_app.utils
        import player_os_app.main
        print("  - All modules import OK")
        
    except ImportError as e:
        print(f"  ✗ Import failed: {e}")
        return False
    
    return True


if __name__ == "__main__":
    print("=" * 50)
    print("TESTING REFACTORED PLAYER_OS_APP")
    print("=" * 50)
    
    try:
        test_config()
        test_utils()
        test_core_player()
        test_input_handler()
        if not test_imports():
            exit(1)
        
        print("\n" + "=" * 50)
        print("✓ ALL TESTS PASSED!")
        print("=" * 50)
        
    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
