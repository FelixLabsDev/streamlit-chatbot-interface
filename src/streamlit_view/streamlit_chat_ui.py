# from openai import OpenAI
import time
import datetime
import streamlit as st
from dotenv import load_dotenv
import os
import shelve
import argparse
import sys
import os
from pathlib import Path
import logging
#######################################################################################################
#######################################################################################################

#######################################
### Uncomment below to work locally ###
#######################################

# # Add the project root directory to Python path
# root_dir = str(Path(__file__).parent.parent.parent)
# if root_dir not in sys.path:
#     sys.path.append(root_dir)

# # Now your imports should work
# from src.streamlit_view.view import send_input, delete_history


############################################
### Uncomment below to work as a package ###
############################################

# Add the project root directory to Python path
root_dir = str(Path(__file__).parent.parent)
if root_dir not in sys.path:
    sys.path.append(root_dir)

# Now your imports should work
from streamlit_view.view import send_input, delete_history, get_response

#######################################################################################################
#######################################################################################################


load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Argument parser to handle command-line arguments
parser = argparse.ArgumentParser(description="Streamlit Chatbot Interface")
parser.add_argument('--clean', action='store_true', help="Delete chat history before startup")
parser.add_argument('--title', type=str, default="Streamlit Chatbot Interface", help="Set the title of the app")
args = parser.parse_args()


# Use the title argument to set the title of the Streamlit app
st.title(args.title)

logger.info("Streamlit app has started")

USER_AVATAR = "👤"
BOT_AVATAR = "🤖"
# client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# --- User Identification ---
# On first run, assign a unique ID to the session.
if 'thread_id' not in st.session_state:
    st.session_state.thread_id = "69420"  # Or use any unique mechanism

thread_id = st.session_state.thread_id

# st.write("### Your User ID:")
# st.write(st.session_state.user_id)


# Ensure openai_model is initialized in session state
# if "openai_model" not in st.session_state:
#     st.session_state["openai_model"] = "gpt-4o-mini"


# Load chat history from shelve file
def load_chat_history():
    dir_path = "view/.streamlit"
    
    # Create the directory if it doesn't exist
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
    
    with shelve.open(f"{dir_path}/chat_history") as db:
        return db.get("messages", [])


# Save chat history to shelve file
def save_chat_history(messages):
    with shelve.open("view/.streamlit/chat_history") as db:
        db["messages"] = messages


# Initialize or load chat history
if "messages" not in st.session_state:
    st.session_state.messages = load_chat_history()
    st.session_state.messages = []

if "waiting_response" not in st.session_state:
    st.session_state.waiting_response = False  # Indicates if bot response is pending
    
st.session_state.ai_messages_queue = []  # Queue for messages




def delete_chat_history():
    # delete history locally (streamlit)
    st.session_state.messages = []
    save_chat_history([])
    # delete history from the server (agent)
    delete_history() 

# Clean history before loading if --clean argument is passed
if args.clean and "clean" not in st.session_state:
    st.session_state.clean = True 
    delete_chat_history()

# Sidebar with a button to delete chat history
with st.sidebar:
    if st.button("Delete Chat History"):
        delete_chat_history()


def display_chat_history():
    # Display chat messages
    for message in st.session_state.messages:
        avatar = USER_AVATAR if message["role"] == "user" else BOT_AVATAR
        with st.chat_message(message["role"], avatar=avatar):
            st.markdown(message["content"])



@st.fragment(run_every=1)
def render_ai_response():
    logger.info(f'st.session_state.ai_messages_queue: {st.session_state.ai_messages_queue}')
    for msg in st.session_state.ai_messages_queue:
        st.chat_message("assistant", avatar="🤖").write(msg)
    logger.info('Response sent successfully')


@st.fragment(run_every=2)
def check_ai_response():
    if not st.session_state.waiting_response:
        return
      
    thread_id = st.session_state.thread_id

    try:
        # Fetch messages from Redis
        response = get_response(thread_id)
        logger.info(f"Response: {response}")
        logger.info(f"Response content: {response.content}")
        if response.status_code == 200:
            data = response.json()
            if data['status'] == 'success':
                ai_response = data['ai_response']
                st.session_state.ai_messages_queue.append(ai_response)
                logger.info(f"AI response: {ai_response}")
                st.session_state.messages.append({"role": "assistant", "content": ai_response})
                logger.info(f"AI response Added: {ai_response}")
            elif data['status'] == 'pending':
                # No messages available yet
                pass
        else:
            logger.error(f"Unexpected response status: {response.status_code}")
            st.warning("No messages available yet")
    except Exception as e:
        logger.error(f"Error fetching messages from Redis: {e}")
    


display_chat_history()



# Main chat interface
if prompt := st.chat_input("How can I help?"):
    logger.info(f"User input: {prompt}")
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar=USER_AVATAR):
        st.markdown(prompt)

    # message_placeholder = st.empty()
    full_response = send_input(prompt, thread_id=st.session_state.thread_id)
    st.session_state.waiting_response = True  # Indicate we expect a response



render_ai_response()
check_ai_response()
# Save chat history after each interaction
save_chat_history(st.session_state.messages)

# streamlit run streamlit_chat_ui.py -- --clean
