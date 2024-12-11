import time
import os
import joblib
import streamlit as st
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure the Generative AI API
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Generate a new chat ID based on the current timestamp
new_chat_id = f'{time.time()}'
MODEL_ROLE = 'ai'
USER_AVATAR_ICON = '👩🏻‍💻'
AI_AVATAR_ICON = '🤖'

st.markdown("""
    <style>
    body {
        background-color: #F5F5F5;
        font-family: Arial, sans-serif;
    }
    .main-title {
        font-size: 36px;
        color: #1A5276;
        font-weight: bold;
        text-align: center;
        margin-top: 20px;
        margin-bottom: 20px;
    }
    .sidebar-title {
        font-size: 24px;
        color: #1A5276;
        font-weight: bold;
        margin-bottom: 20px;
    }
    .chat-container {
        display: flex;
        align-items: flex-start;
        margin: 10px 0;
    }
    .user-container {
        flex-direction: row-reverse;
        text-align: right;
    }
    .avatar {
        display: inline-block;
        width: 35px;
        height: 35px;
        font-size: 18px;
        border-radius: 50%;
        background-color: #FFF;
        color: #1A5276;
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 5px;
        box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.15);
    }
    .chat-bubble {
        border-radius: 15px;
        padding: 15px;
        max-width: 75%;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        font-size: 16px;
        line-height: 1.4;
        transition: all 0.3s ease;
    }
    .ai-bubble {
        background-color: #F7F9F9;
        color: #34495E;
        margin-left: 10px;
    }
    .user-bubble {
        background-color: #CDEFFD;
        color: #1A5276;
        margin-right: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# Create a data folder if it doesn't already exist
if not os.path.exists('data/'):
    os.mkdir('data/')

# Load past chats (if available)
try:
    past_chats: dict = joblib.load('data/past_chats_list')
except FileNotFoundError:
    past_chats = {}

# Sidebar for past chats
with st.sidebar:
    st.markdown('<div class="sidebar-title">Past Chats 📂</div>', unsafe_allow_html=True)
    if st.session_state.get('chat_id') is None:
        st.session_state.chat_id = st.selectbox(
            label='Pick a past chat',
            options=[new_chat_id] + list(past_chats.keys()),
            format_func=lambda x: past_chats.get(x, 'New Chat'),
            placeholder='_',
        )
    else:
        st.session_state.chat_id = st.selectbox(
            label='Pick a past chat',
            options=[new_chat_id, st.session_state.chat_id] + list(past_chats.keys()),
            index=1,
            format_func=lambda x: past_chats.get(x, 'New Chat' if x != st.session_state.chat_id else st.session_state.chat_title),
            placeholder='_',
        )
    st.session_state.chat_title = f'ChatSession-{st.session_state.chat_id}'

# Main title
st.markdown('<div class="main-title">Chat with Gemini</div>', unsafe_allow_html=True)

# Load chat history
try:
    st.session_state.messages = joblib.load(f'data/{st.session_state.chat_id}-st_messages')
    st.session_state.gemini_history = joblib.load(f'data/{st.session_state.chat_id}-gemini_messages')
except FileNotFoundError:
    st.session_state.messages = []
    st.session_state.gemini_history = []

# Start chat session with Gemini model
st.session_state.model = genai.GenerativeModel('gemini-pro')
st.session_state.chat = st.session_state.model.start_chat(history=st.session_state.gemini_history)

# Display previous chat messages with ChatGPT-style layout
for message in st.session_state.messages:
    if message['role'] == 'user':
        st.markdown(f"""
        <div class="chat-container user-container">
            <div class="avatar">{USER_AVATAR_ICON}</div>
            <div class="chat-bubble user-bubble">{message["content"]}</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="chat-container">
            <div class="avatar">{AI_AVATAR_ICON}</div>
            <div class="chat-bubble ai-bubble">{message["content"]}</div>
        </div>
        """, unsafe_allow_html=True)

# React to user input
if prompt := st.chat_input('Type your message...'):
    # Save chat for later
    if st.session_state.chat_id not in past_chats.keys():
        past_chats[st.session_state.chat_id] = st.session_state.chat_title
        joblib.dump(past_chats, 'data/past_chats_list')

    # Display user message
    st.markdown(f"""
    <div class="chat-container user-container">
        <div class="avatar">{USER_AVATAR_ICON}</div>
        <div class="chat-bubble user-bubble">{prompt}</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Add user message to history
    st.session_state.messages.append({'role': 'user', 'content': prompt})

    # Send message to Gemini AI and get response
    response = st.session_state.chat.send_message(prompt, stream=True)
    
    full_response = ''
    with st.container():
        message_placeholder = st.empty()
        for chunk in response:
            if hasattr(chunk, 'text') and chunk.text:
                for ch in chunk.text.split(' '):
                    full_response += ch + ' '
                    time.sleep(0.05)
                    message_placeholder.markdown(f"""
                    <div class="chat-container">
                        <div class="avatar">{AI_AVATAR_ICON}</div>
                        <div class="chat-bubble ai-bubble">{full_response}▌</div>
                    </div>
                    """, unsafe_allow_html=True)

        # Finalize AI response display
        final_text = full_response.strip() if full_response else "Error: AI response was empty or invalid."
        message_placeholder.markdown(f"""
        <div class="chat-container">
            <div class="avatar">{AI_AVATAR_ICON}</div>
            <div class="chat-bubble ai-bubble">{final_text}</div>
        </div>
        """, unsafe_allow_html=True)

    # Add AI response to chat history
    st.session_state.messages.append({'role': MODEL_ROLE, 'content': final_text})

    # Update history and save chat
    st.session_state.gemini_history = st.session_state.chat.history
    joblib.dump(st.session_state.messages, f'data/{st.session_state.chat_id}-st_messages')
    joblib.dump(st.session_state.gemini_history, f'data/{st.session_state.chat_id}-gemini_messages')
