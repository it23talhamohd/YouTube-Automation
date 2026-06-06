import time
import subprocess
import os
import sys

# Reconfigure stdout to use UTF-8 on Windows to support emojis in console logging
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
import logging
from datetime import datetime

# Configure logging to console and a scheduler log file
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
log_file = os.path.join(BASE_DIR, "logs", "scheduler_loop.log")
os.makedirs(os.path.dirname(log_file), exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] Loop: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(log_file, encoding="utf-8")
    ]
)
logger = logging.getLogger("SchedulerLoop")

def run_pipeline():
    logger.info("Executing main.py automation pipeline...")
    try:
        # Run python main.py --run
        cmd = [sys.executable, "main.py", "--run"]
        result = subprocess.run(cmd, cwd=BASE_DIR, capture_output=True, text=True, encoding="utf-8")
        
        # Log command outputs
        if result.returncode == 0:
            logger.info("Pipeline run executed successfully.")
        else:
            logger.error(f"Pipeline exited with error code {result.returncode}.")
            
        if result.stdout:
            logger.debug(f"STDOUT:\n{result.stdout}")
        if result.stderr:
            logger.error(f"STDERR:\n{result.stderr}")
            
    except Exception as e:
        logger.error(f"Failed to execute pipeline process: {e}")

def main():
    logger.info("=============================================")
    logger.info(f"Starting Continuous Hour-Aligned Scheduler Loop")
    logger.info("Keep this terminal window open to run autonomously.")
    logger.info("=============================================")
    
    # Run immediately on start
    run_pipeline()
    
    from datetime import timedelta
    
    while True:
        try:
            # Calculate seconds until the next hour boundary
            now = datetime.now()
            seconds_until_next_hour = 3600 - (now.minute * 60 + now.second) + 1 # Add 1s buffer
            
            wake_up_time = now + timedelta(seconds=seconds_until_next_hour)
            logger.info(f"Sleeping until next hour boundary. Next execution at: {wake_up_time.strftime('%Y-%m-%d %H:%M:%S')}...")
            time.sleep(seconds_until_next_hour)
            
            run_pipeline()
        except KeyboardInterrupt:
            logger.info("Scheduler loop stopped by user.")
            break
        except Exception as e:
            logger.error(f"Unexpected error in scheduler loop: {e}")
            time.sleep(60) # Wait a minute before retrying to prevent hot looping

if __name__ == "__main__":
    main()
