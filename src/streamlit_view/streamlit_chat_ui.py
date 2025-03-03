# from openai import OpenAI
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
from streamlit_view.view import send_input, delete_all_history, delete_chat, get_response

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

st.title(args.title)
logger.info("Streamlit app has started")

# Display current chat ID under title
if "current_chat_id" in st.session_state:
    st.caption(f"Chat ID: {st.session_state.current_chat_id[:8]}")
    

USER_AVATAR = "👤"
BOT_AVATAR = "🤖"

def generate_short_uuid():
    return uuid.uuid4().hex[:8]

def load_chat_history():
    dir_path = "view/.streamlit"
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
    
    with shelve.open(f"{dir_path}/chat_history") as db:
        chats = db.get("chats", {})
        current_chat_id = db.get("current_chat_id", None)
        return chats, current_chat_id

def save_chat_history(chats, current_chat_id):
    with shelve.open("view/.streamlit/chat_history") as db:
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
    save_chat_history(st.session_state.chats, st.session_state.current_chat_id)
    delete_all_history()

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
                    delete_chat(chat_id)
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

@st.fragment(run_every=1)
def render_ai_response():
    if not st.session_state.ai_messages_queue[st.session_state.current_chat_id]:
        return 
    
    logger.info(f'st.session_state.ai_messages_queue: {st.session_state.ai_messages_queue}')
    for msg in st.session_state.ai_messages_queue[st.session_state.current_chat_id]:
        st.chat_message("assistant", avatar="🤖").write(msg)
    logger.info('Response sent successfully')

@st.fragment(run_every=2)
def check_ai_response():
    if not st.session_state.waiting_response:
        return
      
    current_chat_id = st.session_state.current_chat_id

    try:
        # Fetch messages from backend
        response = get_response(current_chat_id)
        logger.info(f"Response content: {response.content}")
        if response.status_code == 200:
            data = response.json()
            if data['status'] == 'success':
                current_chat = st.session_state.chats[current_chat_id]
                ai_response = data['ai_response']
                st.session_state.ai_messages_queue[current_chat_id].append(ai_response)
                logger.info(f"AI response: {ai_response}")
                current_chat["messages"].append({"role": "assistant", "content": ai_response})
                logger.info(f"AI response for chat {current_chat_id}: {ai_response}")
                # # Debug logging for chat state
                # logger.info(f"Current chat ID: {current_chat_id}")
                # logger.info(f"Current chat state: {current_chat}")
                # logger.info(f"Current chat messages: {current_chat.messages}")
                # st.session_state.waiting_response = False  # Reset waiting state after successful response
            elif data['status'] == 'pending':
                # No messages available yet
                pass
        else:
            logger.error(f"Unexpected response status: {response.status_code}")
            st.warning("No messages available yet")
    except Exception as e:
        logger.error(f"Error fetching messages: {e}")

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

    # Send the input and set waiting_response to true
    logger.info(f"Sending input to the model: {prompt}, {st.session_state.current_chat_id}")
    send_input(prompt, st.session_state.current_chat_id)
    st.session_state.waiting_response = True
    

    
    
# Run fragments to check and render responses
render_ai_response()
check_ai_response()
    
# Save chat history
save_chat_history(st.session_state.chats, st.session_state.current_chat_id)