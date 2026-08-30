import os
import sys
from google import genai
from dotenv import load_dotenv
from google.genai.models import Models
import streamlit as st

load_dotenv()
API_KEY = os.getenv("API_KEY")

if not API_KEY:
  try:
    API_KEY = st.secrets["API_KEY"]
  except Exception:
    API_KEY = None
if not API_KEY:
  st.error("API_KEY NOT FOUND")
  st.stop()
    

client = genai.Client(api_key = API_KEY)
model_name = "gemini-3.5-flash-lite"

contents = []
max_conversation_tokens = 1000


def total_tokens_used(messages):
  try:
    response = client.models.count_tokens(
      model = model_name,
      contents = messages
    )
    return response.total_tokens
  except Exception as e:
    print(f"token count error {e}" )
    return 0

def enforce_token_budget(messages, buget):
  try: 
    while total_tokens_used(messages) > buget:
      if (len(messages) <= 2):
        break
      
      # Remove the oldest message
      messages.pop(0)
  except Exception as e:
    print(f"token buget error {e}")
    return 0
    
  

def chat(user_input, system_instruction, temperature, max_output_tokens):
  # adding the question to the model
  contents = st.session_state.messages
  
  contents.append({
    "role": "user",
    "parts":[
      {"text":user_input}
      ]
  })
  
  enforce_token_budget(contents, max_conversation_tokens)
  
  with st.spinner("Thinking ..."):
    response = client.models.generate_content(
      model = model_name,
      contents = contents,
      config = {
        "system_instruction": system_instruction,
        "temperature": temperature,
        "max_output_tokens": max_output_tokens
      }
    )
    
  # adding the data to the model
  contents.append({
    "role": "model",
    "parts": [{"text": response.text}]
  })
  
  return response.text


# -------------------------
# STREAMLIT UI
# -------------------------

st.title("Bear bot")
st.sidebar.header("Options")
st.sidebar.write("Past conversation")
max_output_tokens = st.sidebar.slider("Max Tokens", 1, 300, 100)
temperature = st.sidebar.slider("Temperature", 0.0, 1.0, 0.7)
system_message_type = st.sidebar.selectbox("System Message", ("Sasy Assistant", "Angry Assistant", "Friendly Assistant", "Custom"))

if system_message_type == "Sasy Assistant":
  system_instruction = "You are a Sasy assistant that is fed up with answering questions"
elif system_message_type == "Angry Assistant":
  system_instruction ="You are a angry assistant that likes yelling in all answers"
elif system_message_type == "Friendly Assistant":
  system_instruction = "You are a friendly assistant that enjoys talking with people"
elif system_message_type == "Custom":
  system_instruction = st.sidebar.text_area("Custom System Message", "Enter your type here")
else:
  system_instruction = "You are a helpful assistant"
  
if "messages" not in st.session_state:
  st.session_state.messages = []

if st.sidebar.button("Apply New System Message"):
  st.session_state.messages = []
  st.success("System message update")
  
if st.sidebar.button ("Reset Conversation"):
  st.session_state.messages = []
  st.success("Conversation reset.")


for message in st.session_state.messages:
  with st.chat_message(message["role"]):
    st.markdown(message["parts"][0]["text"])
 
prompt = st.chat_input("Ask anything")
if prompt:
  with st.chat_message("user"):
    st.markdown(prompt)
    
  reply = chat(prompt, system_instruction, temperature, max_output_tokens)
  
  with st.chat_message("model"):
    st.markdown(reply)
     
    