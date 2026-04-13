"""
Утилиты для работы с медиафайлами
Nástroje pro práci s mediálními soubory
"""

import os
import subprocess
from ..config import BASE_PATH


def get_files(folder):
    """
    Получить список файлов в указанной папке
    Získat seznam souborů ve zadané složce
    
    Args:
        folder (str): Имя папки (Music, Video, Photo)
        
    Returns:
        list: Список имён файлов (исключая скрытые файлы)
    """
    path = os.path.join(BASE_PATH, folder.lower())
    if not os.path.exists(path):
        return []
    return [f for f in os.listdir(path) if not f.startswith('.')]


def get_file_type(filename):
    """
    Определить тип файла по расширению
    Určit typ souboru podle přípony
    
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


def get_file_icon(filename):
    """
    Получить иконку для файла на основе типа
    Získat ikonu pro soubor podle typu
    
    Args:
        filename (str): Имя файла
        
    Returns:
        str: Иконка для отображения (символ)
    """
    file_type = get_file_type(filename)
    
    if file_type == 'photo':
        return '◆'  # Алмаз для фото
                    # Diamant pro fotky
    elif file_type == 'video':
        return '▶'  # Треугольник для видео
                    # Trojúhelník pro video
    elif file_type == 'music':
        return '♪'  # Нота для музыки
                    # Nota pro hudbu
    else:
        return '●'  # Точка для неизвестных файлов
                    # Tečka pro neznámé soubory


def stop_ffplay(process):
    """
    Остановить процесс ffplay
    Zastavit proces ffplay
    
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
