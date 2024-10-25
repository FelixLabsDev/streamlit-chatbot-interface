from controller.controller import Orchestrator
import logging
import threading


# Function to run the Flask app
def run_flask():
    logging.info("Flask app started")
    orchestrator.run(port=5000, host="0.0.0.0")


def run_view():
    # Start Flask app in a separate thread
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True  # This makes the Flask thread exit when the main program exits
    flask_thread.start()

    # Start Streamlit app
    orchestrator.view.run("BOT NAME")

if __name__ == "__main__":
    orchestrator = Orchestrator()
    run_view()