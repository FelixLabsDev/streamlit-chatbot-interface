import logging
import threading
import os
from common_utils.logging import setup_logging, get_logger

# Note: Logging is already set up by the main orchestrator application
# We just get a logger instance here
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