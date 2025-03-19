import os
import subprocess
import requests
import logging
import asyncio
from .view_configurations import define_endpoints
from .view_abc import BaseView, RedisEnabledMixin


# Configure logging
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("view")

class View(RedisEnabledMixin, BaseView):
    
    def __init__(self, app, view_callback, title="Streamlit Chatbot Interface"):
        logging.info("Initializing View class")
        define_endpoints(app, view_callback, self.get_response_callback)
        # self.run(title=title)
        
    def set_redis_client(self, redis_client):
        super().set_redis_client(redis_client)
        
    async def send_message(self, chat_id, message):
        await self.redis.store_ai_response(chat_id, message)

    def run_streamlit(self, title):
        logger.info("Running Streamlit app")
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
            
    async def get_response_callback(self, thread_id: str) -> str:
        """Get AI response for a specific chat"""
        if self.redis and self.redis.client:
            return await self.redis.get_first_ai_response(thread_id)
        return None

    async def run(self, title="Streamlit Chatbot Interface"):
        # Offload the blocking call to a thread
        await asyncio.to_thread(self.run_streamlit, title)
        
    def run_sync(self, title="Streamlit Chatbot Interface"):
        # Optionally, you can call the sync version from your main code:
        self.run_streamlit(title)


def send_input(user_input, thread_id="_"):
    logger.info("Inside send_input")
    logger.info(f"User input: {user_input}")
    try:
        # Sending the user input to FastAPI and receiving AI response
        response = requests.post(
            "http://localhost:5051/input", json={"user_input": user_input, "thread_id": thread_id}
        )
        logger.info(f"Response View: {response.content}")
        if response.status_code == 200:
            return response.content
        else:
            return "Error: Failed to get AI response"
    except requests.exceptions.RequestException as e:
        return f"Error: {str(e)}"

def get_response(thread_id):
    logger.info(f"Inside get_response for thread_id: {thread_id}")
    try:
        # Sending the user input to FastAPI and receiving AI response
        response = requests.get(
            f"http://localhost:5051/get_response?thread_id={thread_id}"
        )
        logger.info(f"Response OLD: {response}")
        return response
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