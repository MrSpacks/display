"""
Конфигурация медиаплеера PlayerOS
Konfigurace mediálního přehrávače PlayerOS
"""

import os

# ============================================================================
# НАСТРОЙКИ ОБОРУДОВАНИЯ
# NASTAVENÍ HARDWARU
# ============================================================================

# GPIO пины для кнопок (использует BCM нумерацию)
# GPIO piny pro tlačítka (používá BCM číslování)
# Кнопки подключены через GND - когда нажата, пин становится LOW
# Tlačítka jsou připojena přes GND - při stisknutí se pin stane LOW
BUTTONS = {
    'UP': 22,     # GPIO22 - Листать вверх / Громкость +
                  # GPIO22 - Rolovat nahoru / Hlasitost +
    'DOWN': 5,    # GPIO5  - Листать вниз / Громкость -
                  # GPIO5  - Rolovat dolů / Hlasitost -
    'SELECT': 17, # GPIO17 - Ок / Плей / Пауза
                  # GPIO17 - Ok / Přehrát / Pauza
    'BACK': 27    # GPIO27 - Назад / Стоп
                  # GPIO27 - Zpět / Zastavit
}

# Параметры дисплея ST7789
# Parametry displeje ST7789
DISPLAY_CONFIG = {
    'port': 0,
    'device': 0,
    'gpio_DC': 24,
    'gpio_RST': 25,
    'width': 320,
    'height': 240,
    'rotate': 0,
    # Частота SPI сильно влияет на скорость обновления видео.
    # Frekvence SPI silně ovlivňuje rychlost aktualizace videa.
    # Если экран работает нестабильно, снижайте: 48000000 -> 32000000 -> 24000000.
    # Pokud displej pracuje nestabilně, snižte: 48000000 -> 32000000 -> 24000000.
    'spi_speed_hz': 48000000
}

# ============================================================================
# ПУТИ И ДИРЕКТОРИИ
# CESTY A ADRESÁŘE
# ============================================================================

# Путь к media относительно корня проекта (устойчиво работает и с sudo)
# Cesta k médiu relativně ke kořeni projektu (funguje i se sudo)
BASE_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "media")
)
FOLDERS = ["Music", "Video", "Photo", "Settings"]

# ============================================================================
# ПАРАМЕТРЫ ПРИЛОЖЕНИЯ
# PARAMETRY APLIKACE
# ============================================================================

# Начальная громкость (0-100)
# Výchozí hlasitost (0-100)
DEFAULT_VOLUME = 80

# Параметры отображения уровня громкости
# Parametry zobrazení úrovně hlasitosti
VOLUME_DISPLAY_DURATION = 2.0  # Секунды показа полосы громкости после нажатия кнопки
                               # Sekundy zobrazení pruhu hlasitosti po stisknutí tlačítka

# Шрифты
# Písma
FONTS = {
    'regular': {
        'path': "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        'size': 18
    },
    'bold': {
        'path': "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        'size': 22
    }
}

# ============================================================================
# ПАРАМЕТРЫ ОТОБРАЖЕНИЯ
# PARAMETRY ZOBRAZENÍ
# ============================================================================

# Размеры меню
# Velikosti menu
MENU_ITEM_SPACING = 35  # Расстояние между пунктами меню
                        # Vzdálenost mezi položkami menu
MENU_ITEM_HEIGHT = 30   # Высота пункта меню
                        # Výška položky menu

# Размеры браузера файлов
# Velikosti prohlížeče souborů
FILE_ITEM_SPACING = 30  # Расстояние между файлами
                        # Vzdálenost mezi soubory
FILE_ITEM_HEIGHT = 28   # Высота пункта файла
                        # Výška položky souboru

# Полоса громкости
# Pruh hlasitosti
VOLUME_BAR = {
    'width': 20,
    'height': 150,
    'x': 290,
    'y': 45
}

# Bluetooth MAC адрес (заполнить вручную)
# Bluetooth MAC adresa (vyplnit ručně)
BLUETOOTH_MAC = "XX:XX:XX:XX:XX:XX"
