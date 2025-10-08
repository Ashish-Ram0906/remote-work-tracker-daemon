import time
from datetime import datetime, timezone
import psutil
from pynput import mouse, keyboard
import gi
gi.require_version('Atspi', '2.0')
from gi.repository import Atspi

# --- Global State ---
last_activity_time = time.time()
# Keywords to check for if the user seems idle but might be in a meeting or watching a video
MEDIA_MEETING_KEYWORDS = [
    "youtube", "google meet", "zoom", "vlc", "playing"
]

# --- Event Listeners ---
def on_activity(*args):
    global last_activity_time
    last_activity_time = time.time()

mouse_listener = mouse.Listener(on_move=on_activity, on_click=on_activity, on_scroll=on_activity)
keyboard_listener = keyboard.Listener(on_press=on_activity)

def start_listeners():
    mouse_listener.start()
    keyboard_listener.start()
    print("👂 Activity listeners started.")

def stop_listeners():
    mouse_listener.stop()
    keyboard_listener.stop()
    print("👂 Activity listeners stopped.")

# --- Window Info ---
def get_active_window_info():
    """Gets the title of the currently active window."""
    try:
        desktop = Atspi.get_desktop(0)
        for i in range(desktop.get_child_count()):
            app = desktop.get_child_at_index(i)
            if app and app.get_role_name() == 'application':
                for j in range(app.get_child_count()):
                    window = app.get_child_at_index(j)
                    if window and window.get_state_set().contains(Atspi.StateType.ACTIVE):
                        title = window.get_name()
                        return title, None
    except Exception as e:
        print(f"[{datetime.now()}] [Tracker] -> ❌ Error getting active window: {e}")
        return None, None
    return None, None

# --- Main Polling Function ---
def poll_activity(idle_threshold_seconds: int) -> dict | None:
    """
    Checks the user's current activity, with special handling for idle state
    to detect meetings or media playback.
    """
    timestamp = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
    seconds_since_last_activity = time.time() - last_activity_time
    is_idle_by_input = seconds_since_last_activity > idle_threshold_seconds

    title, app_name = get_active_window_info()

    # If idle by input, check if we can override it with window title
    if is_idle_by_input:
        if title and any(keyword in title.lower() for keyword in MEDIA_MEETING_KEYWORDS):
            print(f"[{datetime.now()}] [Tracker] -> Idle by input, but media/meeting detected. Staying ACTIVE.")
            # Treat as active
        else:
            # Truly idle
            return {
                "timestamp": timestamp,
                "state": "idle",
                "app": None,
                "title": None
            }

    # If active by input or idle was overridden, return active state
    if app_name or title:
        return {
            "timestamp": timestamp,
            "state": "active",
            "app": app_name,
            "title": title
        }

    return None