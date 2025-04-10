import streamlit as st
from openai import AzureOpenAI
import pandas as pd
import pdfplumber
import tempfile

# Azure OpenAI Client
client = AzureOpenAI(
    api_key="CMfEAxVMt34Nq8hQlkz9erOq7PcvKhNCvtyCXB7PhT8ypv7vctuyJQQJ99BDACHYHv6XJ3w3AAABACOGGQbS",
    api_version="2024-12-01-preview",
    azure_endpoint="https://cybersofttrainingday2.openai.azure.com"
)

st.title("🧠 Multi Modal Chatbot")

# Session State Initialization
if "messages" not in st.session_state:
    st.session_state.messages = [{
        "role": "system",
        "content": "You are a helpful assistant. If files are uploaded, summarize them or answer based on their content."
    }]

if "files_uploaded" not in st.session_state:
    st.session_state.files_uploaded = False

# File Uploader (Multiple PDFs and Excel)
uploaded_files = st.file_uploader(
    "Upload PDF or Excel files",
    type=["pdf", "xlsx"],
    accept_multiple_files=True  # Enable multiple file uploads
)

file_text = ""

if uploaded_files and not st.session_state.files_uploaded:
    all_file_contents = []  # Store content from all files

    for uploaded_file in uploaded_files:
        file_type = uploaded_file.type

        # Temporary file to process each upload
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            tmp_file.write(uploaded_file.read())
            tmp_path = tmp_file.name

        # Process PDFs
        if "pdf" in file_type:
            with pdfplumber.open(tmp_path) as pdf:
                pdf_text = "\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])
                all_file_contents.append(f"File: {uploaded_file.name}\n{pdf_text}")

        # Process Excel
        elif "excel" in file_type or "spreadsheet" in file_type:
            df = pd.read_excel(tmp_path)
            excel_text = df.to_markdown()
            all_file_contents.append(f"File: {uploaded_file.name}\n{excel_text}")

    # Combine all file contents
    if all_file_contents:
        file_text = "\n\n---\n\n".join(all_file_contents)  # Separate files with a divider
        st.session_state.messages.append({
            "role": "user",
            "content": f"I've uploaded multiple files. Please analyze the following content:\n{file_text}"
        })
        st.session_state.files_uploaded = True

# Show Chat History
for msg in st.session_state.messages[1:]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Chat Input
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
                model="gpt-4o-mini",
                messages=visible_messages
            )
            reply = response.choices[0].message.content
            st.markdown(reply)

    st.session_state.messages.append({"role": "assistant", "content": reply})
