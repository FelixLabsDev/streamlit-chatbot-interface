import streamlit as st
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
from agent_ti.utils.schemas import AgentResponse

# Clear any cached fragments to prevent polling
st.cache_data.clear()
st.cache_resource.clear()

# Add the project root directory to Python path
root_dir = str(Path(__file__).parent.parent)
if root_dir not in sys.path:
    sys.path.append(root_dir)

# Import the StreamlitView
from streamlit_view.view import StreamlitView


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
    dir_path = "data/chats/.streamlit"
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)

    with shelve.open(f"{dir_path}/single_chat_history") as db:
        chat_id = db.get("chat_id", None)
        messages = db.get("messages", [])
        return chat_id, messages


def save_chat_history(chat_id: str, messages: list):
    """Save chat history to disk."""
    with shelve.open("data/chats/.streamlit/single_chat_history") as db:
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

    # Send the input and get immediate response
    logger.info(f"Sending input to the model: {prompt}, {st.session_state.chat_id}")
    message_id = str(uuid.uuid4())

    # Get response directly from agent
    with st.spinner("Thinking..."):
        agent_response = StreamlitView.send_message(
            prompt,
            st.session_state.chat_id,
            message_id,
        )

    # Process the response
    if isinstance(agent_response, AgentResponse):
        # Add the AI message to chat history
        st.session_state.messages.append(
            {"role": "assistant", "content": agent_response.message}
        )
        logger.info(
            f"AI response for chat {st.session_state.chat_id}: {agent_response.message}"
        )

        # Display the AI response
        with st.chat_message("assistant", avatar=BOT_AVATAR):
            st.markdown(agent_response.message)
    else:
        # Handle error string
        error_msg = str(agent_response)
        logger.error(f"Error response: {error_msg}")
        st.error(f"Error: {error_msg}")

    # Save chat history
    save_chat_history(st.session_state.chat_id, st.session_state.messages)

# Save chat history at the end
save_chat_history(st.session_state.chat_id, st.session_state.messages)
