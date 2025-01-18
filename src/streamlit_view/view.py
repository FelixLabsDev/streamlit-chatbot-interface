import os
import subprocess
import requests
import logging
from .view_configurations import define_endpoints

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class View:
    def __init__(self, app, view_callback, title="Streamlit Chatbot Interface"):
        logging.info("Initializing View class")
        define_endpoints(app, view_callback)
        # self.run(title=title)

    def send_message(self, chat_id, message):
        return message

    def run_streamlit(self, title):
        try:
            filename = os.path.join(os.path.dirname(__file__), "streamlit_chat_ui.py")
            # command = ["streamlit", "run", filename, "--", "--clean", "--title", title]
            command = ["streamlit", "run", filename, "--", "--title", title]
            env = os.environ.copy()
            env["PYTHONPATH"] = os.path.abspath(
                os.path.join(os.path.dirname(__file__), "../../")
            )  # Set project root as PYTHONPATH

            subprocess.run(command, check=True, env=env)
        except subprocess.CalledProcessError as e:
            logging.error(f"Error occurred while running command: {e}")

    def run(self, title="Streamlit Chatbot Interface"):
        self.run_streamlit(title)


def send_input(user_input):
    logger.info("Inside send_input")
    logger.info(f"User input: {user_input}")
    try:
        # Sending the user input to FastAPI and receiving AI response
        response = requests.post(
            "http://localhost:5051/input", json={"user_input": user_input}
        )
        logger.info(f"Response: {response}")
        if response.status_code == 200:
            return response.json().get("ai_response", "No AI response")
        else:
            return "Error: Failed to get AI response"
    except requests.exceptions.RequestException as e:
        return f"Error: {str(e)}"


def delete_history():
    try:
        # Sending the user input to FastAPI and receiving AI response
        response = requests.post("http://localhost:5051/delete_history")
        if response.status_code == 200:
            return response.json().get("graph_response", "history not deleted")
        else:
            return "Error: Failed to delete chat history"
    except requests.exceptions.RequestException as e:
        return f"Error: {str(e)}"
