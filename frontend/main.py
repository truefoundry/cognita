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
from utils import fastapi_request, handle_uploaded_file, print_repo_details

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
BACKEND_URL = os.environ["BACKEND_URL"]
ML_REPO = os.environ["ML_REPO"]
JOB_FQN = os.environ["JOB_FQN"]
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
    max_new_tokens = 1024
    k = 15
    provider, model_name = model_name.split(":", maxsplit=1)
    model_config = {
        "name": model_name,
        "provider": provider,
        "tag": model_name,
        "parameters": {
            "temperature": 0.75,
            "topP": 0.95,
            "topK": 5,
            "repetitionPenalty": 1,
            "stopSequences": [],
            "frequencyPenalty": 0,
            "maximumLength": max_new_tokens,
        },
    }

    payload = {
        "repo_name": repo_name,
        "k": k,
        "maximal_marginal_relevance": False,
        "query": prompt,
        "model_configuration": model_config,
    }

    # backend URL for fetch response
    query_url = urljoin(BACKEND_URL, "/search")
    # request
    llm_response = requests.post(query_url, json=payload)
    # check status code for the response
    if llm_response.status_code == 200:
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
    else:
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
    fetch_repos_url = urljoin(BACKEND_URL, f"/repos")
    repo_removel_url = urljoin(BACKEND_URL, "/repo/{}")

    if sidebar_option == "Existing Project":
        # fetch available repos else throw exception
        if len(st.session_state.get("repo_indexes", [])) == 0:
            with st.spinner("Initializing things..."):
                try:
                    repo_resp = requests.get(fetch_repos_url)
                    repo_resp = repo_resp.json()
                    if repo_resp.get("detail") == "Not Found":
                        raise Exception("Backend /repos API is not accessible.")
                    else:
                        st.session_state["repo_indexes"] = repo_resp.get("output")
                except Exception:
                    st.error("Unable to fetch available repos. Verify the backend API.")
                    st.stop()

        # choose your repo from sidebar
        st.session_state["repo_name"] = st.sidebar.selectbox(
            "Choose your Project: ",
            st.session_state["repo_indexes"],
            on_change=cleanup_history,
        )

        if not st.session_state.get("repo_name", ""):
            st.info("No repos available!")

        if st.session_state.get("repo_name", ""):
            try:
                # fetch the selected repo details
                mlfoundry_run = mlfoundry_client.get_run_by_name(
                    ML_REPO, st.session_state["repo_name"]
                )
                logged_params = mlfoundry_run.get_params()
                # print the repo details on the sidebar for the selected Project Name
                print_repo_details(logged_params)
            except:
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
                        repo_resp = repo_resp.json()
                        if repo_resp.get("detail") == "Not Found":
                            raise Exception("Backend /repos API is not accessible.")
                        else:
                            st.session_state["repo_indexes"] = repo_resp.get("output")
                            st.experimental_rerun()
                    except Exception:
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
                        repo_resp = repo_resp.json()
                        if repo_resp.get("detail") == "Not Found":
                            raise Exception("Backend /repos API is not accessible.")
                        else:
                            st.session_state["repo_indexes"] = repo_resp.get("output")
                            st.experimental_rerun()
                    except Exception:
                        st.error(
                            "Unable to fetch available repos. Verify the backend API."
                        )
                        st.stop()

            # fetch list of models available in the playground
            with st.spinner("Fetching list of available models..."):
                try:
                    st.session_state["model_response"] = requests.get(
                        f'{os.environ.get("TFY_HOST",)}/llm-playground/api/models-enabled',
                        headers={
                            "Authorization": f"Bearer {os.environ.get('TFY_API_KEY')}",
                        },
                    )
                    st.experimental_rerun()
                except Exception:
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

                # Embedding configuration ()
                with col_ex:
                    # enter the repo run name
                    repo_name = col_ex.text_input("Project Name", "")

                    # create sub-column inside the column.
                    sub_colx, sub_coly = st.columns((2, 2), gap="medium")

                    # create a dropdown menu for embedder model
                    embedder = sub_colx.selectbox(
                        "Embedder Model",
                        ("OpenAI", "TruefoundryEmbeddings"),
                        index=1,
                    )
                    # embedder model chunk size
                    chunk_size = sub_coly.text_input("Chunk Size", "350")

                if embedder == "OpenAI":
                    embedder_config = {
                        "model": "text-embedding-ada-002",
                    }
                    embedder_config = json.dumps(embedder_config, indent=4)

                elif embedder == "TruefoundryEmbeddings":
                    embedder_config = {
                        "endpoint_url": os.environ.get(
                            "TRUEFOUNDRY_EMBEDDINGS_ENDPOINT",
                            "https://llm-embedder.example.domain.com",
                        ),
                    }
                    embedder_config = json.dumps(embedder_config, indent=4)

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
                                st.session_state["artifact_fqn"] = (
                                    "mlfoundry://" + artifact_version.fqn
                                )
                                st.session_state["uploaded"] = True
                            else:
                                st.error("Unable to upload file.")
                                st.stop()
                        except:
                            st.error("Unable to upload file.")
                            st.stop()

                    with st.spinner("Indexing job going on..."):
                        emb_payload = {
                            "repo_name": repo_name,
                            "ml_repo": ML_REPO,
                            "job_fqn": JOB_FQN,
                            "source_uri": st.session_state["artifact_fqn"],
                            "embedder": embedder,
                            "chunk_size": chunk_size,
                            "embedder_config": embedder_config,
                        }
                        jobrun_name = fastapi_request(emb_payload, BACKEND_URL)
                        if jobrun_name is None:
                            st.error("Unable to index the documents.")
                            st.stop()

                        # indexing job
                        repo_status_url = urljoin(
                            BACKEND_URL, f"/repo-status/{jobrun_name}?job_fqn={JOB_FQN}"
                        )
                        placeholder = st.empty()
                        progress_bar = st.progress(0)
                        while True:
                            response_status = requests.get(repo_status_url)
                            if response_status.status_code == 200:
                                repo_status_response = response_status.json()
                                if repo_status_response is None:
                                    st.error("Unable to index the documents.")
                                    st.stop()
                                status = repo_status_response.get("status")
                                placeholder.text(f"Status: {status}")
                                if status == "Finished":
                                    st.session_state[
                                        "query_repo_name"
                                    ] = repo_status_response.get("repo_name")
                                    st.text("Success.")
                                    st.success(
                                        "Successfully completed indexing job. You can start asking questions now."
                                    )
                                    st.session_state["expanded"] = False
                                    break
                                if status == "Failed":
                                    st.error("Unable to index the documents.")
                                    st.stop()
                                if status == "Running":
                                    progress_bar.progress(
                                        repo_status_response.get("progress") / 100
                                    )
                            # wait every two seconds for status pull
                            time.sleep(2)

                        placeholder.empty()  # remove the placeholder

    with st.spinner("Fetching list of available models..."):
        if "model_response" not in st.session_state:
            st.session_state["model_response"] = requests.get(
                f'{os.environ.get("TFY_HOST",)}/llm-playground/api/models-enabled',
                headers={
                    "Authorization": f"Bearer {os.environ.get('TFY_API_KEY')}",
                },
            )

    if (st.session_state.get("repo_name", "")) or (
        st.session_state.get("query_repo_name", "")
    ):
        with st.chat_message("assistant"):
            col1, col2 = st.columns([6, 4])
            col1.write("Welcome to QnA Playground. Ask questions on your documents.")
            model_response = st.session_state["model_response"]
            if model_response.status_code != 200:
                st.error("Unable to fetch the list of models.")
                st.stop()
            model_list = list(model_response.json().keys())
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
