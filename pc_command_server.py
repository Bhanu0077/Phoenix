"""
PC Command Server - Run this on the target PC to receive commands
This server listens for commands from the Phoenix AI system and executes them.
"""

from flask import Flask, request, jsonify
import subprocess
import os
import sys
import win32con
import win32process

app = Flask(__name__)
PORT = int(os.getenv("PHOENIX_PC_PORT", "5001"))
SHARED_TOKEN = os.getenv("PHOENIX_PC_SHARED_TOKEN", "").strip()
ALLOWED_CONTROLLER_IP = os.getenv("PHOENIX_CONTROLLER_IP", "").strip()
persistent_cmd = subprocess.Popen(
    ["cmd.exe"],
    creationflags=subprocess.CREATE_NEW_CONSOLE,
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    shell=True
)


# ============================================================
# 🔥 YOUTUBE COMMAND MAPPER
# ============================================================
def map_youtube_command(cmd: str):
    cmd = cmd.lower().strip()

    # Detect: "play <song name>"
    if cmd.startswith("play "):
        song = cmd.replace("play ", "").strip()
        query = song.replace(" ", "+")
        chrome_cmd = f'start chrome "https://www.youtube.com/results?search_query={query}"'
        print(f"[MAPPER] YouTube command mapped to: {chrome_cmd}")
        return chrome_cmd

    # Any command not starting with "play" returns unchanged
    return cmd


@app.route('/execute_command', methods=['POST'])
def execute_command():
    """
    Execute a command received from Phoenix AI using a persistent CMD session.
    """

    try:
        # Optional IP allow-list
        if ALLOWED_CONTROLLER_IP and request.remote_addr != ALLOWED_CONTROLLER_IP:
            return jsonify({"success": False, "error": "Unauthorized controller IP"}), 403

        # Optional shared secret token
        if SHARED_TOKEN:
            token = request.headers.get("X-Phoenix-Token", "").strip()
            if token != SHARED_TOKEN:
                return jsonify({"success": False, "error": "Invalid or missing security token"}), 403

        data = request.json
        command = data.get("command", "").strip()

        if not command:
            return jsonify({"success": False, "error": "No command provided"}), 400

        print(f"[INFO] Received command: {command}")

        # ============================================================
        # 🔥 APPLY YOUTUBE MAPPING
        # ============================================================
        final_cmd = map_youtube_command(command)
        print(f"[INFO] Final command to execute: {final_cmd}")

        # ============================================================
        # 🔥 SEND COMMAND TO PERSISTENT CMD SESSION
        # ============================================================
        try:
            persistent_cmd.stdin.write(final_cmd + "\n")
            persistent_cmd.stdin.flush()
            output = ""
            try:
                output = persistent_cmd.stdout.readline().strip()
            except:
                output = ""

            return jsonify({
                "success": True,
                "output": output,
                "message": "Command executed"
            })
        except Exception as e:
            print(f"[ERROR] Could not write to persistent CMD: {e}")
            return jsonify({"success": False, "error": "Failed to execute command"}), 500


    except Exception as e:
        print(f"[ERROR] Exception: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500



@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "online", "message": "PC Command Server is running"})


if __name__ == '__main__':
    print(f"""
    ╔══════════════════════════════════════════════════════╗
    ║     Phoenix AI - PC Command Server                   ║
    ║     Listening on port {PORT}                           ║
    ║                                                      ║
    ║     Make sure your firewall allows connections       ║
    ║     on port {PORT}                                     ║
    ╚══════════════════════════════════════════════════════╝
    """)

    # Display local IP
    import socket
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    print(f"Local IP Address: {local_ip}")
    print(f"Use this IP in the Phoenix AI interface\n")

    try:
        app.run(host='0.0.0.0', port=PORT, debug=False)
    except PermissionError:
        print(f"\n[ERROR] Permission denied. Port {PORT} may be in use or requires admin privileges.")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Failed to start server: {e}")
        sys.exit(1)
