# from openai import OpenAI
import time
import datetime
import streamlit as st
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
import csv
import io
from agent_ti.utils.schemas import AgentResponse

# Clear any cached fragments to prevent polling
st.cache_data.clear()
st.cache_resource.clear()

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


# Configure logging
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Argument parser to handle command-line arguments
parser = argparse.ArgumentParser(description="Streamlit Chatbot Interface")
parser.add_argument(
    "--clean", action="store_true", help="Delete chat history before startup"
)
parser.add_argument(
    "--title",
    type=str,
    default="Streamlit Chatbot Interface",
    help="Set the title of the app",
)
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
    dir_path = "data/.streamlit"

    # Create the directory if it doesn't exist
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)

    with shelve.open(f"{dir_path}/chat_history") as db:
        return db.get("chats", {}), db.get("current_chat_id", None)


# Save chat history to shelve file
def save_chat_history(chats, current_chat_id):
    with shelve.open("data/.streamlit/chat_history") as db:
        db["chats"] = chats
        db["current_chat_id"] = current_chat_id


def export_chat_to_text(chat_messages):
    export_text = ""
    for msg in chat_messages:
        sender = "human" if msg["role"] == "user" else "ai"
        export_text += f"{sender}: {msg['content']}\n\n"
    return export_text


def export_chat_to_csv(chat_messages):
    """Convert chat messages to CSV format with sender and message columns."""
    output = io.StringIO()
    writer = csv.writer(output)

    # Write header
    writer.writerow(["sender", "message"])

    # Write messages
    for msg in chat_messages:
        sender = "human" if msg["role"] == "user" else "ai"
        writer.writerow([sender, msg["content"]])

    return output.getvalue()


# Initialize session state
if "chats" not in st.session_state or "current_chat_id" not in st.session_state:
    loaded_chats, loaded_current_id = load_chat_history()

    logger.info(f"Loaded chat history: {loaded_chats}, {loaded_current_id}")
    if not loaded_chats:
        new_chat_id = generate_short_uuid()
        loaded_chats = {new_chat_id: {"title": new_chat_id, "messages": []}}
        loaded_current_id = new_chat_id
    st.session_state.chats = loaded_chats
    st.session_state.current_chat_id = loaded_current_id


def delete_all_chat_histories():
    st.session_state.chats = {}
    new_chat_id = generate_short_uuid()
    st.session_state.chats[new_chat_id] = {"title": new_chat_id, "messages": []}
    st.session_state.current_chat_id = new_chat_id

    save_chat_history(st.session_state.chats, st.session_state.current_chat_id)
    StreamlitView.delete_all_history()

with st.sidebar:
    if st.button("New Chat"):
        new_chat_id = generate_short_uuid()
        st.session_state.chats[new_chat_id] = {"title": new_chat_id, "messages": []}
        st.session_state.current_chat_id = new_chat_id
        save_chat_history(st.session_state.chats, st.session_state.current_chat_id)
        st.rerun()

    st.write("---")
    st.subheader("Chat Sessions")

    for chat_id in list(st.session_state.chats.keys()):
        chat = st.session_state.chats[chat_id]
        col1, col2 = st.columns([0.7, 0.3])

        with col1:
            btn_type = (
                "primary"
                if chat_id == st.session_state.current_chat_id
                else "secondary"
            )
            if st.button(
                chat["title"],
                key=f"title_{chat_id}",
                use_container_width=True,
                type=btn_type,
            ):
                st.session_state.current_chat_id = chat_id
                save_chat_history(
                    st.session_state.chats, st.session_state.current_chat_id
                )
                st.rerun()

        with col2:
            with st.popover("⋮"):
                new_title = st.text_input(
                    "Rename chat", value=chat["title"], key=f"rename_{chat_id}"
                )
                if new_title != chat["title"]:
                    st.session_state.chats[chat_id]["title"] = new_title
                    save_chat_history(
                        st.session_state.chats, st.session_state.current_chat_id
                    )

                export_text = export_chat_to_text(chat["messages"])
                st.download_button(
                    label="Export to TXT",
                    data=export_text,
                    file_name=f"chat_{chat_id}.txt",
                    mime="text/plain",
                    key=f"export_{chat_id}",
                )

                export_csv = export_chat_to_csv(chat["messages"])
                st.download_button(
                    label="Export to CSV",
                    data=export_csv,
                    file_name=f"chat_{chat_id}.csv",
                    mime="text/csv",
                    key=f"export_csv_{chat_id}",
                )

                if st.button("Delete", key=f"delete_{chat_id}", type="primary"):
                    del st.session_state.chats[chat_id]
                    StreamlitView.delete_chat(chat_id)
                    if st.session_state.current_chat_id == chat_id:
                        if len(st.session_state.chats) > 0:
                            st.session_state.current_chat_id = next(
                                iter(st.session_state.chats.keys())
                            )
                        else:
                            new_id = generate_short_uuid()
                            st.session_state.chats[new_id] = {
                                "title": new_id,
                                "messages": [],
                            }
                            st.session_state.current_chat_id = new_id
                    save_chat_history(
                        st.session_state.chats, st.session_state.current_chat_id
                    )
                    st.rerun()

    st.write("---")
    if st.button("Delete All Chats", type="secondary"):
        delete_all_chat_histories()
        st.rerun()

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

    # Send the input and get immediate response
    logger.info(
        f"Sending input to the model: {prompt}, {st.session_state.current_chat_id}"
    )
    message_id = str(uuid.uuid4())

    # Get response directly from agent
    with st.spinner("Thinking..."):
        agent_response = StreamlitView.send_message(
            prompt,
            st.session_state.current_chat_id,
            message_id,
        )

    # Process the response
    if isinstance(agent_response, AgentResponse):
        # Add the AI message to chat history
        current_chat["messages"].append(
            {"role": "assistant", "content": agent_response.message}
        )
        logger.info(
            f"AI response for chat {st.session_state.current_chat_id}: {agent_response.message}"
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
    save_chat_history(st.session_state.chats, st.session_state.current_chat_id)
