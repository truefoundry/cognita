import json
import os
import shutil
import time
import uuid
from copy import copy
from urllib.parse import urljoin

import mlfoundry
import requests
import streamlit as st
from dotenv import load_dotenv
from servicefoundry.lib.dao.application import get_job_run
from streamlit_chat import message
from utils import (
    CODE_TEMPLATE,
    TEXT_TEMPLATE,
    fastapi_request,
    handle_uploaded_file,
    print_llm_help,
    print_repo_details,
    validate_github,
)

# load environment variables
load_dotenv()

# set page configuration for streamlit
st.set_page_config(layout="wide")


# initialize global variables
BACKEND_URL = os.environ["BACKEND_URL"]
ML_REPO = os.environ["ML_REPO"]
JOB_FQN = os.environ["JOB_FQN"]
mlfoundry_client = mlfoundry.get_client()  # initialize mlfoundry client


def cleanup_history():
    st.session_state["generated"] = []
    st.session_state["past"] = []
    st.session_state["expander_close"] = True
    st.session_state["repo_name"] = ""
    st.session_state["query_repo_name"] = ""
    st.session_state["artifact_fqn"] = ""


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


def main():
    # remove temp directory for every run
    if os.path.exists("tempDir"):
        shutil.rmtree("tempDir")

    # Initialise session state variables
    initialize_session_variables()

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
            # fetch the selected repo details
            mlfoundry_run = mlfoundry_client.get_run_by_name(
                ML_REPO, st.session_state["repo_name"]
            )
            logged_params = mlfoundry_run.get_params()
            # print the repo details on the sidebar for the selected Project Name
            print_repo_details(logged_params)

        # repo operations
        # delete - for removing the repo
        delete_btn = st.sidebar.button("Delete", on_click=cleanup_history)
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
                        st.sidebar.success("Successfully deleted repo.")

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
            expanded_status = st.session_state.get("expander_close", True)
            with st.expander("Embedder Indexer", expanded=expanded_status):
                # create multi-column for menu items
                col_ex, col_ey = st.columns((2, 2), gap="large")
                # data uploader dropdown menu
                upload_method = col_ex.selectbox(
                    "DataLoader",
                    ("Github", "FileUploader"),
                    index=1,
                    on_change=cleanup_history,
                )

                if upload_method == "FileUploader":
                    # uploader button
                    uploaded_file = col_ex.file_uploader(
                        "Choose file or a zip to upload",
                        type=["pdf", "zip", "py", "txt", "md"],
                    )

                elif upload_method == "Github":
                    repo_link = col_ex.text_input("Enter your github repo link: ")
                    if not validate_github(repo_link) and repo_link:
                        st.error("Please enter a valid Github repository url.")
                        st.stop()

                # Embedding configuration ()
                with col_ey:
                    # enter the repo run name
                    repo_name = col_ey.text_input("Project Name", "")

                    # create sub-column inside the column.
                    sub_colx, sub_coly = st.columns((2, 2), gap="medium")

                    # create a dropdown menu for embedder model
                    embedder = sub_colx.selectbox(
                        "Embedder Model", ("HuggingFaceInstruct", "OpenAI", "TruefoundryEmbeddings"), index=1
                    )
                    # embedder model chunk size
                    chunk_size = sub_coly.text_input("Chunk Size", "350")

                if embedder == "HuggingFaceInstruct":
                    em_config = {
                        "embed_instruction": "Represent the sentence for retrieval: ",
                        "query_instruction": "Represent the question for retrieving supporting sentences: ",
                        "embedder_endpoint": "",
                        "embedder_batchsize": 64,
                    }
                    em_config = json.dumps(em_config, indent=4)

                elif embedder == "OpenAI":
                    em_config = {
                        "model": "text-embedding-ada-002",
                    }
                    em_config = json.dumps(em_config, indent=4)
                
                elif embedder == "TruefoundryEmbeddings":
                    em_config = {
                        "endpoint_url": "https://llm-embedder.example.domain.com",
                    }
                    em_config = json.dumps(em_config, indent=4)

                config_stx, config_sty = st.columns((2, 2), gap="large")
                embedder_config = col_ey.text_area(
                    "Embedder Config", em_config, height=130
                )
                example_parser_config = {".pdf": "PdfParserFast"}
                parser_config = col_ex.text_input(
                    "Parser Configuration", json.dumps(example_parser_config)
                )

                submit_btn = col_ex.button("Process", key="submit_btn")
                if submit_btn:
                    # raise an error if repo_name is null
                    if not repo_name:
                        st.error("Project name cannot be empty")
                        st.experimental_rerun()

                    # validate the embedding configuration
                    try:
                        embedder_config_val = json.loads(embedder_config)
                        # validate embedder_endpoint.
                        if (
                            not embedder_config_val.get("embedder_endpoint")
                            and embedder == "HuggingFaceInstruct"
                        ):
                            st.error(
                                "Please enter a valid embedding model endpoint in the config."
                            )
                            st.stop()
                    except Exception:
                        st.error("Not a valid embedder config json.")
                        st.stop()

                    # close the expander
                    st.session_state["expander_close"] = False

                    # uploading the data
                    with st.spinner("Uploading data..."):
                        if upload_method == "Github":
                            st.session_state["artifact_fqn"] = "github://" + repo_link
                            st.session_state["uploaded"] = True
                        elif upload_method == "FileUploader":
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

                    with st.spinner("Indexing job going on..."):
                        emb_payload = {
                            "repo_name": repo_name,
                            "ml_repo": ML_REPO,
                            "job_fqn": JOB_FQN,
                            "source_uri": st.session_state["artifact_fqn"],
                            "embedder": embedder,
                            "chunk_size": chunk_size,
                            "embedder_config": embedder_config,
                            "repo_creds": "",
                            "parsers_map": parser_config,
                        }
                        jobrun_name = fastapi_request(emb_payload, BACKEND_URL)
                        if jobrun_name is None:
                            st.error("Unable to index the documents.")
                            st.stop()

                        # indexing job
                        repo_status_url = urljoin(
                            BACKEND_URL, f"/repo-status/{jobrun_name}?job_fqn={JOB_FQN}"
                        )
                        st.sidebar.divider()
                        st.sidebar.markdown(
                            f"<strong><span style='color: darkgrey; text-decoration:'>Project Name:</span></strong> <span style='color: white;'>  {repo_name}</span>",
                            unsafe_allow_html=True,
                        )
                        placeholder = st.sidebar.empty()
                        progress_bar = st.sidebar.progress(0)
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
                                    st.sidebar.text("Success.")
                                    st.success(
                                        "Successfully completed indexing job. You can start asking questions now."
                                    )
                                    st.session_state["expander_close"] = False
                                    break
                                if status == "Failed":
                                    st.error("Unable to index the documents.")
                                    st.stop()
                                if status == "Running":
                                    progress_bar.progress(
                                        repo_status_response.get("progress") / 100
                                    )
                            time.sleep(5)  # wait every five seconds for status pull

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
        # container for chat history
        response_container = st.container()

        # container for text box
        container = st.container()

        # Help Section
        print_llm_help()

        # container for text box
        with container:
            with st.form(key="chat_form", clear_on_submit=False):
                # multi column layout in form
                stx, sty = st.columns((2, 1), gap="large")
                # question input field
                user_input = stx.text_area("Ask your question:", key="model_input_text")
                # custom template field
                custom_model_template = stx.text_area(
                    "Custom Prompt Template (Optional): ",
                    value="Use the context below to answer question at the end.\n\n{context}\n\nQuestion: {question}\nAnswer:",
                    height=160,
                )
                submit_button = stx.form_submit_button(label="Ask")

                with sty:
                    st.write("")  # UI space enhancement
                    model_response = st.session_state["model_response"]
                    if model_response.status_code != 200:
                        st.error("Unable to fetch the list of models.")
                        st.stop()

                    model_list = list(model_response.json().keys())
                    model_name = st.selectbox("Model Name: ", model_list, index=0)

                    # split column into sub-layout columns again
                    stx_sub, sty_sub = st.columns((2, 2), gap="small")
                    with stx_sub:
                        st.write("")  # add space in UI
                        # template format
                        template_format = st.selectbox(
                            "Prompt Format: ", ("Code", "Text", "Custom"), index=1
                        )
                        if template_format == "Text":
                            model_template = copy(TEXT_TEMPLATE)
                        elif template_format == "Code":
                            model_template = copy(CODE_TEMPLATE)
                        elif template_format == "Custom":
                            model_template = copy(custom_model_template)

                        max_new_tokens = st.number_input("Max New Tokens", value=2048)

                    with sty_sub:
                        st.write("")  # add space in UI
                        k = st.text_input("K Value", 15)

                if user_input and submit_button:
                    # disable the embedding indexer expander bar when asking questions.
                    st.session_state["expander_close"] = False

                    # model payload
                    provider, model_name = model_name.split(":", maxsplit=1)
                    if "openai" in provider:
                        model_config = {
                            "name": model_name,
                            "provider": provider,
                            "tag": model_name,
                            "parameters": {
                                "temperature": 0.75,
                                "maximumLength": max_new_tokens,
                                "topP": 0.95,
                                "topK": 5,
                                "presencePenalty": 0,
                                "frequencyPenalty": 0,
                                "stopSequences": [],
                                "repetitionPenalty": 1,
                            },
                        }

                    else:
                        model_config = {
                            "name": model_name,
                            "provider": provider,
                            "tag": model_name,
                            "parameters": {
                                "temperature": 0.75,
                                "topP": 0.95,
                                "topK": 5,
                                "repetitionPenalty": 1.01,
                                "stopSequences": [],
                                "frequencyPenalty": 0,
                                "maximumLength": max_new_tokens,
                            },
                        }

                    payload = {
                        "repo_name": st.session_state["repo_name"]
                        if sidebar_option == "Existing Project"
                        else st.session_state["query_repo_name"],
                        "k": k,
                        "maximal_marginal_relevance": False,
                        "query": user_input,
                        "model_configuration": model_config,
                        "prompt_template": model_template,
                    }

                    # Now, fetch the response from the API
                    with st.spinner("Fetching response..."):
                        # backend URL for fetch response
                        query_url = urljoin(BACKEND_URL, "/search")
                        # request
                        llm_response = requests.post(query_url, json=payload)
                        # check status code for the response
                        if llm_response.status_code == 200:
                            llm_response = llm_response.json()
                            # extracting pages information
                            pages = [
                                doc.get("metadata").get("page_num")
                                for doc in llm_response.get("docs")
                            ]
                            pages = list(dict.fromkeys(pages))[:5]
                            pages = sorted([i for i in pages if i is not None])
                            pages = list(map(str, pages)) if pages else []
                            pages = "(" + ", ".join(pages) + ")"
                            # storing the llm response
                            st.session_state["past"].append(user_input)
                            generated_ans = f"""{llm_response.get("answer")}<br>
                            <div style="display: inline;"><p><span style="font-size: smaller; color: darkgrey;"><strong>Model:</strong></span> <span style="font-size: smaller; font-weight: bold; color: white; text-shadow: 0 0 5px rgba(0, 0, 0, 0.5);">{model_name}</span></p><p><span style="font-size: smaller; color: darkgrey;"><strong>Project Name:</strong></span> <span style="font-size: smaller; font-weight: bold; color: white; text-shadow: 0 0 5px rgba(0, 0, 0, 0.5);">{payload.get("run_name")}</span></p><p><span style="font-size: smaller; color: darkgrey;"><strong>Page No:</strong></span> <span style="font-size: smaller; font-weight: bold; color: white; text-shadow: 0 0 5px rgba(0, 0, 0, 0.5);">{pages}</span></p></div>"""
                            st.session_state["generated"].append(generated_ans)
                        else:
                            print("Failed LLM Response: ", llm_response.text)
                            st.error(
                                "Unable to fetch answer from the model. Verify endpoint/payload details."
                            )
                            st.stop()

        # display the response in UI as conversational style
        with response_container:
            for i in range(len(st.session_state["generated"])):
                message(st.session_state["past"][i], is_user=True, key=str(i) + "_user")
                message(st.session_state["generated"][i], key=str(i), allow_html=True)
            st.write("")  # UI space

        # clear everything
        if sidebar_option == "New Project":
            clear_btn = st.sidebar.button("Reset")
            if clear_btn:
                cleanup_history()
                response_container.empty()
                container.empty()
                st.experimental_rerun()


if __name__ == "__main__":
    main()
