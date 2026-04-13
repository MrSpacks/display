"""
PlayerOS - Media Player for Raspberry Pi with ST7789 LCD Display

Provides a fully-featured media player with:
- Music playback via ffplay
- Video playback with full-screen display
- Photo viewing
- Volume control (0-100%)
- Bluetooth device support
- 4-button interface (UP, DOWN, SELECT, BACK)
"""

__version__ = "1.0.0"
__author__ = "PlayerOS Developer"

from .core_player import PlayerOS

# Display и InputHandler импортируются только в main.py чтобы избежать зависимостей

__all__ = [
    'PlayerOS',
]
