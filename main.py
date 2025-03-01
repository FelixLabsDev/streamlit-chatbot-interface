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