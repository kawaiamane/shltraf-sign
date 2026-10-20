"""ProjectVault standalone: Python standard library only."""
import threading, webbrowser
from backend.server import main
if __name__ == '__main__':
    threading.Timer(1.0, lambda: webbrowser.open('http://127.0.0.1:8765')).start()
    main()
