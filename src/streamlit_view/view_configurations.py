from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import logging
from pydantic import ValidationError
import json
import os

print("Current working directory:", os.getcwd())


# from orchestrator.utils.schemas import AgentRequest, AgentResponse, AgentRequestType, ResponseStatus
from utils.schemas import AgentRequest, AgentResponse, AgentRequestType, ResponseStatus

# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("view_configurations")

def define_endpoints(app, view_callback, get_response_callback):
    # Endpoint to receive user input and return AI-generated response
    @app.post("/input")
    async def receive_input(request: Request):
        logger.info("inside receive_input")
        try:
            # Get request data
            data = await request.json()
            
            # Parse the request directly into an AgentRequest object
            try:
                agent_request = AgentRequest.model_validate(data)
            except ValidationError as e:
                logger.error(f"Request validation error: {e}")
                # Fallback to manual construction if validation fails
                agent_request = AgentRequest(
                    type=AgentRequestType.TEXT,
                    chat_id=int(data.get("chat_id")),
                    message=data.get("message") or data.get("user_input"),
                    user_details=data.get("user_details", {}),
                    bypass=data.get("bypass", False),
                    metadata=data.get("metadata")
                )
            
            await view_callback(agent_request)
            return JSONResponse({"status": "success"}, status_code=200)
        except Exception as e:
            logger.error(f"Error in receive_input: {e}")
            raise HTTPException(status_code=400, detail=str(e))
        
    # Endpoint to fetch AI response from Redis
    @app.get("/get_response")
    async def get_response(chat_id: str):
        # Fetch AI response from Redis
        try:
            agent_response = await get_response_callback(chat_id)
            if agent_response:
                # Get the response status
                status_str = "success"
                status_code = 200
                
                if agent_response.is_pending():
                    status_str = "pending"
                    status_code = 202
                elif agent_response.is_error():
                    status_str = "error"
                    status_code = 500
                
                # Convert AgentResponse to JSON and return it directly
                ai_response = json.loads(agent_response.model_dump_json())
                
                return JSONResponse({
                    "status": status_str, 
                    "ai_response": ai_response
                }, status_code=status_code)
            return JSONResponse({"status": "pending"}, status_code=200)
        except Exception as e:
            logger.error(f"Error fetching AI response: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    # Endpoint to delete all chat history
    @app.post("/delete_all_history")
    async def delete_history(request: Request):
        try:
            # Get request data and parse as AgentRequest (if provided)
            data = await request.json() if request.headers.get("content-length", "0") != "0" else {}
            
            # Use the provided AgentRequest or create a new one
            try:
                agent_request = AgentRequest.model_validate(data)
            except (ValidationError, AttributeError):
                # Create default AgentRequest for deleting all history
                agent_request = AgentRequest(
                    type=AgentRequestType.DELETE_HISTORY,
                    chat_id=0  # Using 0 as a placeholder for all chats
                )
            
            await view_callback(agent_request)
            # Return the AI response back to Streamlit
            return JSONResponse({"status": "success", "graph_response": "graph history deleted"}, status_code=200)
        except Exception as e:
            logger.error(f"Error occurred while deleting chat history: {e}")
            raise HTTPException(status_code=400, detail=str(e))
        
    # Endpoint to delete chat history by chat ID
    @app.post("/delete_chat")
    async def delete_chat(request: Request):
        try:
            # Get request data and parse as AgentRequest (if provided)
            data = await request.json()
            
            # Try to use the provided AgentRequest
            try:
                agent_request = AgentRequest.model_validate(data)
            except (ValidationError, AttributeError):
                # If not a valid AgentRequest, create one from the raw data
                chat_id = data.get("chat_id")
                if not chat_id:
                    raise HTTPException(status_code=400, detail="No chat ID received")
                
                agent_request = AgentRequest(
                    type=AgentRequestType.DELETE_ENTRIES_BY_THREAD_ID,
                    chat_id=int(chat_id)
                )
            
            await view_callback(agent_request)
            # Return the AI response back to Streamlit
            return JSONResponse({"status": "success", "graph_response": "chat history deleted"}, status_code=200)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error occurred while deleting chat: {e}")
            raise HTTPException(status_code=400, detail=str(e))