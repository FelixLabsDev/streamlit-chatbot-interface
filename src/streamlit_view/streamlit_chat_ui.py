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
if 'user_id' not in st.session_state:
    st.session_state.user_id = f"user_{int(time.time())}"  # Or use any unique mechanism

user_id = st.session_state.user_id

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
    # st.session_state.messages = load_chat_history()
    st.session_state.messages = []




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
def chat_fragment():
    user_id = st.session_state.user_id
    logger.info(f"inside chat_fragment. User ID: {user_id}")
    
    current_time = datetime.datetime.now().strftime("%H:%M:%S")
    st.write(f"🕒 Текущее время: {current_time}")
    
    try:
        # Fetch messages from Redis
        response = get_response(user_id)
        logger.debug(f"Response: {response.json()}")
        if response.status_code == 200:
            data = response.json()
            if data['status'] == 'success':
                display_chat_history()
                ai_response = data['ai_response']
                logger.debug(f"AI response: {ai_response}")
                with st.chat_message("assistant", avatar=BOT_AVATAR):
                    st.markdown(ai_response)
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

    with st.chat_message("assistant", avatar=BOT_AVATAR):
        message_placeholder = st.empty()
        full_response = send_input(prompt, user_id=st.session_state.user_id)


        # message_placeholder.markdown(full_response)
    # st.session_state.messages.append({"role": "assistant", "content": full_response})

st.write(st.session_state)

chat_fragment()
# Save chat history after each interaction
save_chat_history(st.session_state.messages)

# streamlit run streamlit_chat_ui.py -- --clean
