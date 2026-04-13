"""
Утилиты для работы с медиафайлами
"""

import os
import subprocess
from ..config import BASE_PATH


def get_files(folder):
    """
    Получить список файлов в указанной папке (устаревшая функция, оставлена для совместимости)
    
    Args:
        folder (str): Имя папки (Music, Video, Photo)
        
    Returns:
        list: Список имён элементов (файлы и папки), исключая скрытые
    """
    path = os.path.join(BASE_PATH, folder.lower())
    if not os.path.exists(path):
        return []
    return [f for f in os.listdir(path) if not f.startswith('.')]


def get_folder_contents(base_path, rel_path=""):
    """
    Получить список файлов и папок (с метаданными)
    
    Args:
        base_path (str): Корневая папка (например, ~/display/media/Music)
        rel_path (str): Путь относительно base_path (для подпапок)
        
    Returns:
        list: Список кортежей (name, is_dir)
    """
    full_path = os.path.join(base_path, rel_path) if rel_path else base_path
    if not os.path.isdir(full_path):
        return []
    
    items = []
    try:
        for f in sorted(os.listdir(full_path)):
            if f.startswith('.'):
                continue
            full_item_path = os.path.join(full_path, f)
            is_dir = os.path.isdir(full_item_path)
            items.append((f, is_dir))
    except (OSError, PermissionError):
        pass
    
    return items


def is_item_directory(base_path, name, rel_path=""):
    """
    Проверить, является ли элемент папкой
    
    Args:
        base_path (str): Корневая папка
        name (str): Имя элемента
        rel_path (str): Относительный путь
        
    Returns:
        bool: True если папка, False если файл
    """
    full_path = os.path.join(base_path, rel_path) if rel_path else base_path
    item_path = os.path.join(full_path, name)
    return os.path.isdir(item_path)


def get_file_type(filename):
    """
    Определить тип файла по расширению
    
    Args:
        filename (str): Имя файла
        
    Returns:
        str: Тип файла ('photo', 'video', 'music', 'unknown')
    """
    filename_lower = filename.lower()
    
    if filename_lower.endswith(('.jpg', '.jpeg', '.png', '.bmp', '.gif')):
        return 'photo'
    elif filename_lower.endswith(('.mp4', '.avi', '.mkv', '.mov', '.flv')):
        return 'video'
    elif filename_lower.endswith(('.mp3', '.wav', '.aac', '.flac', '.ogg', '.m4a')):
        return 'music'
    else:
        return 'unknown'


def get_file_icon(filename, is_directory=False):
    """
    Получить иконку для файла или папки на основе типа
    
    Args:
        filename (str): Имя файла/папки
        is_directory (bool): True если это папка
        
    Returns:
        str: Иконка для отображения (символ)
    """
    if is_directory:
        return '📁'  # Папка
    
    file_type = get_file_type(filename)
    
    if file_type == 'photo':
        return '◆'  # Алмаз для фото
    elif file_type == 'video':
        return '▶'  # Треугольник для видео
    elif file_type == 'music':
        return '♪'  # Нота для музыки
    else:
        return '●'  # Точка для неизвестных файлов


def compute_progress_fill_rect(bar_x, bar_y, bar_width, bar_height, progress_percent, padding=2):
    """Вернуть корректный прямоугольник заливки прогресс-бара или None."""
    percent = max(0.0, min(100.0, float(progress_percent)))

    inner_left = bar_x + padding
    inner_top = bar_y + padding
    inner_right = bar_x + bar_width - padding
    inner_bottom = bar_y + bar_height - padding
    if inner_right < inner_left or inner_bottom < inner_top:
        return None

    inner_width = inner_right - inner_left
    filled = int((percent / 100.0) * inner_width)
    if filled <= 0:
        return None

    x2 = min(inner_right, inner_left + filled)
    if x2 < inner_left:
        return None

    return [inner_left, inner_top, x2, inner_bottom]


def stop_ffplay(process):
    """
    Остановить процесс ffplay
    
    Args:
        process: Процесс ffplay для остановки
    """
    if process:
        try:
            process.terminate()
        except:
            pass
    return None


if __name__ == "__main__":
    print("Utilities module for PlayerOS")
