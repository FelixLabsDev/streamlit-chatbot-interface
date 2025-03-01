from controller.controller import Orchestrator
from utils.logging_config import setup_logging, get_logger
import threading
import os

# Initialize logging
setup_logging(
    default_level="INFO",
    log_dir="data/logs",
    enable_colors=True
)

logger = get_logger(__name__)
from datetime import datetime

class UTF8LogFilter(logging.Filter):
    def filter(self, record):
        if isinstance(record.msg, bytes):
            try:
                record.msg = record.msg.decode('utf-8')
            except UnicodeDecodeError:
                pass  # Keep the original message if decoding fails
        return True

logging_config = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format":  "%(asctime)s: %(name)s > %(filename)s > %(funcName)s:%(lineno)d ~ %(levelname)s: %(message)s",
            "datefmt": "%Y-%m-%dT%H:%M:%S%z"
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "standard",
            "stream": "ext://sys.stdout",
            "filters": ["utf8_filter"]
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "formatter": "standard",
            "filename": os.path.join('data', 'logs', f'app_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
            "maxBytes": 1024*1024*10,
            "backupCount": 5,
            "encoding": "utf-8",
            "filters": ["utf8_filter"]
        }
    },
    "filters": {
        "utf8_filter": {
            "()": UTF8LogFilter
        }
    },
    "loggers": {
        "": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": True
        }
    }
}
log_dir = os.path.join('data', 'logs')
os.makedirs(log_dir, exist_ok=True)
logging.config.dictConfig(logging_config)

# Function to run the FastAPI app
def run_server():
    logger.info("FastAPI app started")
    orchestrator.run(port=5051, host="0.0.0.0")

def run_view(title="Bot name"):
    # Start FastAPI app in a separate thread
    fastapi_thread = threading.Thread(target=run_server)
    fastapi_thread.daemon = True  # This makes the FastAPI thread exit when the main program exits
    fastapi_thread.start()

    logger.info("Starting view with title: %s", title)
    # Start Streamlit app
    orchestrator.run_view(title)

if __name__ == "__main__":
    logger.info("Initializing application")
    orchestrator = Orchestrator()
    run_view()