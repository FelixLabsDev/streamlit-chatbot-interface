import streamlit as st
from dotenv import load_dotenv 
import os
import shelve 
import argparse
import sys
from pathlib import Path
import logging
import uuid
import random
import time

# Add the project root directory to Python path
root_dir = str(Path(__file__).parent.parent)
if root_dir not in sys.path:
    sys.path.append(root_dir)

# Import the StreamlitView
from streamlit_view.view import StreamlitView

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Argument parser to handle command-line arguments
parser = argparse.ArgumentParser(description="Streamlit Single Chat Interface")
parser.add_argument('--clean', action='store_true', help="Delete chat history before startup")
parser.add_argument('--title', type=str, default="Streamlit Chat", help="Set the title of the app")
args = parser.parse_args()

st.title(args.title)
logger.info("Streamlit single chat app has started")

USER_AVATAR = "👤"
BOT_AVATAR = "🤖"

# Clear the queue after rendering
st.session_state.ai_messages_queue = []

def generate_chat_id():
    """Generate a unique ID for the chat session."""
    return str(random.randint(10000000, 99999999))


def load_chat_history():
    """Load chat history from disk."""
    dir_path = "view_utils/.streamlit"
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
    
    with shelve.open(f"{dir_path}/single_chat_history") as db:
        chat_id = db.get("chat_id", None)
        messages = db.get("messages", [])
        return chat_id, messages


def save_chat_history(chat_id: str, messages: list):
    """Save chat history to disk."""
    with shelve.open("view_utils/.streamlit/single_chat_history") as db:
        db["chat_id"] = chat_id
        db["messages"] = messages


def export_chat_to_text(messages: list) -> str:
    """Convert chat messages to exportable text format."""
    export_text = ""
    for msg in messages:
        sender = "human" if msg["role"] == "user" else "ai"
        export_text += f"{sender}: {msg['content']}\n\n"
    return export_text


def clear_chat_history():
    """Clear the chat history and create a new chat session."""
    # Generate a new chat ID
    chat_id = generate_chat_id()
    st.session_state.chat_id = chat_id
    st.session_state.messages = []
    
    # Reset message queue and tracking sets
    st.session_state.ai_messages_queue = []
    
    # Reset the tracking sets
    st.session_state.waiting_response_for = set()
    st.session_state.received_response_for = set()
    
    # Save empty history
    save_chat_history(chat_id, [])
    
    # Tell the backend to delete all history
    StreamlitView.delete_all_history()
    
    logger.info(f"Chat history cleared, new chat ID: {chat_id}")


def waiting_response():
    """Get the set of message IDs that are waiting for a response."""
    return st.session_state.waiting_response_for


def received_response():
    """Get the set of message IDs that have received a response."""
    return st.session_state.received_response_for


# Initialize session state
if "chat_id" not in st.session_state or "messages" not in st.session_state:
    loaded_chat_id, loaded_messages = load_chat_history()
    if not loaded_chat_id:
        # Create a new chat session
        loaded_chat_id = generate_chat_id()
        loaded_messages = []
    st.session_state.chat_id = loaded_chat_id
    st.session_state.messages = loaded_messages

# Initialize waiting_response and ai_messages_queue in session state
if "waiting_response_for" not in st.session_state:
    st.session_state.waiting_response_for = set()

if "received_response_for" not in st.session_state:
    st.session_state.received_response_for = set()
    
if 'ai_messages_queue' not in st.session_state:
    st.session_state.ai_messages_queue = []  # Queue for messages

# Display current chat ID under title
st.caption(f"Chat ID: {st.session_state.chat_id}")

# Sidebar with only the Clear History button
with st.sidebar:
    st.subheader("Chat Options")
    if st.button("Clear History"):
        clear_chat_history()
        st.rerun()
    
    # Optional: Add export functionality
    export_text = export_chat_to_text(st.session_state.messages)
    st.download_button(
        label="Export to TXT",
        data=export_text,
        file_name=f"chat_{st.session_state.chat_id}.txt",
        mime="text/plain"
    )

def render_ai_response():
    """Render any queued AI responses."""
    logger.info('Render AI response')
    logger.debug(f'waiting_response_for: {st.session_state.waiting_response_for}')
    logger.debug(f'received_response_for: {st.session_state.received_response_for}')
   
    logger.info(f'ai_messages_queue: {st.session_state.ai_messages_queue}')
    for msg in st.session_state.ai_messages_queue:
        st.chat_message("assistant", avatar=BOT_AVATAR).write(msg)
    

    # Update the tracking sets
    waiting = waiting_response()
    received = received_response()
    st.session_state.waiting_response_for = waiting - received
    st.session_state.received_response_for = received - waiting
    
    logger.info('Response rendering completed')
    logger.debug(f'waiting_response_for: {st.session_state.waiting_response_for}')
    logger.debug(f'received_response_for: {st.session_state.received_response_for}')

def check_ai_response():
    try:
        # Fetch messages from backend - returns AgentResponse
        agent_response = StreamlitView.get_response(st.session_state.chat_id)
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
            ai_message = agent_response.message
            
            # Process metadata if available
            if agent_response.metadata and hasattr(agent_response.metadata, 'values'):
                metadata = agent_response.metadata.values
                
                # Process message_ids in response metadata
                if "message_id" in metadata:
                    message_ids = metadata["message_id"]
                    
                    # Add message_ids to received_response_for set
                    for msg_id in message_ids:
                        st.session_state.received_response_for.add(msg_id)
                        logger.info(f"Added message_id {msg_id} to received_response_for")
            
            # Add the message to the queue
            st.session_state.ai_messages_queue.append(ai_message)
            logger.info(f"AI response: {ai_message}")
            st.session_state.messages.append({"role": "assistant", "content": ai_message})
            logger.info(f"AI response for chat {st.session_state.chat_id}: {ai_message}")
            
            # Save chat history after receiving AI response
            save_chat_history(st.session_state.chat_id, st.session_state.messages)
        
    except Exception as e:
        logger.error(f"Error fetching messages: {e}")

@st.fragment(run_every=4)
def get_ai_messages():
    render_ai_response()
    if not waiting_response():
        return
    
    check_ai_response()

# Display message history
for message in st.session_state.messages:
    avatar = USER_AVATAR if message["role"] == "user" else BOT_AVATAR
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])

# Process user input
if prompt := st.chat_input("How can I help?"):
    # Add user message to history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Display the user message
    with st.chat_message("user", avatar=USER_AVATAR):
        st.markdown(prompt)

    # Send the input and get message_id
    logger.info(f"Sending input to the model: {prompt}, {st.session_state.chat_id}")
    message_id = str(uuid.uuid4())
    st.session_state.waiting_response_for.add(message_id)
    logger.info(f"Added message_id {message_id} to waiting_response_for")
    
    # Send input to the model
    response = StreamlitView.send_input(prompt, st.session_state.chat_id, message_id)


# Save chat history
save_chat_history(st.session_state.chat_id, st.session_state.messages)

# Run fragments to check and render responses
get_ai_messages()
