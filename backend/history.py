import os
import json
import time
import subprocess
from typing import List, Dict, Any, Optional
from .downloader import DOWNLOADS_DIR

HISTORY_FILE = os.path.join(DOWNLOADS_DIR, "history.json")

def load_history() -> List[Dict[str, Any]]:
    if not os.path.exists(HISTORY_FILE):
        return []
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def save_history(history: List[Dict[str, Any]]):
    try:
        os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving history: {e}")

def add_to_history(item: Dict[str, Any]):
    history = load_history()
    item_id = item.get("id")
    item_fp = item.get("filepath")
    
    # Remove existing entry if matching id or matching non-empty filepath
    history = [
        h for h in history
        if not (
            (item_id and h.get("id") == item_id) or
            (item_fp and h.get("filepath") and os.path.normpath(h.get("filepath")) == os.path.normpath(item_fp))
        )
    ]
    item["timestamp"] = int(time.time())
    history.insert(0, item)
    # Keep last 100 items
    history = history[:100]
    save_history(history)

def remove_from_history(item_id: str, delete_file: bool = False) -> Dict[str, Any]:
    history = load_history()
    target = None
    remaining = []
    for h in history:
        if h.get("id") == item_id:
            target = h
        else:
            remaining.append(h)
    
    file_deleted = False
    error_msg = None
    if target and delete_file:
        filepath = target.get("filepath")
        if filepath and os.path.exists(filepath):
            try:
                os.remove(filepath)
                file_deleted = True
            except Exception as e:
                error_msg = str(e)
                print(f"Error deleting file {filepath}: {e}")
                
    save_history(remaining)
    return {
        "success": target is not None,
        "found": target is not None,
        "file_deleted": file_deleted,
        "error": error_msg
    }

def clear_all_history(delete_files: bool = False) -> Dict[str, Any]:
    history = load_history()
    deleted_count = 0
    if delete_files:
        for item in history:
            fp = item.get("filepath")
            if fp and os.path.exists(fp):
                try:
                    os.remove(fp)
                    deleted_count += 1
                except Exception as e:
                    print(f"Could not delete {fp}: {e}")
    save_history([])
    return {"success": True, "files_deleted": deleted_count}

def open_file_in_explorer(filepath: str) -> bool:
    """Opens Windows Explorer with the specified file selected, or opens folder."""
    try:
        downloads_dir = DOWNLOADS_DIR
        if filepath and os.path.exists(filepath):
            norm_path = os.path.normpath(os.path.abspath(filepath))
            if os.name == 'nt':
                # Critical: Windows Explorer requires exact string explorer.exe /select,"C:\path\to\file"
                # Do NOT use a python list with separate arguments because list2cmdline inserts a space after the comma.
                clean_path = norm_path.replace('"', '')
                subprocess.Popen(f'explorer.exe /select,"{clean_path}"')
                return True
            elif hasattr(os, 'uname') and os.uname().sysname == 'Darwin':
                subprocess.Popen(['open', '-R', norm_path])
                return True
            else:
                subprocess.Popen(['xdg-open', os.path.dirname(norm_path)])
                return True
        else:
            # File might have been renamed or moved; open downloads folder
            return open_downloads_folder(downloads_dir)
    except Exception as e:
        print(f"Failed to open in explorer: {e}")
        return False

def open_media_file(filepath: str) -> bool:
    """Launches the default media player on Windows for the file."""
    if not filepath or not os.path.exists(filepath):
        return False
    try:
        norm_path = os.path.normpath(os.path.abspath(filepath))
        if os.name == 'nt':
            try:
                os.startfile(norm_path)
            except Exception:
                subprocess.Popen(f'start "" "{norm_path}"', shell=True)
            return True
        elif hasattr(os, 'uname') and os.uname().sysname == 'Darwin':
            subprocess.Popen(['open', norm_path])
            return True
        else:
            subprocess.Popen(['xdg-open', norm_path])
            return True
    except Exception as e:
        print(f"Failed to open media file: {e}")
        return False

def open_downloads_folder(folder_path: str) -> bool:
    """Opens the downloads directory in Windows Explorer / default file manager."""
    try:
        abs_path = os.path.abspath(folder_path)
        os.makedirs(abs_path, exist_ok=True)
        norm_path = os.path.normpath(abs_path)
        if os.name == 'nt':
            # explorer.exe "<path>" is fast and reliable
            subprocess.Popen(f'explorer.exe "{norm_path}"')
            return True
        elif hasattr(os, 'uname') and os.uname().sysname == 'Darwin':
            subprocess.Popen(['open', norm_path])
            return True
        else:
            subprocess.Popen(['xdg-open', norm_path])
            return True
    except Exception as e:
        print(f"Failed to open folder: {e}")
        return False
