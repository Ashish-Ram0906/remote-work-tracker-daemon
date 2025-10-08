import time
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler

import config
import tracker
import api_client

# --- Global State ---
log_buffer = []
# This will now hold the full dictionary of the currently tracked activity
current_activity = None

# --- Scheduled Job Functions ---

def polling_job():
    """
    Polls user activity, calculates duration of the last activity when it changes,
    and adds completed activities to the buffer.
    """
    global current_activity
    
    # Get the state of activity right now
    now = datetime.now()
    polled_activity = tracker.poll_activity(config.settings['idle_threshold_seconds'])
    
    if not polled_activity:
        return # Do nothing if tracker returned no data

    # Check if this is the very first activity we're tracking
    if current_activity is None:
        print(f"[{now}] -> Starting to track new activity: {polled_activity['state']}")
        polled_activity['start_time'] = now
        current_activity = polled_activity
        return

    # Define a signature to easily compare activities
    current_signature = (polled_activity['state'], polled_activity['app'], polled_activity['title'])
    last_signature = (current_activity['state'], current_activity['app'], current_activity['title'])

    # If the activity has changed, finalize the previous one and log it
    if current_signature != last_signature:
        print(f"[{now}] -> Activity changed from '{last_signature[0]}' to '{current_signature[0]}'")
        
        # Calculate duration of the previous activity
        duration_seconds = (now - current_activity['start_time']).total_seconds()
        current_activity['duration'] = round(duration_seconds)
        
        # Remove the temporary start_time key before adding to buffer
        del current_activity['start_time']
        
        log_buffer.append(current_activity)
        print(f"[{now}]   -> Logged previous activity with duration: {duration_seconds:.2f}s")
        
        # Start tracking the new activity
        polled_activity['start_time'] = now
        current_activity = polled_activity

def sending_job():
    """Sends the contents of the buffer to the backend."""
    global log_buffer
    
    print(f"\n[{datetime.now()}] --- Sending Job Triggered ---")
    if not log_buffer:
        print(f"[{datetime.now()}]   -> Buffer is empty. Nothing to send.")
        return

    data_to_send = list(log_buffer)
    
    if api_client.send_data_to_backend(data_to_send):
        log_buffer = log_buffer[len(data_to_send):]
        print(f"[{datetime.now()}]   -> ✅ Send successful. Cleared {len(data_to_send)} items from buffer.")
    else:
        print(f"[{datetime.now()}]   -> ❌ Send failed. Data will be kept for next attempt.")

# --- Main Execution ---

def main():
    """The main entry point for the daemon."""
    global current_activity
    print("🚀 Starting Remote Work Tracker Daemon...")

    try:
        config.load_config()
        tracker.start_listeners()
        
        scheduler = BackgroundScheduler(timezone="UTC")
        scheduler.add_job(polling_job, 'interval', seconds=5)
        scheduler.add_job(sending_job, 'interval', seconds=30)
        scheduler.start()
        
        print("✅ Daemon is running. Press CTRL+C to stop.")
        
        while True:
            time.sleep(1)

    except (FileNotFoundError, ValueError) as e:
        print(f"❌ CRITICAL ERROR: {e}. Daemon cannot start.")
    except KeyboardInterrupt:
        print("\n🛑 Shutting down daemon...")
    finally:
        # Before shutting down, log the final activity
        if current_activity:
            duration = (datetime.now() - current_activity['start_time']).total_seconds()
            current_activity['duration'] = round(duration)
            del current_activity['start_time']
            log_buffer.append(current_activity)
            if log_buffer:
                print("--- Sending final batch of logs before shutdown ---")
                sending_job()

        tracker.stop_listeners()
        if 'scheduler' in locals() and scheduler.running:
            scheduler.shutdown()
        print("👋 Daemon has stopped.")

if __name__ == "__main__":
    main()