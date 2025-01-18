from controller.controller import Orchestrator
import logging
import threading


# Function to run the FastAPI app
def run_server(logger):
    logger.info("FastAPI app started")
    orchestrator.run(port=5051, host="0.0.0.0")


def run_view(title="Bot name"):
    # Start FastAPI app in a separate thread
    fastapi_thread = threading.Thread(target=run_server, args=(orchestrator.logger,))
    fastapi_thread.daemon = True  # This makes the FastAPI thread exit when the main program exits
    fastapi_thread.start()

    # Start Streamlit app
    orchestrator.run_view(title)

if __name__ == "__main__":
    orchestrator = Orchestrator()
    run_view()