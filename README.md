# Docs QA Playground

This repository helps to setup a production-grade RAG workflow with the help of Truefoundry.

## Architecture

To deploy the complete workflow, we need to set up various components. Here's an overview of the architecture:

### Document Store:

The Document Store is where your documents will be stored. Common options include AWS S3, Google Storage Buckets, or Azure Blob Storage. In some cases, data might come in from APIs, such as Confluence docs.

### Indexer Job:

The Indexer Job takes the documents as input, splits them into chunks, calls the embedding model to embed the chunks, and stores the vectors in the VectorDB. The embedding model can be loaded in the job itself or accessed via an API to ensure scalability.

### Embedding Model:

If you're using OpenAI or an externally hosted model, you don't need to host a model. However, if you opt for an open-source model, you'll have to deploy it in your cloud environment.

### LLM Model:

For OpenAI or hosted model APIs like Cohere and Anthropic, there's no need for additional deployment. Otherwise, you'll need to set up an open-source LLM.

### Query Service:

A FastAPI service provides an API to list all indexed document collections and allows users to query over these collections. It also supports triggering new indexing jobs for additional document collections.

### VectorDB:

You can use a hosted solution like PineCone or host an open-source VectorDB like Qdrant or Milvus to efficiently retrieve similar document chunks.

### Metadata Store:

This store is essential for managing links to indexed documents and storing the configuration used to embed the chunks in those documents.

## Setup with Truefoundry:

Truefoundry, a Kubernetes-based platform, simplifies the deployment of ML training jobs and services at an optimal cost. You can deploy all the components mentioned above on your own cloud account using Truefoundry. The final deployment will be a streamlined and powerful system ready to handle your question-answering needs.

## Deploy on TrueFoundry

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

8.  Open your Terminal on parent folder

9.  Create a virtual env (\*\*python >= 3.10 required)

    ```
      python3 -m venv ./venv
      source ./venv/bin/activate (for Linux/Mac env)
      source .\venv\Scripts\activate (for Windows env)
    ```

10. Install our **servicefoundry** cli

    ```
    pip install servicefoundry
    ```

11. Login from cli

    ```
    sfy login --host <paste your TFY_HOST here>
    ```

12. Fetch your **Workspace FQN** for the workspace we created at **Step 5**

13. Setup `Vector DB`, in our case we will deploy `QDrant`

    ```
    servicefoundry deploy --workspace_fqn <paste your Workspace FQN here> --file qdrant.yaml --no-wait
    ```

14. Deploy `Indexer` Job

    -   Edit the `indexer.yaml` and add following environment variables (**Please replace your workspace name with the placeholder**)

        ```
        env:
            OPENAI_API_KEY: <OpenAI API Key>
            QDRANT_URL: qdrant.<workspace_name>.svc.cluster.local
        ```

    -   Deploy the `Indexer` job

        ```
        sfy deploy --workspace_fqn <paste your Workspace FQN here> --file indexer.yaml --no-wait
        ```

        For more details: [link](https://docs.truefoundry.com/docs/introduction-to-job)

15. Deploy `Backend` service

    -   Edit `serve.yaml` and add the values of environment variables (**Please fill in the placeholders with required information**)

        ```
        env:
            OPENAI_API_KEY: <OpenAI API Key>
            ML_REPO: <paste your ML_Repo name>
            QDRANT_URL: qdrant.<workspace_name>.svc.cluster.local
            TFY_API_KEY: <TFY_API_KEY>
            TFY_HOST: <TFY_HOST>
        ...
        ```

    -   Deploy the `Backend` service

        ```
        sfy deploy --workspace_fqn <paste your workspace fqn here> --file serve.yaml --no-wait
        ```

16. Deploy `Frontend` service

    -   Fetch `host` for your frontend: navigate to **Integrations > Clusters**, copy the `Base Domain URL` from your cluster card

    -   Edit frontend.yaml and add `host`

        ```
        ports:
        - host: <host>
        ...
        ```

    -   Fetch `JOB_FQN`: navigate to **Deployments > Jobs**, click on your job `llm-qa-indexer` and copy the `Application FQN` from the details

    -   Edit `frontend.yaml` and add the values of environment variables (**Please fill in the placeholders with required information**)

        ```
        env:
            JOB_FQN: <JOB_FQN>
            ML_REPO: <ML_Repo name>
            TFY_API_KEY: <TFY_API_KEY>
            BACKEND_URL: http://llm-qa-backend.<workspace_name>.svc.cluster.local:8000
            TFY_HOST: <TFY_HOST>
        ...
        ```

    -   Deploy the `Frontend` service

        ```
        sfy deploy --workspace_fqn <paste your Workspace FQN here> --file frontend.yaml --no-wait
        ```

17. Visit your QnA playground

    -   Navigate to **Deployments > Services**

    -   Click on the `Endpoint` for your service
