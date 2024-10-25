from controller.controller import Orchestrator
import logging
import os
import subprocess

if __name__ == "__main__":
    orchestrator = Orchestrator()

    filename = os.path.join('src','streamlit_view', 'streamlit_chat_ui.py')
    command = ['streamlit', 'run', filename, '--', '--clean', '--title', "Streamlit Chatbot TEST Interface"]  
    subprocess.run(command, check=True)
    logging.info("Flask app started")
    orchestrator.run(port=5050, host="0.0.0.0", debug=True)
