from flask import Flask, request, jsonify
import subprocess
import threading
import requests
# from agent_ti import Graph






# Function to send user input to Flask
def send_input(user_input):
    try:
        # Sending the user input to Flask and receiving AI response
        response = requests.post("http://localhost:5000/input", json={"user_input": user_input})
        if response.status_code == 200:
            return response.json().get("ai_response", "No AI response")
        else:
            return "Error: Failed to get AI response"
    except requests.exceptions.RequestException as e:
        return f"Error: {str(e)}"




# app = Flask(__name__)

# # Mock AI response generation function (replace with actual AI model logic)
# def generate_ai_response(user_input):
#     response = graph.invoke_graph(user_input, "052", "eden")
#     return response
#     # return "testset"
    
# # Endpoint to receive user input and return AI-generated response
# @app.route('/input', methods=['POST'])
# def receive_input():
#     user_input = request.json.get('user_input')
    
#     if user_input:
#         # Generate AI response based on the user input
#         ai_response = generate_ai_response(user_input) 

#         # Return the AI response back to Streamlit
#         return jsonify({"status": "success", "ai_response": ai_response}), 200
    
#     return jsonify({"status": "error", "message": "No input received"}), 400


# # Function to run the Flask app
# def run_flask():
#     app.run(port=5000)

def run_streamlit():
    try:
        # Replace 'your_command' with the actual command you want to run
        command = ['streamlit', 'run', 'streamlit_chat_ui.py', '--', '--clean']  # Example: ['echo', 'Hello, World!']
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error occurred while running command: {e}")


def run():
    run_streamlit()

# if __name__ == '__main__':
#     # Start Flask app in a separate thread
#     flask_thread = threading.Thread(target=run_flask)
#     flask_thread.daemon = True  # This makes the Flask thread exit when the main program exits
#     flask_thread.start()

#     # Start Streamlit app
#     run_streamlit()