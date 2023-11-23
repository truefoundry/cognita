import json
import os
import shutil
import time
import uuid
from urllib.parse import urljoin

import mlfoundry
import requests
import streamlit as st
from dotenv import load_dotenv
from PIL import Image
from settings import settings
from utils import (create_collection_and_add_docs, fetch_modelnames,
                   fetch_prompts, handle_uploaded_file, print_repo_details)

# load environment variables
load_dotenv()

st.set_page_config(page_title="QnA Playground", layout="wide", page_icon=":rocket:")

st.markdown(
    f"""
            <style>
                .block-container {{
                    padding-top: 2rem;
                    padding-bottom: 1rem;
                    padding-left: 1rem;
                    padding-right: 1rem;
                }}
                .css-1544g2n {{
                    padding: 1rem 1rem 1.5rem;
                }}
            </style>
            """,
    unsafe_allow_html=True,
)
st.sidebar.markdown(
    f"<span style='position: fixed; bottom: 3rem; font-size: large;'><strong><a style='text-decoration: none;' href='https://github.com/truefoundry/docs-qa-playground.git'>Deploy on your own cloud</strong></span>",
    unsafe_allow_html=True,
)

# initialize global variables
BACKEND_URL = settings.BACKEND_URL
ML_REPO = settings.ML_REPO_NAME
mlfoundry_client = mlfoundry.get_client()  # initialize mlfoundry client


def cleanup_history():
    st.session_state["generated"] = []
    st.session_state["past"] = []
    st.session_state["expanded"] = True
    st.session_state["repo_name"] = ""
    st.session_state["query_repo_name"] = ""
    st.session_state["artifact_fqn"] = ""
    st.session_state["question"] = ""
    st.session_state["response"] = None
    st.session_state["selected_model"] = ""


def initialize_session_variables():
    if "generated" not in st.session_state:
        st.session_state["generated"] = []
    if "past" not in st.session_state:
        st.session_state["past"] = []
    if "repo_name" not in st.session_state:
        st.session_state["repo_name"] = ""
    if "artifact_fqn" not in st.session_state:
        st.session_state["artifact_fqn"] = ""
    if "response_status" not in st.session_state:
        st.session_state["response_status"] = False
    if "repo_indexes" not in st.session_state:
        st.session_state["repo_indexes"] = []
    if "question" not in st.session_state:
        st.session_state["question"] = ""
    if "response" not in st.session_state:
        st.session_state["response"] = None
    if "selected_model" not in st.session_state:
        st.session_state["selected_model"] = ""


def ask_question(repo_name, model_name, prompt):
    if model_name == "" or model_name is None:
        st.warning("Please select a model")
        return
    if prompt == "" or prompt is None:
        st.warning("Please enter a question")
        return
    if repo_name == "" or repo_name is None:
        st.warning("Please select a repository")
        return
    # model payload
    max_new_tokens = 500
    k = 7
    model_config = {
        "name": model_name,
        "parameters": {
            "maximumLength": max_new_tokens,
        },
    }

    # prompt template setup
    prompt_template = fetch_prompts(model_name)

    payload = {
        "collection_name": repo_name,
        "query": prompt,
        "model_configuration": model_config,
        "prompt_template": prompt_template,
        "k": k,
    }

    try:
        # backend URL for fetch response
        query_url = urljoin(BACKEND_URL, "/search")
        # request
        llm_response = requests.post(query_url, json=payload)
        llm_response.raise_for_status()
        llm_response = llm_response.json()
        # extracting pages information
        pages = [
            doc.get("metadata").get("page_num") for doc in llm_response.get("docs")
        ]
        pages = list(dict.fromkeys(pages))[:5]
        pages = sorted([i for i in pages if i is not None])
        pages = list(map(str, pages)) if pages else []
        pages = "(" + ", ".join(pages) + ")"
        # storing the llm response
        st.session_state["response"] = llm_response
    except Exception as err:
        print(err)
        st.error(
            f"Unable to fetch answer from the model. Verify endpoint/payload details. Error: {llm_response.text}"
        )
        st.stop()


def main():
    # remove temp directory for every run
    if os.path.exists("tempDir"):
        shutil.rmtree("tempDir")

    # Initialise session state variables
    initialize_session_variables()

    if os.path.exists("./assets/logo.png"):
        st.sidebar.image(Image.open("./assets/logo.png"))
    elif os.path.exists("frontend/assets/logo.png"):
        st.sidebar.image(Image.open("frontend/assets/logo.png"))

    # choose the project worflow type
    sidebar_option = st.sidebar.radio(
        "Choose your option: ",
        ("Existing Project", "New Project"),
        index=0,
        on_change=cleanup_history,
    )

    # initialize all backend url endpoints
    fetch_repos_url = urljoin(BACKEND_URL, f"/collections")
    repo_removel_url = urljoin(BACKEND_URL, "/collections/{}")

    if sidebar_option == "Existing Project":
        # fetch available repos else throw exception
        if len(st.session_state.get("repo_indexes", [])) == 0:
            with st.spinner("Initializing things..."):
                try:
                    repo_resp = requests.get(fetch_repos_url)
                    repo_resp.raise_for_status()
                    repos = repo_resp.json()
                    st.session_state["repo_indexes"] = repos.get("collections")
                except Exception as err:
                    print(err)
                    st.error("Unable to fetch available repos. Verify the backend API.")
                    st.stop()

        # choose your repo from sidebar
        st.session_state["repo_name"] = st.sidebar.selectbox(
            "Choose your Project: ",
            [collection["name"] for collection in st.session_state["repo_indexes"]],
            on_change=cleanup_history,
        )

        if not st.session_state.get("repo_name", ""):
            st.info("No repos available!")

        if st.session_state.get("repo_name", ""):
            try:
                # fetch the selected repo details
                repo = next(
                    (
                        collection
                        for collection in st.session_state["repo_indexes"]
                        if collection.get("name") == st.session_state["repo_name"]
                    ),
                    None,
                )
                # print the repo details on the sidebar for the selected Project Name
                print_repo_details(repo)
            except Exception as err:
                print(err)
                st.error("Unable to fetch project details.")
                st.stop()

        # repo operations
        # delete - for removing the repo
        delete_btn = st.sidebar.button("Delete Project", on_click=cleanup_history)
        if delete_btn:
            if len(st.session_state.get("repo_indexes", [])) > 0:
                st.session_state["query_repo_name"] = ""  # clear out LLM repo
                with st.spinner("Deleting the repo..."):
                    remove_url = repo_removel_url.format(st.session_state["repo_name"])
                    repo_del_response = requests.delete(
                        remove_url,
                        timeout=20,
                    )
                    repo_del_response = repo_del_response.json()
                    if repo_del_response.get("status") == "ok":
                        st.sidebar.success("Successfully deleted project repo.")

                with st.spinner("Fetching newly added repos..."):
                    try:
                        repo_resp = requests.get(fetch_repos_url)
                        repo_resp.raise_for_status()
                        repos = repo_resp.json()
                        st.session_state["repo_indexes"] = repos.get("collections")
                    except Exception as err:
                        print(err)
                        st.error(
                            "Unable to fetch available repos. Verify the backend API."
                        )
                        st.stop()

        # refresh - fetching any newly added repo
        refresh_btn = st.sidebar.button("Refresh", on_click=cleanup_history)
        if refresh_btn:
            if len(st.session_state.get("repo_indexes", [])) > 0:
                with st.spinner("Fetching newly added repos..."):
                    try:
                        repo_resp = requests.get(fetch_repos_url)
                        repo_resp.raise_for_status()
                        repos = repo_resp.json()
                        st.session_state["repo_indexes"] = repos.get("collections")
                    except Exception as err:
                        print(err)
                        st.error(
                            "Unable to fetch available repos. Verify the backend API."
                        )
                        st.stop()

            # fetch list of models available in the playground
            with st.spinner("Fetching list of available models..."):
                try:
                    model_response = requests.get(
                        settings.LLM_GATEWAY_ENDPOINT + "/api/model/?enabled_only=true",
                        headers={
                            "Authorization": f"Bearer {settings.TFY_API_KEY}",
                        },
                    )
                    st.session_state["model_response"] = model_response.json()
                    st.experimental_rerun()
                except Exception as err:
                    print(err)
                    st.error("Unable to fetch updated model list.")
                    st.stop()

    elif sidebar_option == "New Project":
        # create a embedder container
        embedder_container = st.container()

        with embedder_container:
            # create an expander for initializing embedder indexing
            expanded_status = st.session_state.get("expanded", True)
            with st.expander("Embedder Indexer", expanded=expanded_status):
                # create multi-column for menu items
                col_ex, col_ey = st.columns((2, 2), gap="large")

                uploaded_file = col_ey.file_uploader(
                    "Choose file or a zip to upload", type=["pdf", "zip", "txt", "md"]
                )

                col_ey.warning(
                    "Disclaimer: Please do not upload any sensitive data as this playground will be publicly available."
                )

                # Embedding configuration ()
                with col_ex:
                    # enter the repo run name
                    repo_name = col_ex.text_input("Project Name", "")

                    # create sub-column inside the column.
                    sub_colx, sub_coly = st.columns((2, 2), gap="medium")

                    # create a dropdown menu for embedder model
                    embedder = sub_colx.selectbox(
                        "Embedder Model",
                        ("OpenAI", "E5-large-v2"),
                        index=1,
                    )
                    # embedder model chunk size
                    chunk_size = sub_coly.text_input("Chunk Size", "350")

                if embedder == "OpenAI":
                    embedder_config = {
                        "provider": "OpenAI",
                        "config": {"model": "text-embedding-ada-002"},
                    }

                elif embedder == "E5-large-v2":
                    embedder_config = {
                        "provider": "TruefoundryEmbeddings",
                        "config": {
                            "endpoint_url": settings.TRUEFOUNDRY_EMBEDDINGS_ENDPOINT
                        },
                    }

                submit_btn = col_ex.button("Process", key="submit_btn")
                if submit_btn:
                    # raise an warning if repo_name is null
                    if not repo_name:
                        st.warning("Project name cannot be empty")
                        time.sleep(2)
                        st.experimental_rerun()

                    # uploading the data
                    with st.spinner("Uploading data..."):
                        try:
                            files_dir = f"{repo_name}_" + str(uuid.uuid4())
                            upload_mask = handle_uploaded_file(uploaded_file)
                            # upload the files to mlfoundry artifacts
                            artifact_version = mlfoundry_client.log_artifact(
                                ml_repo=ML_REPO,
                                name=files_dir,
                                artifact_paths=[
                                    mlfoundry.ArtifactPath(
                                        os.path.join(os.getcwd(), "tempDir")
                                    )
                                ],
                            )
                            if upload_mask:
                                st.session_state["artifact_fqn"] = artifact_version.fqn
                                st.session_state["uploaded"] = True
                            else:
                                st.error("Unable to upload file.")
                                st.stop()
                        except:
                            st.error("Unable to upload file.")
                            st.stop()

                    with st.spinner("Indexing job going on..."):
                        try:
                            create_collection_and_add_docs(
                                url=BACKEND_URL,
                                collection_name=repo_name,
                                source_uri=st.session_state["artifact_fqn"],
                                embedder_config=embedder_config,
                                chunk_size=chunk_size,
                            )
                        except Exception as err:
                            print(err)
                            st.error("Unable to index the documents.")
                            st.stop()

                        placeholder = st.empty()
                        progress_bar = st.progress(0)
                        while True:
                            try:
                                response_status = requests.get(
                                    f"{BACKEND_URL}/collections/{repo_name}/status"
                                )
                                response_status.raise_for_status()
                                repo_status_response = response_status.json()
                                status = repo_status_response.get("status")
                                placeholder.text(f"Status: {status}")
                                if status == "COMPLETED":
                                    progress_bar.progress(100 / 100)
                                    st.session_state["query_repo_name"] = repo_name
                                    st.text("Success.")
                                    st.success(
                                        "Successfully completed indexing job. You can start asking questions now."
                                    )
                                    st.session_state["expanded"] = False
                                    break
                                if status == "FAILED":
                                    st.error("Unable to index the documents.")
                                    st.stop()
                                if (
                                    status == "RUNNING"
                                    or status == "MISSING"
                                    or status == "INITIALIZED"
                                ):
                                    progress_bar.progress(50 / 100)
                            except Exception as err:
                                print(err)
                                st.error("Unable to index the documents.")
                                st.stop()
                            # wait every two seconds for status pull
                            time.sleep(2)

                        placeholder.empty()  # remove the placeholder

    with st.spinner("Fetching list of available models..."):
        if "model_response" not in st.session_state:
            try:
                response = requests.get(
                    settings.LLM_GATEWAY_ENDPOINT + "/api/model/enabled",
                    headers={
                        "Authorization": f"Bearer {settings.TFY_API_KEY}",
                    },
                )
                response.raise_for_status()
                st.session_state["model_response"] = response.json()
            except Exception as err:
                print(err)
                st.error("Unable to fetch model list.")
                st.stop()

    if (st.session_state.get("repo_name", "")) or (
        st.session_state.get("query_repo_name", "")
    ):
        with st.chat_message("assistant"):
            col1, col2 = st.columns([6, 4])
            col1.write("Welcome to QnA Playground. Ask questions on your documents.")
            model_response = st.session_state["model_response"]
            model_list = fetch_modelnames(
                model_response,
                filters=[],
            )
            st.session_state["selected_model"] = col2.selectbox(
                "Model Name: ", model_list, index=0, label_visibility="collapsed"
            )

        prompt = st.chat_input("Ask your question here")
        if prompt:
            st.session_state["question"] = prompt
            with st.chat_message("user"):
                st.markdown(st.session_state["question"], unsafe_allow_html=True)
            with st.spinner("Generating response..."):
                ask_question(
                    st.session_state["repo_name"]
                    if sidebar_option == "Existing Project"
                    else st.session_state["query_repo_name"],
                    st.session_state["selected_model"],
                    prompt,
                )
            if st.session_state["response"]:
                with st.chat_message("assistant"):
                    st.markdown(
                        st.session_state["response"].get("answer"),
                        unsafe_allow_html=True,
                    )

        # clear everything
        if sidebar_option == "New Project":
            clear_btn = st.sidebar.button("Reset")
            if clear_btn:
                cleanup_history()
                st.experimental_rerun()


if __name__ == "__main__":
    main()
