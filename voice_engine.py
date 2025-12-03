import os
import re
from dataclasses import dataclass
from typing import Literal, Optional, Dict, Any

Domain = Literal["robot", "pc", "ai", "system"]

@dataclass
class ParsedCommand:
    domain: Domain
    action: str
    params: Dict[str, Any]


# USER BASE PATH (Modify if needed)
USER_BASE = r"C:\Users\Bhanu\OneDrive"

def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


# --------------------------
# DIRECTORY MAPS
# --------------------------
SPECIAL_DIRS = {
    "desktop": USER_BASE + r"\Desktop",
    "documents": USER_BASE + r"\Documents",
    "downloads": USER_BASE + r"\Downloads",
    "pictures": USER_BASE + r"\Pictures",
    "videos": USER_BASE + r"\Videos",
    "music": USER_BASE + r"\Music",
}


# --------------------------
# MATCH DIRECTORY COMMANDS
# --------------------------
def _match_cd(text: str) -> Optional[ParsedCommand]:

    # KEY PHRASES
    triggers = [
        "change directory to ",
        "cd to ",
        "go to ",
        "open folder ",
        "open directory "
    ]

    for trig in triggers:
        if text.startswith(trig):
            folder = text.replace(trig, "").strip()

            # Check if it is a special directory
            if folder in SPECIAL_DIRS:
                path = SPECIAL_DIRS[folder]
                return ParsedCommand("pc", "command", {"command": f'cd "{path}"'})

            # Otherwise treat as subfolder inside Desktop
            path = USER_BASE + r"\Desktop" + "\\" + folder
            return ParsedCommand("pc", "command", {"command": f'cd "{path}"'})

    return None


# --------------------------
# PC COMMAND MAPPER
# --------------------------
def _map_pc_command(text: str) -> str:
    t = text.lower().strip()

    # YouTube voice command: "play <song>"
    if t.startswith("play "):
        song = t.replace("play ", "").strip()
        query = song.replace(" ", "+")
        return f'start chrome "https://www.youtube.com/results?search_query={query}"'

    mapping = {
        "open chrome": "start chrome",
        "open firefox": "start firefox",
        "open notepad": "start notepad",
        "open calculator": "start calc",
        "open paint": "start mspaint",
    }

    for key, value in mapping.items():
        if key in t:
            return value

    if t.startswith("open "):
        app = t.replace("open ", "").strip()
        return f"start {app}"

    return text

def _match_run(text: str) -> Optional[ParsedCommand]:
    """
    Detect commands like:
    - run hello
    - run hello.py
    - execute hello
    """

    if text.startswith("run ") or text.startswith("execute "):
        file = text.replace("run ", "").replace("execute ", "").strip()

        # Ensure .py extension
        if not file.endswith(".py"):
            file = file + ".py"

        cmd = f"python {file}"
        return ParsedCommand("pc", "command", {"command": cmd})

    return None


def _match_pc(text: str) -> Optional[ParsedCommand]:

    if text.startswith("play "):
        song = text.replace("play ", "").strip()
        return ParsedCommand("pc", "command", {"command": f"play {song}"})

    if any(kw in text for kw in ["open ", "start ", "launch "]):
        cmd = _map_pc_command(text)
        return ParsedCommand("pc", "command", {"command": cmd})

    return None


def _match_robot(text: str):
    return None


def _match_system(text: str):
    return None


# --------------------------
# FINAL PARSER
# --------------------------
def parse_command(text: str) -> ParsedCommand:
    norm = _normalize(text)

    # ORDER IMPORTANT
    # 1) System
    # 2) DIRECTORY
    # 3) PC
    # 4) Robot
    for matcher in (_match_system, _match_cd, _match_run, _match_pc, _match_robot):
        result = matcher(norm)
        if result:
            return result

    return ParsedCommand("ai", "chat", {"text": text.strip()})
