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
from utils.schemas import AgentRequest, AgentResponse, AgentRequestType, ResponseStatus, Metadata
from view_utils.view_abc import BaseView, RedisEnabledMixin

from utils.logging_config import get_logger


# Configure logging
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = get_logger(__name__)

class StreamlitView(RedisEnabledMixin, BaseView):
    
    def __init__(self, config, view_callback, title="Streamlit Chatbot Interface", host="0.0.0.0", port=5051):
        logging.info("Initializing View class")
        self.config = config
        self.host = host
        self.port = port
        self.app = FastAPI()
        self.title = title
        
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
        # Direct instantiation using the config object properties
        print('View config:', config)
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

    def run_streamlit(self, title):
        logger.info("Running Streamlit app")
        try:
            filename = os.path.join(
                os.path.dirname(__file__),
                self.config.ui_file
            )
            # command = ["streamlit", "run", filename, "--", "--clean", "--title", title]
            command = ["streamlit", "run", filename, "--", "--title", title]
            env = os.environ.copy()
            env["PYTHONPATH"] = os.path.abspath(
                os.path.join(os.path.dirname(__file__), "../../")
            )  # Set project root as PYTHONPATH

            subprocess.run(command, check=True, env=env)
        except subprocess.CalledProcessError as e:
            logging.error(f"Error occurred while running command: {e}")
            
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
        # Start both the FastAPI server and Streamlit
        fastapi_task = self.run_fastapi()
        streamlit_task = asyncio.create_task(asyncio.to_thread(self.run_streamlit, self.title))
        
        # Wait for both tasks to complete
        return await asyncio.gather(fastapi_task, streamlit_task)
        
    def run_sync(self, title="Streamlit Chatbot Interface"):
        # Optionally, you can call the sync version from your main code:
        self.run_streamlit(title)

    @staticmethod
    def send_input(user_input, chat_id, message_id) -> Tuple[Union[requests.Response, str], Optional[str]]:
        logger.info("Inside send_input")
        logger.info(f"User input: {user_input}")
        try:
            # Create a unique message_id for tracking
            
            # Create a Metadata object with message_id
            metadata = Metadata()
            metadata.add("message_id", message_id)
            
            # Create an AgentRequest object
            agent_request = AgentRequest(
                chat_id=int(chat_id),
                type=AgentRequestType.TEXT,
                message=user_input,
                user_details={},
                bypass=False,
                metadata=metadata
            )
            
            # Serialize AgentRequest to JSON for the HTTP request
            request_json = json.loads(agent_request.model_dump_json())
            
            # Sending the AgentRequest to FastAPI
            response = requests.post(
                "http://localhost:5051/input", 
                json=request_json
            )
            logger.info(f"SEND_INPUT Response: {response}")
            
            # Return both the response and the message_id
            if response.status_code == 200:
                return response
            else:
                return "Error: Failed to get AI response", None
        except requests.exceptions.RequestException as e:
            return f"Error: {str(e)}", None
        except Exception as e:
            logger.error(f"Error in send_input: {str(e)}")
            return f"Error: {str(e)}", None

    @staticmethod
    def get_response(chat_id) -> AgentResponse:
        logger.info(f"Inside get_response for chat_id: {chat_id}")
        try:
            # Get response from the server
            response = requests.get(
                f"http://localhost:5051/get_response?chat_id={chat_id}"
            )
            logger.info(f"GET_RESPONSE Response: {response}")
            
            # If successful, parse the JSON into an AgentResponse
            if response.status_code == 200:
                data = response.json()
                if data['status'] == 'success':
                    # Parse the JSON response directly into an AgentResponse
                    if 'ai_response' in data and isinstance(data['ai_response'], dict):
                        # The ai_response already contains the full AgentResponse structure
                        agent_response = AgentResponse.model_validate(data['ai_response'])
                        return agent_response
                    else:
                        # Create an AgentResponse with a message only
                        metadata = Metadata()
                        metadata.add("message_id", str(uuid.uuid4()))
                        
                        return AgentResponse(
                            chat_id=int(chat_id),
                            message=data.get('ai_response'),
                            status=ResponseStatus.SUCCESS,
                            metadata=metadata
                        )
                else:
                    # Return a pending response
                    return AgentResponse.pending(chat_id=int(chat_id))
            
            # Return an error response for non-200 status codes
            metadata = Metadata()
            metadata.add("error", f"Unexpected status code {response.status_code}")
            return AgentResponse.error(chat_id=int(chat_id), metadata=metadata)
            
        except requests.exceptions.RequestException as e:
            # Return an error response for request exceptions
            metadata = Metadata()
            metadata.add("error", str(e))
            return AgentResponse.error(chat_id=int(chat_id), metadata=metadata)
        except Exception as e:
            logger.error(f"Error in get_response: {str(e)}")
            # Return an error response for any other exceptions
            metadata = Metadata()
            metadata.add("error", str(e))
            return AgentResponse.error(chat_id=int(chat_id), metadata=metadata)

    @staticmethod
    def delete_all_history():
        try:
            # Create an AgentRequest for deleting all history
            agent_request = AgentRequest(
                chat_id=0,  # Using 0 as a placeholder for all chats
                type=AgentRequestType.DELETE_HISTORY,
                message=None
            )
            
            # Serialize and send the request
            request_json = json.loads(agent_request.model_dump_json())
            response = requests.post("http://localhost:5051/delete_all_history", json=request_json)
            
            if response.status_code == 200:
                return response.json().get("graph_response", "history not deleted")
            else:
                return "Error: Failed to delete all chat history"
        except requests.exceptions.RequestException as e:
            return f"Error: {str(e)}"

    @staticmethod
    def delete_chat(chat_id):
        try:
            # Create an AgentRequest for deleting a specific chat
            agent_request = AgentRequest(
                chat_id=int(chat_id),
                type=AgentRequestType.DELETE_ENTRIES_BY_THREAD_ID,
                message=None
            )
            
            # Serialize and send the request
            request_json = json.loads(agent_request.model_dump_json())
            response = requests.post("http://localhost:5051/delete_chat", json=request_json)
            
            if response.status_code == 200:
                return response.json().get("graph_response", "history not deleted")
            else:
                return "Error: Failed to delete chat history"
        except requests.exceptions.RequestException as e:
            return f"Error: {str(e)}"