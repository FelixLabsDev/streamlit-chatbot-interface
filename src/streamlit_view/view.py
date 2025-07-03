import os
import subprocess
import requests
import logging
import asyncio
import uvicorn
import uuid
import json
from typing import Callable, Dict, Any, Optional, Tuple, Union
from fastapi import FastAPI
from streamlit_view.view_configurations import define_endpoints, ServerConfig

# Todo: Need to create own schemas for views, and combine views into one repo
from common_utils.schemas import AgentRequest, AgentResponse, RequestStatus
from common_utils.view.view_abc import BaseView
from common_utils.logging import get_logger

# Load configuration first


# Configure logging
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = get_logger(__name__)


class StreamlitView(BaseView):
    def __init__(
        self,
        config,
        view_callback,
        title="Streamlit Chatbot Interface",
        host="0.0.0.0",
        port=5051,
    ):
        logging.info(
            f"Initializing StreamlitView - host: {host}, port: {port}, title: {title}"
        )
        self.config = config
        self.title = title
        self.app = FastAPI()
        
        # Store host and port for FastAPI server
        self._host = host
        self._port = port
        
        # Configure the server settings
        ServerConfig().configure(host=host, port=port)

        define_endpoints(self.app, view_callback)

    @property
    def host(self) -> str:
        return self._host

    @property
    def port(self) -> int:
        return self._port

    @classmethod
    def from_config(cls, config, callback: Callable) -> "StreamlitView":
        """
        Create a StreamlitView instance from configuration.
        """
        return cls(
            config,
            callback,
            title=config.title,
            host=config.fastapi.host,
            port=config.fastapi.port,
        )

    def run_streamlit(self):
        logger.info("Running Streamlit app")
        try:
            filename = os.path.join(os.path.dirname(__file__), self.config.ui_file)
            command = ["streamlit", "run", filename, "--", "--title", self.title]
            env = os.environ.copy()
            env["PYTHONPATH"] = os.path.abspath(
                os.path.join(os.path.dirname(__file__), "../../")
            )  # Set project root as PYTHONPATH

            subprocess.run(command, check=True, env=env)
        except subprocess.CalledProcessError as e:
            logger.error(f"Error running Streamlit: {e}")

    async def run_uvicorn(self) -> None:
        """Run the FastAPI server."""
        logger.info(
            "Starting FastAPI server", extra={"host": self.host, "port": self.port}
        )
        config = uvicorn.Config(
            self.app, host=self.host, port=self.port, log_level="info", loop="asyncio"
        )
        server = uvicorn.Server(config)
        await server.serve()

    def run_fastapi(self) -> asyncio.Task:
        """Start the FastAPI server."""
        return asyncio.create_task(self.run_uvicorn())

    async def run(self):
        """Run both FastAPI server and Streamlit application."""
        fastapi_task = self.run_fastapi()
        streamlit_task = asyncio.create_task(asyncio.to_thread(self.run_streamlit))

        return await asyncio.gather(fastapi_task, streamlit_task)

    @staticmethod
    def send_message(chat_id: str, message: str) -> Union[AgentResponse, str]:
        """Send user input to the FastAPI server and return a proper AgentResponse."""
        logger.info(f"Sending user input for chat_id: {chat_id}")
        server_config = ServerConfig()
        logger.debug(f"posting to {server_config.base_url}/input")
        try:
            # Create metadata with message_id
            request = AgentRequest.text(
                chat_id=str(chat_id), message=user_input
            )

            # Send request to FastAPI server
            response = requests.post(
                f"{server_config.base_url}/input",
                json=json.loads(request.model_dump_json()),
            )

            if response.status_code == RequestStatus.SUCCESS.code:
                response_data = response.json()
                return AgentResponse.model_validate_json(response_data["response"])
            else:
                return f"Error: Request failed with status code {response.status_code}"
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error: {e}")
            return f"Error: {str(e)}"
        except Exception as e:
            logger.error(f"Error sending input: {e}")
            return f"Error: {str(e)}"

    @staticmethod
    def delete_all_history():
        """Delete all chat history."""
        try:
            server_config = ServerConfig()
            agent_request = AgentRequest.delete_history()
            response = requests.post(
                f"{server_config.base_url}/delete_all_history",
                json=json.loads(agent_request.model_dump_json()),
            )

            if response.status_code == RequestStatus.SUCCESS.code:
                return "History deleted successfully"
            else:
                return f"Error: Failed to delete history (code: {response.status_code})"
        except Exception as e:
            logger.error(f"Error deleting history: {e}")
            return f"Error: {str(e)}"

    @staticmethod
    def delete_chat(chat_id):
        """Delete chat history for a specific chat."""
        try:
            server_config = ServerConfig()
            agent_request = AgentRequest.delete_entries_by_chat_id(chat_id=str(chat_id))
            response = requests.post(
                f"{server_config.base_url}/delete_chat",
                json=json.loads(agent_request.model_dump_json()),
            )

            if response.status_code == RequestStatus.SUCCESS.code:
                return "Chat deleted successfully"
            else:
                return f"Error: Failed to delete chat (code: {response.status_code})"
        except Exception as e:
            logger.error(f"Error deleting chat: {e}")
            return f"Error: {str(e)}"
