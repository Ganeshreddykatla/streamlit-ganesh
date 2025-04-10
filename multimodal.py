import streamlit as st
from openai import AzureOpenAI
import pandas as pd
import pdfplumber
import tempfile
from dotenv import load_dotenv
import os
import base64
from PIL import Image
from io import BytesIO

# Load environment variables
# load_dotenv()
# api_key = os.getenv("key")
# endpoint = os.getenv("url")

# Azure OpenAI Client
client = AzureOpenAI(
    api_key="CMfEAxVMt34Nq8hQlkz9erOq7PcvKhNCvtyCXB7PhT8ypv7vctuyJQQJ99BDACHYHv6XJ3w3AAABACOGGQbS",
    api_version="2024-12-01-preview",
    azure_endpoint="https://cybersofttrainingday2.openai.azure.com"
)

st.title("🧠 Multimodal Chatbot (PDF | Excel | Image)")

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = [{
        "role": "system",
        "content": "You are a helpful assistant. If files or images are uploaded, analyze or summarize them first."
    }]
if "files_uploaded" not in st.session_state:
    st.session_state.files_uploaded = False

# File uploader (PDF, Excel, Images)
uploaded_files = st.file_uploader(
    "Upload PDF, Excel or Image files",
    type=["pdf", "xlsx", "jpg", "jpeg", "png"],
    accept_multiple_files=True
)

# Process files
file_chunks = []
image_inputs = []

if uploaded_files and not st.session_state.files_uploaded:
    for uploaded_file in uploaded_files:
        file_type = uploaded_file.type

        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            tmp_file.write(uploaded_file.read())
            tmp_path = tmp_file.name

        if "pdf" in file_type:
            with pdfplumber.open(tmp_path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        file_chunks.append(f"📄 {uploaded_file.name} - Page {page.page_number}\n{text[:1500]}")  # Truncate to avoid long tokens

        elif "excel" in file_type:
            df = pd.read_excel(tmp_path)
            excel_text = df.to_markdown()
            file_chunks.append(f"📊 {uploaded_file.name}\n{excel_text[:1500]}")

        elif "image" in file_type:
            img = Image.open(tmp_path)
            buffered = BytesIO()
            img.save(buffered, format="PNG")
            img_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")
            image_inputs.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/png;base64,{img_base64}"
                }
            })

    if file_chunks:
        st.session_state.messages.append({
            "role": "user",
            "content": "Here's the content from uploaded documents:\n\n" + "\n\n---\n\n".join(file_chunks)
        })

    if image_inputs:
        st.session_state.messages.append({
            "role": "user",
            "content": [
                {"type": "text", "text": "Please analyze these image(s):"},
                *image_inputs
            ]
        })

    st.session_state.files_uploaded = True

# Display chat history
for msg in st.session_state.messages[1:]:
    with st.chat_message(msg["role"]):
        if isinstance(msg["content"], list):
            st.markdown("🖼️ Image input sent.")
        else:
            st.markdown(msg["content"])

# Chat input
if prompt := st.chat_input("Ask anything..."):
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    visible_messages = [
        {"role": m["role"], "content": m["content"]}
        for m in st.session_state.messages
    ]

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=visible_messages
            )
            reply = response.choices[0].message.content
            st.markdown(reply)

    st.session_state.messages.append({"role": "assistant", "content": reply})
