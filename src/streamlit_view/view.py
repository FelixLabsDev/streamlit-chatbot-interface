import os
import subprocess
import requests
import logging
import asyncio
import uvicorn
from typing import Callable
from fastapi import FastAPI
from .view_configurations import define_endpoints
from view.view_abc import BaseView, RedisEnabledMixin


# Configure logging
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("view")

class StreamlitView(RedisEnabledMixin, BaseView):
    
    def __init__(self, view_callback, title="Streamlit Chatbot Interface", host="0.0.0.0", port=5051):
        logging.info("Initializing View class")
        self.host = host
        self.port = port
        self.app = FastAPI()
        self.title = title
        
        define_endpoints(self.app, view_callback, self.get_response_callback)
    
    @classmethod
    def from_config(cls, config: dict, callback: Callable) -> 'StreamlitView':
        host = config.get('host', 'localhost')
        port = config.get('port', 8501)
        title = config.get('title', "Streamlit Chatbot Interface")
        instance = cls(callback, host=host, port=port, title=title)
        return instance
    
    def set_redis_client(self, redis_client):
        super().set_redis_client(redis_client)
        
    async def send_message(self, chat_id, message):
        await self.redis.store_ai_response(chat_id, message)

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
            
    async def get_response_callback(self, thread_id: str) -> str:
        """Get AI response for a specific chat"""
        if self.redis and self.redis.client:
            return await self.redis.get_first_ai_response(thread_id)
        return None

    async def run_uvicorn(self) -> None:
        """Run the FastAPI server."""
        logger.info("Starting FastAPI server", extra={"host": self.host, "port": self.port})
        config = uvicorn.Config(self.app, host=self.host, port=self.port, log_level="info", loop="asyncio")
        server = uvicorn.Server(config)
        await server.serve()

    async def run_fastapi(self) -> asyncio.Task:
        """Start the FastAPI server."""
        return asyncio.create_task(self.run_uvicorn())

    async def run(self, title="Streamlit Chatbot Interface"):
        # Start both the FastAPI server and Streamlit
        fastapi_task = self.run_fastapi()
        streamlit_task = asyncio.create_task(asyncio.to_thread(self.run_streamlit, title))
        
        # Wait for both tasks to complete
        return asyncio.gather(fastapi_task, streamlit_task)
        
    def run_sync(self, title="Streamlit Chatbot Interface"):
        # Optionally, you can call the sync version from your main code:
        self.run_streamlit(title)


def send_input(user_input, thread_id):
    logger.info("Inside send_input")
    logger.info(f"User input: {user_input}")
    try:
        # Sending the user input to FastAPI and receiving AI response
        response = requests.post(
            "http://localhost:5051/input", json={"user_input": user_input, "thread_id": thread_id}
        )
        logger.info(f"SEND_INPUT Response: {response}")
        if response.status_code == 200:
            return response
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
        logger.info(f"GET_RESPONSE Response: {response}")
        return response
    except requests.exceptions.RequestException as e:
        return f"Error: {str(e)}"


def delete_all_history():
    try:
        # Sending the user input to FastAPI and receiving AI response
        response = requests.post("http://localhost:5051/delete_all_history")
        if response.status_code == 200:
            return response.json().get("graph_response", "history not deleted")
        else:
            return "Error: Failed to delete all chat history"
    except requests.exceptions.RequestException as e:
        return f"Error: {str(e)}"

def delete_chat(chat_id):
    try:
        # Sending the user input to FastAPI and receiving AI response
        response = requests.post("http://localhost:5051/delete_chat", json={"chat_id": chat_id})
        if response.status_code == 200:
            return response.json().get("graph_response", "history not deleted")
        else:
            return "Error: Failed to delete chat history"
    except requests.exceptions.RequestException as e:
        return f"Error: {str(e)}"