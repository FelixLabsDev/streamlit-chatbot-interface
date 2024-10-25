from flask import Flask, request, jsonify
import subprocess
import threading
import requests
from agent_ti import Graph
from src.streamlit_view.view import run

app = Flask(__name__)

base_agent_path = r""
print("Loading new graph...")
graph = Graph(base_path=base_agent_path, clean=True)


# Mock AI response generation function (replace with actual AI model logic)
def generate_ai_response(user_input):
    response = graph.invoke_graph(user_input, "052", "eden")
    return response
    # return "testset"


# Endpoint to receive user input and return AI-generated response
@app.route("/input", methods=["POST"])
def receive_input():
    user_input = request.json.get("user_input")

    if user_input:
        # Generate AI response based on the user input
        ai_response = generate_ai_response(user_input)

        # Return the AI response back to Streamlit
        return jsonify({"status": "success", "ai_response": ai_response}), 200

    return jsonify({"status": "error", "message": "No input received"}), 400


# Endpoint to delete chat history
@app.route("/delete_history", methods=["POST"])
def delete_history():
    try:
        # Delete chat history
        graph.delete_chat_history()
        # Return the AI response back to Streamlit
        return jsonify(
            {"status": "success", "graph_response": "graph history deleted"}
        ), 200
    except Exception as e:
        print(f"Error occurred while deleting chat history: {e}")
        return jsonify({"status": "error", "Error": str(e)}), 400


# Function to run the Flask app
def run_flask():
    app.run(port=5000, debug=True, use_reloader=False)


def run_view():
    # Start Flask app in a separate thread
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True  # This makes the Flask thread exit when the main program exits
    flask_thread.start()

    # Start Streamlit app
    run("BOT NAME")


if __name__ == "__main__":
    run_view()
