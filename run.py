#!/usr/bin/env python3
import subprocess
import sys
import threading
import time
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")

def start_scheduler():
    from src.scheduler import start_scheduler as _start
    _start()
    while True:
        time.sleep(1)

def run():
    logging.info("Starting Background Scheduler...")
    t = threading.Thread(target=start_scheduler, daemon=True)
    t.start()

    logging.info("Starting Streamlit Dashboard...")
    try:
        subprocess.run([sys.executable, "-m", "streamlit", "run", "app/main.py"])
    except KeyboardInterrupt:
        logging.info("Shutting down...")

if __name__ == "__main__":
    run()
