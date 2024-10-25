import os
import subprocess
import subprocess
import requests
import logging
from src.streamlit_view.view_configurations import define_endpoints, endpoint_blueprint


class View:
    def __init__(self, app, view_callback, title="Streamlit Chatbot Interface"):
        logging.info("Initializing View class")
        define_endpoints(view_callback)
        app.register_blueprint(endpoint_blueprint)
        # self.run(title=title)

    def send_message(self, chat_id, message):
        return message

    def run_streamlit(self, title):
        try:
            filename = os.path.join(os.path.dirname(__file__), "streamlit_chat_ui.py")
            command = ["streamlit", "run", filename, "--", "--clean", "--title", title]
            env = os.environ.copy()
            env["PYTHONPATH"] = os.path.abspath(
                os.path.join(os.path.dirname(__file__), "../../")
            )  # Set project root as PYTHONPATH

            subprocess.run(command, check=True, env=env)
        except subprocess.CalledProcessError as e:
            print(f"Error occurred while running command: {e}")

    def run(self, title="Streamlit Chatbot Interface"):
        self.run_streamlit(title)


def send_input(user_input):
    try:
        # Sending the user input to Flask and receiving AI response
        response = requests.post(
            "http://localhost:5000/input", json={"user_input": user_input}
        )
        if response.status_code == 200:
            return response.json().get("ai_response", "No AI response")
        else:
            return "Error: Failed to get AI response"
    except requests.exceptions.RequestException as e:
        return f"Error: {str(e)}"


def delete_history():
    try:
        # Sending the user input to Flask and receiving AI response
        response = requests.post("http://localhost:5000/delete_history")
        if response.status_code == 200:
            return response.json().get("flask_server_response", "history not deleted")
        else:
            return "Error: Failed to delete chat history"
    except requests.exceptions.RequestException as e:
        return f"Error: {str(e)}"
