from flask import Flask, request, jsonify
import subprocess
import threading
import requests
from agent_ti import Graph
from src.streamlit_view.view import run

app = Flask(__name__)

base_agent_path = r""
graph = Graph(base_path=base_agent_path, clean=True)

# Mock AI response generation function (replace with actual AI model logic)
def generate_ai_response(user_input):
    response = graph.invoke_graph(user_input, "052", "eden")
    return response
    # return "testset"
    
# Endpoint to receive user input and return AI-generated response
@app.route('/input', methods=['POST'])
def receive_input():
    user_input = request.json.get('user_input')
    
    if user_input:
        # Generate AI response based on the user input
        ai_response = generate_ai_response(user_input) 

        # Return the AI response back to Streamlit
        return jsonify({"status": "success", "ai_response": ai_response}), 200
    
    return jsonify({"status": "error", "message": "No input received"}), 400

# Function to run the Flask app
def run_flask():
    app.run(port=5000)

def run_view():
    # Start Flask app in a separate thread
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True  # This makes the Flask thread exit when the main program exits
    flask_thread.start()

    # Start Streamlit app
    run()

if __name__ == '__main__':
    run_view()