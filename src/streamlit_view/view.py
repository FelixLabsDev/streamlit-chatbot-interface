import os
from flask import Flask, request, jsonify
import subprocess
import threading
import requests
        
filename = os.path.join(os.path.dirname(__file__), 'streamlit_chat_ui.py')


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


# Function to delete chat history
def delete_history():
    try:
        # Sending the user input to Flask and receiving AI response
        response = requests.post("http://localhost:5000/delete_history")
        if response.status_code == 200:
            return response.json().get("flask_server_response", "history not deleted")
        else:
            return "Error: Failed to delete chat history"
    except requests.exceptions.RequestException as e:
        return f"Error: {str(e)}"

def run_streamlit():
    try:
        # Replace 'your_command' with the actual command you want to run
        command = ['streamlit', 'run', filename, '--', '--clean']  
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error occurred while running command: {e}")


def run():
    run_streamlit()
