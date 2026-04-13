#!/usr/bin/env python3
"""Тесты для прогресса воспроизведения и форматирования времени."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import player_os_app.core_player as core_player_module
from player_os_app.core_player import PlayerOS
from player_os_app.utils import compute_progress_fill_rect


def test_format_playback_time_short():
    assert PlayerOS.format_playback_time(0) == "0:00"
    assert PlayerOS.format_playback_time(65) == "1:05"
    assert PlayerOS.format_playback_time(3599) == "59:59"


def test_format_playback_time_long():
    # 7947 секунд = 2:12:27
    assert PlayerOS.format_playback_time(7947.9) == "2:12:27"


def test_compute_progress_fill_rect_zero_percent():
    rect = compute_progress_fill_rect(20, 130, 280, 8, 0)
    assert rect is None


def test_compute_progress_fill_rect_small_percent_is_valid():
    rect = compute_progress_fill_rect(20, 130, 280, 8, 0.2)
    assert rect is None or rect[2] >= rect[0]


def test_compute_progress_fill_rect_bounds():
    rect = compute_progress_fill_rect(20, 130, 280, 8, 100)
    assert rect is not None
    assert rect[2] >= rect[0]


def test_seek_media_does_not_reset_when_duration_unknown():
    app = PlayerOS.__new__(PlayerOS)
    app.current_track_duration = 0
    app.volume = 80
    app.ffplay_process = None
    app.audio_process = None
    app.is_playing = True
    app.is_paused = False
    app.media_seek_offset = 0
    app.playback_start_time = 0
    app.stop_video_reader = False
    app.video_reader_thread = None
    app.video_frame = None
    app.files = ["song.mp3"]
    app.selected_idx = 0
    app.current_folder = "Music"
    app.current_path = ""

    captured = {"cmd": None}

    class DummyProc:
        def poll(self):
            return None

    def fake_popen(cmd, stdout=None, stderr=None):
        captured["cmd"] = cmd
        return DummyProc()

    original_popen = core_player_module.subprocess.Popen
    core_player_module.subprocess.Popen = fake_popen
    try:
        app.seek_media(42)
    finally:
        core_player_module.subprocess.Popen = original_popen

    assert captured["cmd"] is not None
    assert "-ss" in captured["cmd"]
    assert captured["cmd"][captured["cmd"].index("-ss") + 1] == "42"
    assert app.media_seek_offset == 42


def test_get_media_duration_fallback_from_ffmpeg_duration_line():
    app = PlayerOS.__new__(PlayerOS)

    class FakeResult:
        def __init__(self, returncode=0, stdout="", stderr=""):
            self.returncode = returncode
            self.stdout = stdout
            self.stderr = stderr

    calls = {"n": 0}

    def fake_run(cmd, capture_output=False, text=False, timeout=None):
        calls["n"] += 1
        # 2 попытки ffprobe без результата
        if calls["n"] in (1, 2):
            return FakeResult(returncode=1, stdout="", stderr="N/A")
        # fallback ffmpeg -i
        return FakeResult(returncode=1, stdout="", stderr="Duration: 00:02:03.50, start: 0.000000")

    original_run = core_player_module.subprocess.run
    core_player_module.subprocess.run = fake_run
    try:
        duration = app.get_media_duration("dummy.mp3")
    finally:
        core_player_module.subprocess.run = original_run

    assert abs(duration - 123.5) < 0.001


def test_play_next_skips_directories():
    """Проверить что play_next() пропускает папки и находит следующий трек."""
    app = PlayerOS.__new__(PlayerOS)
    app.files = ["song1.mp3", "folder", "song2.mp3"]
    app.selected_idx = 0
    app.current_folder = "Music"
    app.current_path = ""
    app.state = "PLAYING"
    app.is_playing = True
    app.volume = 80
    app.ffplay_process = None
    app.audio_process = None
    app.is_paused = False
    app.stop_video_reader = False
    app.video_reader_thread = None
    app.video_frame = None
    app.current_image = None

    called = {"times": 0}
    def fake_play_media():
        called["times"] += 1
    app.play_media = fake_play_media

    def fake_is_directory(name, folder, path):
        return name == "folder"
    app.is_directory = fake_is_directory

    app.play_next()
    assert app.selected_idx == 2
    assert called["times"] == 1


def test_play_next_cycles_to_start():
    """Проверить что play_next() циклит с начала по достижении конца."""
    app = PlayerOS.__new__(PlayerOS)
    app.files = ["song1.mp3", "song2.mp3"]
    app.selected_idx = 1
    app.current_folder = "Music"
    app.current_path = ""
    app.state = "PLAYING"
    app.is_playing = True
    app.volume = 80
    app.ffplay_process = None
    app.audio_process = None
    app.is_paused = False
    app.stop_video_reader = False
    app.video_reader_thread = None
    app.video_frame = None
    app.current_image = None

    called = {"times": 0}
    def fake_play_media():
        called["times"] += 1
    app.play_media = fake_play_media

    def fake_is_directory(name, folder, path):
        return False
    app.is_directory = fake_is_directory

    app.play_next()
    assert app.selected_idx == 0
    assert called["times"] == 1


if __name__ == "__main__":
    test_format_playback_time_short()
    test_format_playback_time_long()
    test_compute_progress_fill_rect_zero_percent()
    test_compute_progress_fill_rect_small_percent_is_valid()
    test_compute_progress_fill_rect_bounds()
    test_seek_media_does_not_reset_when_duration_unknown()
    test_get_media_duration_fallback_from_ffmpeg_duration_line()
    test_play_next_skips_directories()
    test_play_next_cycles_to_start()
    print("✓ playback feature tests passed")
