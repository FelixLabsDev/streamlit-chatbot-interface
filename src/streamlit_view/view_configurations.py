from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import logging
from pydantic import ValidationError
import json
import os
import sys


from agent_ti.utils.schemas import AgentRequest, AgentResponse, RequestStatus, Metadata


logger = logging.getLogger(__name__)


def define_endpoints(app, view_callback):
    @app.post("/input")
    async def receive_input(request: Request):
        try:
            data = await request.json()
            logger.info(f"Processing input request - chat_id: {data.get('chat_id')}, message: {data.get('message', '')}")

            try:
                agent_request = AgentRequest.model_validate(data)
            except ValidationError as e:
                logger.error(f"Invalid request format: {e}")
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid request format: {str(e)}",
                )

            # Get response directly from agent
            agent_response = await view_callback(agent_request)
            
            logger.debug(f"Agent response: {agent_response}")

            # Handle None response by creating a pending response
            if agent_response is None:
                agent_response = AgentResponse(
                    chat_id=agent_request.chat_id,  # Use chat_id from request
                    message="Request received and queued for processing",
                    metadata=Metadata().add("info", "Request is being processed asynchronously")
                )
            logger.debug(f"Agent response now: {agent_response}")

            return JSONResponse(
                {"status": "success", "response": agent_response.model_dump_json()},
                status_code=200,
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error processing input: {e}", exc_info=True)
            # Create an error response instead of raising an exception
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/delete_all_history")
    async def delete_history(request: Request):
        try:
            # For now, just return success - we'll implement this later
            return JSONResponse(
                {"status": "success", "message": "Chat history deleted"},
                status_code=200,
            )
        except Exception as e:
            logger.error(f"Error deleting history: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/delete_chat")
    async def delete_chat(request: Request):
        try:
            data = await request.json()

            agent_request = AgentRequest.model_validate(data)

            if not agent_request.chat_id:
                raise HTTPException(status_code=400, detail="No chat ID provided")

            # For now, just return success - we'll implement this later
            return JSONResponse(
                {"status": "success", "message": "Chat deleted"},
                status_code=200,
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error deleting chat: {e}")
            raise HTTPException(status_code=500, detail=str(e))


class ServerConfig:
    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ServerConfig, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self._host = "localhost"
            self._port = 5051
            self._initialized = True

    @property
    def host(self) -> str:
        return self._host

    @property
    def port(self) -> int:
        return self._port

    def configure(self, host: str, port: int):
        self._host = host
        self._port = port

    @property
    def base_url(self) -> str:
        return f"http://{self._host}:{self._port}"
