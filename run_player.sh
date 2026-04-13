#!/bin/bash
# Запуск PlayerOS Media Player с Raspberry Pi

echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║   PlayerOS Media Player - Startup Script    ║"
echo "║         Raspberry Pi with ST7789 LCD        ║"
echo "╚══════════════════════════════════════════════╝"
echo ""

# Проверяем, запущено ли с sudo
if [[ $EUID -ne 0 ]]; then
   echo "→ Requesting administrator privileges (sudo)..."
   echo ""
   sudo "$0" "$@"
   exit $?
fi

# Всегда работаем из корня проекта.
cd "$(dirname "$0")"

echo "✓ Running with sudo privileges"
echo ""

# Активируем виртуальное окружение
if [ ! -f "venv/bin/activate" ]; then
    echo "✗ ERROR: Virtual environment not found at: venv/bin/activate"
    echo "  Run: python3 -m venv venv"
    exit 1
fi

echo "→ Activating Python virtual environment..."
source venv/bin/activate

if [ $? -ne 0 ]; then
    echo "✗ Failed to activate virtual environment"
    exit 1
fi

echo "✓ Virtual environment activated"
echo ""

# Проверяем наличие необходимых модулей
echo "→ Checking dependencies..."
python3 -c "import luma.lcd; import PIL; import RPi.GPIO" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "✗ Missing dependencies. Install with:"
    echo "  pip install -r requirements_player_os.txt"
    exit 1
fi
echo "✓ All dependencies OK"
echo ""

# Проверяем наличие ffmpeg
if ! command -v ffmpeg &> /dev/null; then
    echo "✗ ERROR: ffmpeg not found. Install with:"
    echo "  sudo apt-get install ffmpeg"
    exit 1
fi
echo "✓ ffmpeg available"
echo ""

echo "═" | awk '{for(i=0;i<46;i++)printf "═"; print ""}'
echo "Starting PlayerOS application..."
echo "Press Ctrl+C to exit"
echo "═" | awk '{for(i=0;i<46;i++)printf "═"; print ""}'
echo ""

# Запускаем приложение
python3 -m player_os_app.main

# Код возврата приложения
EXIT_CODE=$?

echo ""
echo "═" | awk '{for(i=0;i<46;i++)printf "═"; print ""}'
if [ $EXIT_CODE -eq 0 ]; then
    echo "✓ PlayerOS has shut down normally"
else
    echo "✗ PlayerOS exited with code: $EXIT_CODE"
fi
echo ""
