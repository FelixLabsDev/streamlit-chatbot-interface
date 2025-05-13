from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import logging
from pydantic import ValidationError
import json
import os

# print("Current working directory:", os.getcwd())


# from orchestrator.utils.schemas import AgentRequest, AgentResponse, AgentRequestType, ResponseStatus
# Todo: Need to create own schemas for views, and combine views into one repo
from agent_ti.utils.schemas import AgentRequest, AgentRequestType, AgentResponse, RequestStatus

# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("view_configurations")

def define_endpoints(app, view_callback, get_response_callback):
    @app.post("/input")
    async def receive_input(request: Request):
        logger.info("Processing input request")
        try:
            data = await request.json()
            
            try:
                agent_request = AgentRequest.model_validate(data)
            except ValidationError as e:
                logger.error(f"Invalid request format: {e}")
                raise HTTPException(status_code=RequestStatus.ERROR.code, detail=f"Invalid request format: {str(e)}")
            
            await view_callback(agent_request)
            return JSONResponse({"status": RequestStatus.SUCCESS.value}, status_code=RequestStatus.SUCCESS.code)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error processing input: {e}", exc_info=True)
            raise HTTPException(status_code=RequestStatus.ERROR.code, detail=str(e))
        
    @app.get("/get_response")
    async def get_response(chat_id: str):
        try:
            agent_response = await get_response_callback(chat_id)
            if not agent_response:
                return JSONResponse({"status": RequestStatus.PENDING.value}, status_code=RequestStatus.SUCCESS.code)

            ai_response = json.loads(agent_response.model_dump_json())
            return JSONResponse({
                "status": agent_response.status.value, 
                "ai_response": ai_response
            }, status_code=agent_response.status.code)
        except Exception as e:
            logger.error(f"Error retrieving response: {e}")
            raise HTTPException(status_code=RequestStatus.ERROR.code, detail=str(e))

    @app.post("/delete_all_history")
    async def delete_history(request: Request):
        try:
            # Create an AgentRequest to delete all history
            agent_request = AgentRequest.delete_history()
            
            await view_callback(agent_request)
            return JSONResponse(
                {"status": "success", "message": "Chat history deleted"}, 
                status_code=RequestStatus.SUCCESS.code
            )
        except Exception as e:
            logger.error(f"Error deleting history: {e}")
            raise HTTPException(status_code=RequestStatus.ERROR.code, detail=str(e))
        
    @app.post("/delete_chat")
    async def delete_chat(request: Request):
        try:
            data = await request.json()
            
            agent_request = AgentRequest.model_validate(data)
            
            if not agent_request.chat_id:
                raise HTTPException(status_code=RequestStatus.ERROR.code, detail="No chat ID provided")
            
            # Create proper request using the class method
            agent_request = AgentRequest.delete_entries_by_chat_id(chat_id=str(agent_request.chat_id))
            
            await view_callback(agent_request)
            return JSONResponse(
                {"status": "success", "message": "Chat deleted"}, 
                status_code=RequestStatus.SUCCESS.code
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error deleting chat: {e}")
            raise HTTPException(status_code=RequestStatus.ERROR.code, detail=str(e))