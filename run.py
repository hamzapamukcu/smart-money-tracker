#!/usr/bin/env python3
import subprocess
import sys
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")

def run():
    logging.info("Starting Streamlit Dashboard...")
    try:
        subprocess.run([sys.executable, "-m", "streamlit", "run", "app/main.py"])
    except KeyboardInterrupt:
        logging.info("Shutting down...")

if __name__ == "__main__":
    run()
