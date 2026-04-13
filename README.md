# PlayerOS

PlayerOS is a Raspberry Pi media player for a 320x240 ST7789 display with four hardware buttons.

The current repository is intentionally reduced to the files that are actually needed to run and maintain the project:

- Python application in player_os_app
- systemd service in playerpi.service
- startup script in run_player.sh
- dependency list in requirements_player_os.txt
- smoke test in test_refactored.py

## Features

- Music playback with ffplay
- Video playback on the ST7789 display
- Photo viewing
- Volume control from hardware buttons
- Bluetooth device scan, connect, disconnect, and audio output switching
- systemd-friendly launch flow

## Project Layout

```text
player_os_app/
  __init__.py
  config.py
  core_player.py
  display.py
  input_handler.py
  main.py
  utils/
requirements_player_os.txt
run_player.sh
playerpi.service
test_refactored.py
README.md
```

## Hardware

- Raspberry Pi with GPIO access
- ST7789 SPI display, 320x240
- 4 buttons connected to GND
- Optional Bluetooth audio device

Default button mapping:

```python
BUTTONS = {
    'UP': 22,
    'DOWN': 5,
    'SELECT': 17,
    'BACK': 27,
}
```

## Installation

### 1. System packages

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip ffmpeg python3-rpi.gpio
```

### 2. Python environment

```bash
cd /home/spacks/display
python3 -m venv venv
source venv/bin/activate
pip install -r requirements_player_os.txt
```

### 3. Media folders

The application reads media from:

```text
media/music
media/video
media/photo
```

Create them if needed:

```bash
mkdir -p media/music media/video media/photo
```

## Run

Direct launch:

```bash
cd /home/spacks/display
source venv/bin/activate
sudo python3 -m player_os_app.main
```

Or use the helper script:

```bash
cd /home/spacks/display
./run_player.sh
```

## Controls

| Button | Action |
| --- | --- |
| UP | Move up, increase volume, previous photo |
| DOWN | Move down, decrease volume, next photo |
| SELECT | Open, play, pause, confirm |
| BACK | Back, stop playback |

## Service Setup

Install the service:

```bash
sudo cp playerpi.service /etc/systemd/system/playerpi.service
sudo systemctl daemon-reload
sudo systemctl enable playerpi.service
sudo systemctl start playerpi.service
```

Useful commands:

```bash
sudo systemctl status playerpi.service
sudo systemctl restart playerpi.service
sudo systemctl stop playerpi.service
journalctl -u playerpi.service -f
```

## Testing

Basic smoke test:

```bash
cd /home/spacks/display
source venv/bin/activate
python3 test_refactored.py
```

If you run tests on a non-Raspberry Pi machine, imports that require GPIO or the display stack can fail unless those packages are installed.

## Configuration

Main runtime settings are in player_os_app/config.py:

- GPIO button pins
- ST7789 SPI configuration
- media base path
- fonts
- default volume

The media root is resolved relative to the repository, so the app works more reliably under sudo.

## Troubleshooting

### Display does not initialize

- Verify SPI is enabled
- Check gpio_DC and gpio_RST in player_os_app/config.py
- Run the application with sudo

### luma or Pillow import errors

Make sure you are using the virtual environment that has the project dependencies installed:

```bash
sudo /home/spacks/display/venv/bin/python -m player_os_app.main
```

### No audio or Bluetooth output

- Verify ffmpeg and ffplay are installed
- Check PulseAudio or PipeWire availability for Bluetooth output
- Confirm the target Bluetooth device is paired and connected

## Git Notes

This repository is cleaned up for version control:

- local virtual environment is ignored
- Python cache files are ignored
- media content is ignored
- generated build directories are ignored

## License

No license file is currently included in this repository.