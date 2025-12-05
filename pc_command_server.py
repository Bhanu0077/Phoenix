# pc_command_server.py
# Phoenix High-Capability PC Controller (corrected)
# Run this on the Windows PC you want to control.

import os
import sys
import subprocess
import shlex
import time
import webbrowser
import re
from flask import Flask, request, jsonify
import psutil
import pyautogui
import pygetwindow as gw
import requests

# Optional Windows helpers
try:
    import win32gui
    import win32con
except Exception:
    win32gui = None

# Audio control (pycaw)
try:
    from ctypes import POINTER, cast
    from comtypes import CLSCTX_ALL
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
    PYCaw_AVAILABLE = True
except Exception:
    PYCaw_AVAILABLE = False

app = Flask(__name__)
PORT = int(os.getenv("PHOENIX_PC_PORT", "5001"))
SHARED_TOKEN = os.getenv("PHOENIX_PC_SHARED_TOKEN", "").strip()
ALLOWED_CONTROLLER_IP = os.getenv("PHOENIX_CONTROLLER_IP", "").strip()

# Small map of friendly names -> paths (adjust for your machine)
APP_MAP = {
    "chrome": r"C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
    "firefox": r"C:\\Program Files\\Mozilla Firefox\\firefox.exe",
    "edge": r"C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe",
    "notepad": "notepad.exe",
}

# ------------------------
# Helpers
# ------------------------

def unauthorized(msg="Unauthorized"):
    return jsonify({"success": False, "error": msg}), 403


def require_auth(req):
    # optional IP allowlist
    if ALLOWED_CONTROLLER_IP and req.remote_addr != ALLOWED_CONTROLLER_IP:
        return False, f"controller IP {req.remote_addr} not allowed"
    # shared token
    if SHARED_TOKEN:
        token = req.headers.get("X-Phoenix-Token", "").strip()
        if token != SHARED_TOKEN:
            return False, "invalid or missing X-Phoenix-Token header"
    return True, None


def safe_start(cmd):
    try:
        if os.path.exists(cmd):
            os.startfile(cmd)
            return True, f"Started {cmd}"
        subprocess.Popen(shlex.split(cmd), shell=False)
        return True, f"Executed {cmd}"
    except Exception as exc:
        return False, str(exc)


def open_url(url):
    try:
        webbrowser.open(url)
        return True, f"Opened {url}"
    except Exception as exc:
        return False, str(exc)


def kill_process_by_name(name):
    found = []
    for p in psutil.process_iter(["pid", "name", "exe", "cmdline"]):
        try:
            low = (p.info.get('name') or "").lower()
            exe = (p.info.get('exe') or "")
            if name.lower() in low or (exe and name.lower() in exe.lower()):
                p.terminate()
                found.append(p.info)
        except Exception:
            pass
    return found


def activate_window(title_contains=None):
    try:
        if not title_contains:
            return False, "no title provided"
        wins = gw.getWindowsWithTitle(title_contains)
        if not wins:
            # try partial matching across all windows
            allwins = gw.getAllTitles()
            for t in allwins:
                if title_contains.lower() in (t or "").lower():
                    wins = gw.getWindowsWithTitle(t)
                    break
        if wins:
            w = wins[0]
            try:
                w.activate()
            except Exception:
                try:
                    w.minimize(); time.sleep(0.05); w.restore()
                except Exception:
                    pass
            return True, f"Activated window: {w.title}"
        return False, "no window found"
    except Exception as exc:
        return False, str(exc)


def take_screenshot():
    filename = f"Phoenix_Screenshot_{int(time.time())}.png"
    path = os.path.join(os.getcwd(), filename)
    try:
        pyautogui.screenshot(path)
        return True, f"Screenshot saved: {path}"
    except Exception as exc:
        return False, str(exc)


def refresh_browser():
    try:
        pyautogui.hotkey('ctrl', 'r')
        return True, "Page refreshed"
    except Exception as exc:
        return False, str(exc)


# ------------------------
# Volume via pycaw
# ------------------------

def set_system_volume(percent):
    if not PYCaw_AVAILABLE:
        return False, "pycaw/comtypes not installed"
    try:
        percent = int(percent)
        percent = max(0, min(percent, 100))
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume = cast(interface, POINTER(IAudioEndpointVolume))
        volume_level = percent / 100.0
        volume.SetMasterVolumeLevelScalar(volume_level, None)
        return True, f"Volume set to {percent}%"
    except Exception as exc:
        return False, str(exc)


# ------------------------
# Play song (smart) — fetch first video id and open it
# ------------------------

def handle_play_song(raw):
    # raw e.g. "play singari"
    song = raw.lower().replace("play ", "", 1).strip()
    if not song:
        return False, "No song name provided"

    query = song.replace(' ', '+')
    search_url = f"https://www.youtube.com/results?search_query={query}"

    try:
        # Request search page and extract first /watch?v= id
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        r = requests.get(search_url, headers=headers, timeout=6)
        html = r.text
        m = re.search(r"/watch\?v=([A-Za-z0-9_-]{11})", html)
        if m:
            vid = m.group(1)
            watch = f"https://www.youtube.com/watch?v={vid}"
            webbrowser.open(watch)
            return True, f"Playing: {watch}"
        else:
            # fallback: open search results
            webbrowser.open(search_url)
            return True, f"Opened search results for: {song}"
    except Exception as exc:
        return False, f"Failed to search YouTube: {exc}"


# ------------------------
# YouTube controls (keyboard shortcuts)
# ------------------------

def handle_youtube_control(raw):
    # Try to bring YouTube/tab to front first
    activate_window("YouTube")
    activate_window("Chrome")
    activate_window("Edge")
    activate_window("Firefox")

    if 'pause' in raw or 'stop' in raw:
        pyautogui.press('k')
        return True, 'Paused/Stopped video'
    if 'play' in raw or 'resume' in raw:
        pyautogui.press('k')
        return True, 'Play/Resume video'
    if 'forward' in raw or 'skip' in raw or 'next' in raw:
        pyautogui.press('l')
        return True, 'Skipped forward'
    if 'rewind' in raw or 'back' in raw or 'previous' in raw:
        pyautogui.press('j')
        return True, 'Rewinded/Back'
    if 'fullscreen' in raw:
        pyautogui.press('f')
        return True, 'Toggled fullscreen'
    return False, 'Unknown youtube control'


# ------------------------
# Command executor
# ------------------------

def execute_user_command(command: str):
    raw = (command or "").strip()
    if not raw:
        return False, "Empty command"

    low = raw.lower()

    # ------------------------ SCREENSHOT ------------------------
    if "screenshot" in low:
        return take_screenshot()

    # ------------------------ REFRESH ------------------------
    if "refresh" in low or "reload" in low:
        return refresh_browser()

    # ------------------------ VOLUME ------------------------
    if "volume" in low or "sound" in low:
        m = re.search(r"(\d{1,3})", low)
        if m:
            return set_system_volume(m.group(1))

        if "increase volume to" in low:
            num = low.replace("increase volume to", "").strip()
            return set_system_volume(num)

        if "decrease volume to" in low:
            num = low.replace("decrease volume to", "").strip()
            return set_system_volume(num)

        return False, "Say: 'volume 40' or 'increase volume to 50'"

    # ------------------------ PLAY SONG ------------------------
    if low.startswith("play "):
        return handle_play_song(low)

    # ------------------------ YOUTUBE CONTROL ------------------------
    if "youtube" in low or low.startswith(("pause", "rewind", "forward", "skip")):
        return handle_youtube_control(low)

    # ------------------------ SEARCH ------------------------
    if low.startswith("search ") or low.startswith("find "):
        query = low.split(" ", 1)[1]
        return open_url(f"https://www.google.com/search?q={query.replace(' ', '+')}")

    # ------------------------ TYPE ------------------------
    if low.startswith("type "):
        text = raw.split(" ", 1)[1]
        pyautogui.write(text, interval=0.02)
        return True, f"Typed: {text}"

    # ------------------------ OPEN ------------------------
    if low.startswith(("open ", "start ", "launch ")):
        target = raw.split(" ", 1)[1]

        if target.lower() in APP_MAP:
            return safe_start(APP_MAP[target.lower()])

        if target.startswith("http"):
            return open_url(target)

        try:
            os.startfile(target)
            return True, f"Started {target}"
        except:
            return open_url(f"https://www.google.com/search?q={target.replace(' ', '+')}")

    # ------------------------ CLOSE ------------------------
    if low.startswith(("close ", "kill ", "terminate ")):
        target = low.split(" ", 1)[1]
        killed = kill_process_by_name(target)
        if killed:
            return True, f"Closed {target}"
        return False, "Process not found"

    # ------------------------ FALLBACK ------------------------
    ok, msg = safe_start(raw)
    if ok:
        return True, msg

    return open_url(f"https://www.google.com/search?q={low.replace(' ', '+')}")

# ------------------------
# Flask endpoint
# ------------------------
@app.route('/execute_command', methods=['POST'])
def execute_command():
    try:
        ok, err = require_auth(request)
        if not ok:
            return unauthorized(err)
        data = request.get_json(silent=True) or {}
        command = (data.get('command') or '').strip()
        if not command:
            return jsonify({'success': False, 'error': 'No command provided'}), 400
        print(f"[INFO] Received command: {command}")
        result_ok, result_msg = execute_user_command(command)
        status_code = 200 if result_ok else 400
        return jsonify({'success': result_ok, 'output': result_msg}), status_code
    except Exception as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return jsonify({'success': False, 'error': str(exc)}), 500


# ------------------------
# Main
# ------------------------
if __name__ == '__main__':
    print(f"Phoenix PC Command Server starting on port {PORT}")
    if not PYCaw_AVAILABLE:
        print("Warning: pycaw/comtypes not available — volume control will fail until installed")
    try:
        app.run(host='0.0.0.0', port=PORT, debug=False)
    except Exception as e:
        print(f"Failed to start server: {e}")
        sys.exit(1)
