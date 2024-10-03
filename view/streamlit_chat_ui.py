from openai import OpenAI
import streamlit as st
from dotenv import load_dotenv
import os
import shelve
import argparse
from tomerbot.graphs import Graph   
import requests
import json

load_dotenv()

    
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

        
# Argument parser to handle command-line arguments
parser = argparse.ArgumentParser(description="Streamlit Chatbot Interface")
parser.add_argument('--clean', action='store_true', help="Delete chat history before startup")
args = parser.parse_args()



st.title("Streamlit Chatbot Interface")

USER_AVATAR = "👤"
BOT_AVATAR = "🤖"
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

base_agent_path = r"N:\Dev\1_FelixLabs\WhatsappTomerBot\tomerbot"


############################################
############# Under construction ###########
############################################
# if "graph" not in st.session_state:
#     st.session_state.graph = Graph(base_path=base_agent_path, clean=True)
############################################
############################################
############################################



# Ensure openai_model is initialized in session state
if "openai_model" not in st.session_state:
    st.session_state["openai_model"] = "gpt-4o-mini"


# Load chat history from shelve file
def load_chat_history():
    print(os.getcwd())
    with shelve.open(".streamlit/chat_history") as db:
        return db.get("messages", [])


# Save chat history to shelve file
def save_chat_history(messages):
    with shelve.open(".streamlit/chat_history") as db:
        db["messages"] = messages


# Initialize or load chat history
if "messages" not in st.session_state:
    st.session_state.messages = load_chat_history()

def delete_chat_history():
    st.session_state.messages = []
    save_chat_history([])

# Clean history before loading if --clean argument is passed
if args.clean and "clean" not in st.session_state:
    st.session_state.clean = True 
    delete_chat_history()

# Sidebar with a button to delete chat history
with st.sidebar:
    if st.button("Delete Chat History"):
        delete_chat_history()

# Display chat messages
for message in st.session_state.messages:
    avatar = USER_AVATAR if message["role"] == "user" else BOT_AVATAR
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])

# Main chat interface
if prompt := st.chat_input("How can I help?"):

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar=USER_AVATAR):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar=BOT_AVATAR):
        message_placeholder = st.empty()
        full_response = ""
        ### replace this section
        # for response in client.chat.completions.create( model=st.session_state["openai_model"],
        #                                                 messages=st.session_state["messages"],
        #                                                 stream=True,
        #                                                 ):
        #     full_response += response.choices[0].delta.content or ""
        #     message_placeholder.markdown(full_response + "|")
        ### till here

        # My response logic
        # full_response = st.session_state.graph.invoke_graph(prompt, "123", "test")
        full_response = send_input(prompt)


        message_placeholder.markdown(full_response)
    st.session_state.messages.append({"role": "assistant", "content": full_response})

# Save chat history after each interaction
save_chat_history(st.session_state.messages)

# run from view dir
# streamlit run streamlit_app.py -- --clean
