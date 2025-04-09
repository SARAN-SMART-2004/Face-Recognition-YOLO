import subprocess
import threading
import time
import winsound

def play_windows_beep():
    time.sleep(10)  # Adjust based on how long your server loads
    winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)  # Beep sound

def start_django_server():
    subprocess.call(["python", "manage.py", "runserver"])

threading.Thread(target=play_windows_beep).start()
start_django_server()
