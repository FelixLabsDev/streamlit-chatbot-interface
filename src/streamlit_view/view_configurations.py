from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def define_endpoints(app, view_callback, get_response_callback):
    logger.info("inside define_endpoints")
    # Endpoint to receive user input and store in Redis
    @app.post("/input")
    async def receive_input(request: Request):
        logger.info("inside receive_input")
        data = await request.json()
        user_input = data.get("user_input")
        user_id = data.get("user_id")

        if user_input:
            # Store user input in Redis
            data_dict = {
                "user_id": user_id,
                "type": "text",
                "chat_id": "69420",
                "text": user_input
            }
            await view_callback(data_dict)
            return JSONResponse({"status": "success"}, status_code=200)

        raise HTTPException(status_code=400, detail="No input received")

    # Endpoint to fetch AI response from Redis
    @app.get("/get_response")
    async def get_response(user_id: str):
        # Fetch AI response from Redis
        try:
            ai_response = await get_response_callback(user_id)
            if ai_response:
                return JSONResponse({"status": "success", "ai_response": ai_response}, status_code=200)
            return JSONResponse({"status": "pending"}, status_code=200)
        except Exception as e:
            logger.error(f"Error fetching AI response: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    # Endpoint to delete chat history
    @app.post("/delete_history")
    async def delete_history():
        try:
            # Delete chat history
            data_dict = {
                "type": "delete_history", 
                "chat_id": "69420"
            }
            await view_callback(data_dict)
            # Return the AI response back to Streamlit
            return JSONResponse({"status": "success", "graph_response": "graph history deleted"}, status_code=200)
        except Exception as e:
            print(f"Error occurred while deleting chat history: {e}")
            raise HTTPException(status_code=400, detail=str(e))

    # Endpoint to delete all chat history
    @app.post("/delete_all_history")
    async def delete_history():
        try:
            # Delete all chat history
            data_dict = {
                "type": "delete_history", 
            }
            view_callback(data_dict)
            # Return the AI response back to Streamlit
            return JSONResponse({"status": "success", "graph_response": "graph history deleted"}, status_code=200)
        except Exception as e:
            print(f"Error occurred while deleting chat history: {e}")
            raise HTTPException(status_code=400, detail=str(e))
        
    # Endpoint to delete chat history by chat ID
    @app.post("/delete_chat")
    async def delete_chat(request: Request):
        data = await request.json()
        chat_id = data.get("chat_id")
        if chat_id:
            # Delete chat history by chat ID
            data_dict = {
                "type": "delete_chat", 
                "chat_id": chat_id
            }
            view_callback(data_dict)
            # Return the AI response back to Streamlit
            return JSONResponse({"status": "success", "graph_response": "chat history deleted"}, status_code=200)
        raise HTTPException(status_code=400, detail="No chat ID received")
