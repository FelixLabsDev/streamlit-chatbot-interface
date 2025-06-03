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
import csv
import io

# Clear any cached fragments to prevent polling
st.cache_data.clear()
st.cache_resource.clear()

# Add the project root directory to Python path
root_dir = str(Path(__file__).parent.parent)
if root_dir not in sys.path:
    sys.path.append(root_dir)

# Import the StreamlitView
from streamlit_view.view import StreamlitView

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Argument parser to handle command-line arguments
parser = argparse.ArgumentParser(description="Streamlit Single Chat Interface")
parser.add_argument(
    "--clean", action="store_true", help="Delete chat history before startup"
)
parser.add_argument(
    "--title", type=str, default="Streamlit Chat", help="Set the title of the app"
)
args = parser.parse_args()

st.title(args.title)
logger.info("Streamlit single chat app has started")

USER_AVATAR = "👤"
BOT_AVATAR = "🤖"


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


def export_chat_to_csv(messages: list) -> str:
    """Convert chat messages to CSV format with sender and message columns."""
    output = io.StringIO()
    writer = csv.writer(output)

    # Write header
    writer.writerow(["sender", "message"])

    # Write messages
    for msg in messages:
        sender = "human" if msg["role"] == "user" else "ai"
        writer.writerow([sender, msg["content"]])

    return output.getvalue()


def clear_chat_history():
    """Clear the chat history and create a new chat session."""
    # Generate a new chat ID
    chat_id = generate_chat_id()
    st.session_state.chat_id = chat_id
    st.session_state.messages = []

    # Save empty history
    save_chat_history(chat_id, [])

    # Tell the backend to delete all history
    StreamlitView.delete_all_history()

    logger.info(f"Chat history cleared, new chat ID: {chat_id}")


def check_for_ai_response():
    """Check for AI response and update chat if found."""
    try:
        # Fetch messages from backend - returns AgentResponse
        agent_response = StreamlitView.get_response(st.session_state.chat_id)
        logger.info(f"Response: {agent_response}")

        # Check the status of the AgentResponse
        if agent_response.is_error:
            # Error occurred
            logger.error(
                f"Error response: {agent_response.metadata.values.get('error', 'Unknown error')}"
            )
            return False

        if agent_response.is_pending:
            # Response is still pending
            logger.info("Response is pending")
            return False

        # Process successful AgentResponse
        if agent_response.is_success:
            ai_message = agent_response.message

            # Add the AI response to the chat
            st.session_state.messages.append(
                {"role": "assistant", "content": ai_message}
            )
            logger.info(
                f"AI response for chat {st.session_state.chat_id}: {ai_message}"
            )

            # Save chat history after receiving AI response
            save_chat_history(st.session_state.chat_id, st.session_state.messages)

            return True

    except Exception as e:
        logger.error(f"Error fetching messages: {e}")
        return False


# Initialize session state
if "chat_id" not in st.session_state or "messages" not in st.session_state:
    loaded_chat_id, loaded_messages = load_chat_history()
    if not loaded_chat_id:
        # Create a new chat session
        loaded_chat_id = generate_chat_id()
        loaded_messages = []
    st.session_state.chat_id = loaded_chat_id
    st.session_state.messages = loaded_messages

# Display current chat ID under title
st.caption(f"Chat ID: {st.session_state.chat_id}")

# Sidebar with only the Clear History button
with st.sidebar:
    st.subheader("Chat Options")
    if st.button("Clear History"):
        clear_chat_history()
        st.rerun()

    # Export functionality
    export_text = export_chat_to_text(st.session_state.messages)
    st.download_button(
        label="Export to TXT",
        data=export_text,
        file_name=f"chat_{st.session_state.chat_id}.txt",
        mime="text/plain",
    )

    export_csv = export_chat_to_csv(st.session_state.messages)
    st.download_button(
        label="Export to CSV",
        data=export_csv,
        file_name=f"chat_{st.session_state.chat_id}.csv",
        mime="text/csv",
    )

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

    # Send the input
    logger.info(f"Sending input to the model: {prompt}, {st.session_state.chat_id}")
    message_id = str(uuid.uuid4())

    # Send input to the model
    response = StreamlitView.send_input(prompt, st.session_state.chat_id, message_id)

    # Save chat history
    save_chat_history(st.session_state.chat_id, st.session_state.messages)

# Check for AI response
response_received = check_for_ai_response()
if response_received:
    st.rerun()


# Auto-refresh to check for responses every 2 seconds
@st.fragment(run_every=2)
def auto_check_responses():
    response_received = check_for_ai_response()
    if response_received:
        st.rerun()


auto_check_responses()

# Save chat history
save_chat_history(st.session_state.chat_id, st.session_state.messages)
