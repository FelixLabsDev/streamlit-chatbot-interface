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
from streamlit_view.view_configurations import define_endpoints
# from orchestrator.utils.schemas import AgentRequest, AgentResponse, AgentRequestType, ResponseStatus
# Todo: Need to create own schemas for views, and combine views into one repo
from agent_ti.utils.schemas import AgentRequest, AgentRequestType, AgentResponse, RequestStatus, Metadata 
from view_utils.view_abc import BaseView, RedisEnabledMixin

from utils.logging_config import get_logger
from utils.config_loader import Config

# Load configuration first
config = Config.from_yaml("configs/config.yml")
HOST = config.view.fastapi.host
PORT = config.view.fastapi.port


# Configure logging
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = get_logger(__name__)

class StreamlitView(RedisEnabledMixin, BaseView):
    
    def __init__(self, config, view_callback, title="Streamlit Chatbot Interface", host="0.0.0.0", port=5051):
        logging.info("Initializing StreamlitView")
        logging.info(f"host: {host}, port: {port}, title: {title}")
        self.config = config
        self.host = host
        self.port = port
        self.title = title
        self.app = FastAPI()
        
        define_endpoints(self.app, view_callback, self.get_response_callback)
    
    @classmethod
    def from_config(cls, config, callback: Callable) -> 'StreamlitView':
        """
        Create a StreamlitView instance from configuration.
        
        Args:
            config: StreamlitViewConfig with required fastapi settings
            callback: The callback function to handle view events
            
        Returns:
            StreamlitView: A configured view instance
        """
        return cls(
            config,
            callback,
            title=config.title,
            host=config.fastapi.host,
            port=config.fastapi.port
        )
    
    def set_redis_client(self, redis_client):
        super().set_redis_client(redis_client)
        
    async def send_message(self, response: AgentResponse):
        await self.redis.store_ai_response(response)

    def run_streamlit(self):
        logger.info("Running Streamlit app")
        try:
            filename = os.path.join(
                os.path.dirname(__file__),
                self.config.ui_file
            )
            command = ["streamlit", "run", filename, "--", "--title", self.title]
            env = os.environ.copy()
            env["PYTHONPATH"] = os.path.abspath(
                os.path.join(os.path.dirname(__file__), "../../")
            )  # Set project root as PYTHONPATH

            subprocess.run(command, check=True, env=env)
        except subprocess.CalledProcessError as e:
            logger.error(f"Error running Streamlit: {e}")
            
    async def get_response_callback(self, chat_id: str) -> AgentResponse:
        """Get AI response for a specific chat"""
        if self.redis and self.redis.client:
            return await self.redis.get_first_ai_response(chat_id)
        return None

    async def run_uvicorn(self) -> None:
        """Run the FastAPI server."""
        logger.info("Starting FastAPI server", extra={"host": self.host, "port": self.port})
        config = uvicorn.Config(self.app, host=self.host, port=self.port, log_level="info", loop="asyncio")
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
        
    def run_sync(self, title="Streamlit Chatbot Interface"):
        """Run Streamlit synchronously."""
        self.run_streamlit(title)

    @staticmethod
    def send_input(user_input, chat_id, message_id) -> Tuple[Union[requests.Response, str], Optional[str]]:
        """Send user input to the FastAPI server."""
        logger.info(f"Sending user input for chat_id: {chat_id}")
        logger.debug(f"posting to http://{HOST}:{PORT}/input")
        try:
            # Create metadata with message_id
            metadata = Metadata().add("message_id", message_id)
            
            # Create request using the class method
            agent_request = AgentRequest.text(
                chat_id=str(chat_id),
                message=user_input,
                metadata=metadata
            )
            
            # Send request to FastAPI server
            response = requests.post(
                # f"http://{StreamlitView.host}:{StreamlitView.port}/input", 
                f"http://localhost:{PORT}/input", 
                json=json.loads(agent_request.model_dump_json())
            )
            
            if response.status_code == RequestStatus.SUCCESS.code:
                return response
            else:
                return f"Error: Request failed with status code {response.status_code}", None
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error: {e}")
            return f"Error: {str(e)}", None
        except Exception as e:
            logger.error(f"Error sending input: {e}")
            return f"Error: {str(e)}", None

    @staticmethod
    def get_response(chat_id) -> AgentResponse:
        """Get AI response from the FastAPI server."""
        logger.info(f"Getting response for chat_id: {chat_id}")
        try:
            response = requests.get(f"http://{HOST}:{PORT}/get_response?chat_id={chat_id}")
            
            if response.status_code == RequestStatus.SUCCESS.code:
                data = response.json()
                
                if data['status'] == RequestStatus.SUCCESS.value:
                    # Parse response as AgentResponse if available
                    if 'ai_response' in data and isinstance(data['ai_response'], dict):
                        return AgentResponse.model_validate(data['ai_response'])
                    
                    # Create new AgentResponse with message only
                    metadata = Metadata().add("message_id", str(uuid.uuid4()))
                    
                    return AgentResponse(
                        chat_id=str(chat_id),
                        message=data.get('ai_response'),
                        status=RequestStatus.SUCCESS,
                        metadata=metadata
                    )
                
                # Return pending response
                return AgentResponse.pending(chat_id=str(chat_id))
            
            # Return error response for non-200 status codes
            metadata = Metadata().add("error", f"Unexpected status code {response.status_code}")
            return AgentResponse.error(chat_id=str(chat_id), metadata=metadata)
            
        except Exception as e:
            logger.error(f"Error getting response: {e}")
            metadata = Metadata().add("error", str(e))
            return AgentResponse.error(chat_id=str(chat_id), metadata=metadata)

    @staticmethod
    def delete_all_history():
        """Delete all chat history."""
        try:
            agent_request = AgentRequest.delete_history()
            response = requests.post(
                f"http://{HOST}:{PORT}/delete_all_history", 
                json=json.loads(agent_request.model_dump_json())
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
            agent_request = AgentRequest.delete_entries_by_chat_id(chat_id=str(chat_id))
            response = requests.post(
                f"http://{HOST}:{PORT}/delete_chat", 
                json=json.loads(agent_request.model_dump_json())
            )
            
            if response.status_code == RequestStatus.SUCCESS.code:
                return "Chat deleted successfully"
            else:
                return f"Error: Failed to delete chat (code: {response.status_code})"
        except Exception as e:
            logger.error(f"Error deleting chat: {e}")
            return f"Error: {str(e)}"