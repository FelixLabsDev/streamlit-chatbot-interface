from agent_ti import Graph
from src.streamlit_view.view import View
from fastapi import FastAPI
import logging
import uvicorn

class Orchestrator():
    def __init__(self, *args, **kwargs):
        print('hi')
        self.app = FastAPI()  # Create the FastAPI app instance
        self.logger = logging.getLogger(__name__)

        self.model = Graph(clean=True, DEBUG=True)
        self.view = View(self.app, self.view_callback)
 

    # Callback function for the view which will typically call the model to generate a response
    # Supported message types: text, image, audio
    def view_callback(self, data_dict):
        print("Hello, you have reached the callback, it is printed below:")
        if data_dict["type"] == "unsupported":
            self.view.send_message(data_dict["chat_id"], "Oops, I don't understand that type of message!")
        elif data_dict["type"] == "delete_history":
            self.model.delete_chat_history()
            return
        elif data_dict["type"] == "delete_chat":
            thread_id = data_dict.get("chat_id")
            self.model.delete_entries_by_thread_id(thread_id)
            return

        if data_dict["type"] == "text":
            prompt = data_dict["text"]
            thread_id = data_dict.get("chat_id", 69)
            user_id = data_dict.get("name", "felix")

        model_response = self.model.invoke_graph(prompt, thread_id)
        return self.view.send_message(data_dict["chat_id"], model_response)
        
    def run(self, **kwargs):
        uvicorn.run(self.app, **kwargs)  # Use uvicorn to run the FastAPI app

    def run_view(self, title):
        self.view.run(title)
