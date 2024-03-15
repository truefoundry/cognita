# Deploy on TrueFoundry

---

To be able to **Query** on your own documents, follow the steps below:

1.  Register at TrueFoundry, follow [here](https://www.truefoundry.com/register)

    -   Fill up the form and register as an organization (let's say <org_name>)
    -   On `Submit`, you will be redirected to your dashboard endpoint ie https://<org_name>.truefoundry.cloud
    -   Complete your email verification
    -   Login to the platform at your dashboard endpoint ie. https://<org_name>.truefoundry.cloud

    `Note: Keep your dashboard endpoint handy, we will refer it as "TFY_HOST" and it should have structure like "https://<org_name>.truefoundry.cloud"`

2.  Setup a cluster, use TrueFoundry managed for quick setup

    -   Give a unique name to your **[Cluster](https://docs.truefoundry.com/docs/workspace)** and click on **Launch Cluster**
    -   It will take few minutes to provision a cluster for you
    -   On **Configure Host Domain** section, click `Register` for the pre-filled IP
    -   Next, `Add` a **Docker Registry** to push your docker images to.
    -   Next, **Deploy a Model**, you can choose to `Skip` this step

3.  Add a **Storage Integration**

4.  Create a **ML Repo**

    -   Navigate to **ML Repo** tab
    -   Click on `+ New ML Repo` button on top-right
    -   Give a unique name to your **ML Repo** (say 'docs-qa-llm')
    -   Select **Storage Integration**
    -   On `Submit`, your **ML Repo** will be created

        For more details: [link](https://docs.truefoundry.com/docs/creating-ml-repo-via-ui)

5.  Create a **Workspace**

    -   Navigate to **Workspace** tab
    -   Click on `+ New Workspace` button on top-right
    -   Select your **Cluster**
    -   Give a name to your **Workspace** (say 'docs-qa-llm')
    -   Enable **ML Repo Access** and `Add ML Repo Access`
    -   Select your **ML Repo** and role as **Project Admin**
    -   On `Submit`, a new **Workspace** will be created. You can copy the **Workspace FQN** by clicking on **FQN**.

    For more details: [link](https://docs.truefoundry.com/docs/installation-and-setup#5-creating-workspaces)

6.  Generate an **API Key**

    -   Navigate to **Settings > API Keys** tab
    -   Click on `Create New API Key`
    -   Give any name to the **API Key**
    -   On `Generate`, **API Key** will be gererated.
    -   **Please save the value or download it**

        `Note: we will refer it as "TFY_API_KEY"`

        For more details: https://docs.truefoundry.com/docs/generate-api-key

7.  In order to use default OpenAI embedder. Please get an **OpenAI API Key**. You can get your API Key [here](https://platform.openai.com/account/api-keys)

8.  Qdrant Deployment
    To store and retrieve vectors we setup a vector database in this case Qdrant. You can also setup other databases like Chroma, Weviate,

    -   Go to deployments tab
    -   Select Applications
    -   Select your workspace name for deployment
    -   Select Qdrant
    -   Enter the name of Qdrant DB
    -   Click Submit

    Qdrant will be deployed on your instance, and an endpoint will be available in Qdrant dashboard keep it handy, this will be referred as `VECTOR_DB_CONFIG` url.

9.  Open your Terminal on parent folder and create a virtual env (\*\*python >= 3.10 required)

    ```
      python3 -m venv ./venv
      source ./venv/bin/activate (for Linux/Mac env)
      source .\venv\Scripts\activate (for Windows env)
    ```

10. Install requirements.txt

    ```
    pip install -r backend/requirements.txt
    ```

11. Login from cli

    ```
    sfy login --host <paste your TFY_HOST here>
    ```

12. Setup .env file (Example given below)

    ```
    # For truefoundry setup
    # VECTOR_DB_CONFIG = '{"url": "<vectordb url here from 8.>", "provider": "<any of chroma/qdrant/weaviate>"}'
    VECTOR_DB_CONFIG = '{"url": "https://qdrant-test.tfy-ctl-euwe1-org.org.truefoundry.tech", "provider": "qdrant"}'

    # METADATA_STORE_CONFIG = '{"provider": "mlfoundry", "config": {"ml_repo_name": "<ml-repo name here>"}}'
    METADATA_STORE_CONFIG = '{"provider": "mlfoundry", "config": {"ml_repo_name": "test"}}'

    # For local setup
    TFY_API_KEY = "<YOUR_API_KEY From 6.>"
    TFY_HOST = "<TFY_HOST From 1.">

    TFY_SERVICE_ROOT_PATH = '/'

    # Optional if you have indexer job deployed in truefoundry, and you want to trigger it for indexing.
    # JOB_FQN =
    # JOB_COMPONENT_NAME =

    # Optional if you want to use redis for caching
    # EMBEDDING_CACHE_CONFIG =

    DEBUG_MODE = true
    LOG_LEVEL = "DEBUG"
    ```
