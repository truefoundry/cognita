import os
import shutil
from urllib.parse import urljoin
from zipfile import ZipFile

import requests
import streamlit as st


TEXT_TEMPLATE = """Given a list of documents, answer the given question precisely and accurately. Copying from the list of documents to form an answer is encouraged. Answer only from the information found in the documents. Paraphrasing is allowed but do not change any of the facts. Once you answer the question, stop immediately. If the given documents do not contain a relevant answer, say "I am not sure" and stop. Do not make up an answer.
    
    DOCUMENTS:
    {context}

    QUESTION:
    {question}

    ANSWER:
    """
CODE_TEMPLATE = """
            You will be provided a list of code snippets and a question.
            Your job is to understand the code snippets and answer the question in details in natural language.
            Once you answer the question, stop immediately.
            If the given documents do not contain a relevant answer, say "I am not sure" and stop.
            Do not make up an answer.

            Code snippets:

            {context}

            QUESTION:
            {question}

            ANSWER:
            """


def handle_uploaded_file(uploaded_file):
    status = False
    if uploaded_file is not None:
        status = True
        os.makedirs("tempDir", exist_ok=True)
        with open(os.path.join("tempDir", uploaded_file.name), "wb") as f:
            f.write(uploaded_file.getbuffer())

    return status


def validate_github(link):
    if "github" in link.lower():
        return True
    return False


def fastapi_request(payload, BACKEND_URL):
    url = urljoin(BACKEND_URL, "/repo")
    response = requests.post(url, json=payload)
    print(response)

    if response.status_code == 200:
        run_name = response.json()
    else:
        run_name = None
        st.error("Error from indexing endpoint:")
        st.error(response.text)

    return run_name


def print_repo_details(logged_params):
    st.sidebar.text("")
    st.sidebar.markdown(
        f"<strong><span style='text-decoration:'>Embedding Model:</span></strong> <span>  {logged_params['embedder']}</span>",
        unsafe_allow_html=True,
    )
    st.sidebar.markdown(
        f"<strong><span style='text-decoration:'>Embedding Chunk Size:</span></strong> <span>  {logged_params['chunk_size']}</span>",
        unsafe_allow_html=True,
    )


def print_llm_help():
    with st.expander("LLM Help Section (FAQ): ", expanded=False):
        faq_html = """
        <style>
            p {
                color: darkgrey;
            }
        </style>

        <details open>
        <summary><strong>When should I enter an endpoint URL in the "HuggingFaceModel Endpoint" field?</strong></summary>
        <p>If you choose the model name (dropdown) to be "HuggingfaceModel," you should enter the endpoint URL in the "HuggingFaceModel Endpoint" field. This is required to specify the location of the Hugging Face model you want to use.</p>
        </details>

        <details open>
        <summary><strong>When should I enter a custom prompt in the "Custom Prompt Template" field?</strong></summary>
        <p>If you choose 'Custom' from the 'Template Format' dropdown menu, you should input a custom prompt into the 'Custom Prompt Template' field. This will allow you to give specific instructions or questions for the model to generate responses that match your requirements. Please note that this feature currently only works with the HuggingFace Model.</p>
        </details>

        <details open>
        <summary><strong>What should I do if I choose the model name as "OpenAI"?</strong></summary>
        <p>If you select "OpenAI" as the model name (dropdown), you don't need to enter the "HuggingFaceModel Endpoint." In this case, you only need to provide your OpenAI API Key to access the OpenAI model.</p>
        </details>

        <details open>
        <summary><strong>Do I need to enter a custom prompt if I choose the "Text" or "Code" prompt format?</strong></summary>
        <p>No, if you choose the "Prompt Format" dropdown menu to be "Text" or "Code," you don't have to enter a custom prompt. Pre-defined templates are available in the backend for these use cases, which work flawlessly.</p>
        </details>
        """

        st.markdown(faq_html, unsafe_allow_html=True)
