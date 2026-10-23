import os
import sys
import webbrowser
import threading
import time
import uvicorn

def open_browser():
    time.sleep(1.2)
    webbrowser.open("http://127.0.0.1:8000")

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

if __name__ == "__main__":
    print("=" * 60)
    print("  [*] VDOWN - Universal High-Speed Video & Audio Downloader")
    print("=" * 60)
    print("  Local Server : http://127.0.0.1:8000")
    print("  Downloads Dir: " + os.path.abspath("downloads"))
    print("=" * 60)
    
    # Auto-open browser in background thread
    threading.Thread(target=open_browser, daemon=True).start()
    
    # Run uvicorn server
    uvicorn.run("backend.app:app", host="127.0.0.1", port=8000, reload=False)
