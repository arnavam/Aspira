import logging
import os
import sys
import time

# Store start time for elapsed time calculation
_start_time = time.time()

def reset_timer():
    """Reset the elapsed time counter (call when user input is received)."""
    global _start_time
    _start_time = time.time()

class ElapsedTimeFormatter(logging.Formatter):
    """Custom formatter that shows elapsed time since start."""
    
    def format(self, record):
        elapsed = time.time() - _start_time
        record.elapsed = f"{elapsed:.2f}s"
        return super().format(record)

def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    
    # Prevent duplicate handlers
    if logger.hasHandlers():
        logger.handlers.clear()
        
    log_level_str = os.environ.get("LOG_LEVEL", "INFO").upper()
    log_level = getattr(logging, log_level_str, logging.INFO)
    logger.setLevel(log_level)
    
    formatter = ElapsedTimeFormatter(
        '[%(elapsed)s] -- %(filename)s -- %(message)s'
    )
    
    # Always stdout (Docker best practice)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Optional file (local dev only)
    if not os.environ.get("DOCKER_ENV"):
        log_dir = "log"
        os.makedirs(log_dir, exist_ok=True)
        file_handler = logging.FileHandler(os.path.join(log_dir, "app.log"), encoding='utf-8')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    logger.propagate = False
    return logger
