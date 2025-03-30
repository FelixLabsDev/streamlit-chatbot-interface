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
import uuid
import random
import time


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
# from streamlit_view.view import send_input, delete_all_history, delete_chat, get_response

from streamlit_view.view import StreamlitView

#######################################################################################################
#######################################################################################################


load_dotenv()

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
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

def generate_short_uuid():
    # return uuid.uuid4().hex[:8]
    return str(random.randint(10000000, 99999999))

def load_chat_history():
    dir_path = "view_utils/.streamlit"
    
    # Create the directory if it doesn't exist
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
    
    with shelve.open(f"{dir_path}/chat_history") as db:
        return db.get("chats", {}), db.get("current_chat_id", None)


# Save chat history to shelve file
def save_chat_history(chats, current_chat_id):
    with shelve.open("view_utils/.streamlit/chat_history") as db:
        db["chats"] = chats
        db["current_chat_id"] = current_chat_id

def export_chat_to_text(chat_messages):
    export_text = ""
    for msg in chat_messages:
        sender = "human" if msg["role"] == "user" else "ai"
        export_text += f"{sender}: {msg['content']}\n\n"
    return export_text

if "chats" not in st.session_state or "current_chat_id" not in st.session_state:
    loaded_chats, loaded_current_id = load_chat_history()
    
    logger.info(f"Loaded chat history: {loaded_chats}, {loaded_current_id}")
    if not loaded_chats:
        new_chat_id = generate_short_uuid()
        loaded_chats = {
            new_chat_id: {
                "title": new_chat_id,
                "messages": []
            }
        }
        loaded_current_id = new_chat_id
    st.session_state.chats = loaded_chats
    st.session_state.current_chat_id = loaded_current_id

# Initialize waiting_response and ai_messages_queue in session state
if "waiting_response" not in st.session_state:
    st.session_state.waiting_response = False

# Add waiting_response_for and received_response_for tracking
if "waiting_response_for" not in st.session_state:
    st.session_state.waiting_response_for = {}

if "received_response_for" not in st.session_state:
    st.session_state.received_response_for = {}
    
if 'ai_messages_queue' not in st.session_state:
    st.session_state.ai_messages_queue = {}  # Queue for messages


st.session_state.ai_messages_queue[st.session_state.current_chat_id] = []

def delete_all_chat_histories():
    st.session_state.chats = {}
    new_chat_id = generate_short_uuid()
    st.session_state.chats[new_chat_id] = {
        "title": new_chat_id,
        "messages": []
    }
    st.session_state.current_chat_id = new_chat_id
    
    st.session_state.ai_messages_queue = {}
    st.session_state.waiting_response_for = {}
    st.session_state.received_response_for = {}
    
    st.session_state.waiting_response_for[st.session_state.current_chat_id] = set()
    st.session_state.received_response_for[st.session_state.current_chat_id] = set()
    save_chat_history(st.session_state.chats, st.session_state.current_chat_id)
    StreamlitView.delete_all_history()

with st.sidebar:
    if st.button("New Chat"):
        new_chat_id = generate_short_uuid()
        st.session_state.chats[new_chat_id] = {
            "title": new_chat_id,
            "messages": []
        }
        st.session_state.current_chat_id = new_chat_id
        save_chat_history(st.session_state.chats, st.session_state.current_chat_id)
        st.rerun()
    
    st.write("---")
    st.subheader("Chat Sessions")
    
    for chat_id in list(st.session_state.chats.keys()):
        chat = st.session_state.chats[chat_id]
        col1, col2 = st.columns([0.7, 0.3])
        
        with col1:
            btn_type = "primary" if chat_id == st.session_state.current_chat_id else "secondary"
            if st.button(
                chat["title"],
                key=f"title_{chat_id}",
                use_container_width=True,
                type=btn_type
            ):
                st.session_state.current_chat_id = chat_id
                save_chat_history(st.session_state.chats, st.session_state.current_chat_id)
                st.rerun()
        
        with col2:
            with st.popover("⋮"):
                new_title = st.text_input(
                    "Rename chat",
                    value=chat["title"],
                    key=f"rename_{chat_id}"
                )
                if new_title != chat["title"]:
                    st.session_state.chats[chat_id]["title"] = new_title
                    save_chat_history(st.session_state.chats, st.session_state.current_chat_id)
                
                export_text = export_chat_to_text(chat["messages"])
                st.download_button(
                    label="Export to TXT",
                    data=export_text,
                    file_name=f"chat_{chat_id}.txt",
                    mime="text/plain",
                    key=f"export_{chat_id}"
                )
                
                if st.button(
                    "Delete",
                    key=f"delete_{chat_id}",
                    type="primary"
                ):
                    del st.session_state.chats[chat_id]
                    StreamlitView.delete_chat(chat_id)
                    if st.session_state.current_chat_id == chat_id:
                        if len(st.session_state.chats) > 0:
                            st.session_state.current_chat_id = next(iter(st.session_state.chats.keys()))
                        else:
                            new_id = generate_short_uuid()
                            st.session_state.chats[new_id] = {"title": new_id, "messages": []}
                            st.session_state.current_chat_id = new_id
                    save_chat_history(st.session_state.chats, st.session_state.current_chat_id)
                    st.rerun()
    
    st.write("---")
    if st.button("Delete All Chats", type="secondary"):
        delete_all_chat_histories()
        st.rerun()

def waiting_response(chat_id):
    return st.session_state.waiting_response_for.get(chat_id, set())

def received_response(chat_id):
    return st.session_state.received_response_for.get(chat_id, set())


def render_ai_response():
    current_chat_id = st.session_state.current_chat_id

    logger.info('Render AI response')
    logger.debug(f'st.session_state.waiting_response_for: {st.session_state.waiting_response_for}')
    logger.debug(f'st.session_state.received_response_for: {st.session_state.received_response_for}')
   
    
    # if not received_response(current_chat_id):
    #     return 
    
    logger.info(f'st.session_state.ai_messages_queue: {st.session_state.ai_messages_queue}')
    for msg in st.session_state.ai_messages_queue[current_chat_id]:
        st.chat_message("assistant", avatar="🤖").write(msg)
    
    waiting = waiting_response(current_chat_id)
    received = received_response(current_chat_id)
    st.session_state.waiting_response_for[current_chat_id] = waiting - received
    st.session_state.received_response_for[current_chat_id] = received - waiting
    
    logger.info('Response sent successfully')
    logger.debug(f'st.session_state.waiting_response_for: {st.session_state.waiting_response_for}')
    logger.debug(f'st.session_state.received_response_for: {st.session_state.received_response_for}')
    
    

def check_ai_response():
      
    current_chat_id = st.session_state.current_chat_id

    try:
        # Fetch messages from backend - now returns AgentResponse
        agent_response = StreamlitView.get_response(current_chat_id)
        logger.info(f"Response: {agent_response}")
        
        # Check the status of the AgentResponse
        if agent_response.is_error():
            # Error occurred
            logger.error(f"Error response: {agent_response.metadata.values.get('error', 'Unknown error')}")
            return
            
        if agent_response.is_pending():
            # Response is pending
            logger.info("Response is pending")
            return
        
        # Process successful AgentResponse
        if agent_response.is_success():
            current_chat = st.session_state.chats[current_chat_id]
            ai_message = agent_response.message
            
            # Process metadata if available
            if agent_response.metadata and hasattr(agent_response.metadata, 'values'):
                metadata = agent_response.metadata.values
                
                # Process message_ids in response metadata
                if "message_id" in metadata:
                    message_ids = metadata["message_id"]
                    
                    # Initialize received_response_for if needed
                    if current_chat_id not in st.session_state.received_response_for:
                        st.session_state.received_response_for[current_chat_id] = set()
                    
                    # Add message_ids to received_response_for set
                    for msg_id in message_ids:
                        st.session_state.received_response_for[current_chat_id].add(msg_id)
                        logger.info(f"Added message_id {msg_id} to received_response_for[{current_chat_id}]")
            
            # Add the message to the queue
            st.session_state.ai_messages_queue[current_chat_id].append(ai_message)
            logger.info(f"AI response: {ai_message}")
            current_chat["messages"].append({"role": "assistant", "content": ai_message})
            logger.info(f"AI response for chat {current_chat_id}: {ai_message}")
            save_chat_history(st.session_state.chats, st.session_state.current_chat_id)

        
    except Exception as e:
        logger.error(f"Error fetching messages: {e}")
        

@st.fragment(run_every=4)
def get_ai_messages():
    render_ai_response()
    if not waiting_response(st.session_state.current_chat_id):
        return
    
    check_ai_response()


# Display current chat
current_chat = st.session_state.chats[st.session_state.current_chat_id]
for message in current_chat["messages"]:
    avatar = USER_AVATAR if message["role"] == "user" else BOT_AVATAR
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])

# Process user input
if prompt := st.chat_input("How can I help?"):
    
    current_chat["messages"].append({"role": "user", "content": prompt})
    
    with st.chat_message("user", avatar=USER_AVATAR):
        st.markdown(prompt)

    # Send the input and get message_id
    logger.info(f"Sending input to the model: {prompt}, {st.session_state.current_chat_id}")
    message_id = str(uuid.uuid4())
    if st.session_state.current_chat_id not in st.session_state.waiting_response_for:
        st.session_state.waiting_response_for[st.session_state.current_chat_id] = set()
    st.session_state.waiting_response_for[st.session_state.current_chat_id].add(message_id)
    logger.info(f"Added message_id {message_id} to waiting_response_for[{st.session_state.current_chat_id}]")
    
    response = StreamlitView.send_input(prompt, st.session_state.current_chat_id, message_id)



# Save chat history
save_chat_history(st.session_state.chats, st.session_state.current_chat_id)

# Run fragments to check and render responses
get_ai_messages()
