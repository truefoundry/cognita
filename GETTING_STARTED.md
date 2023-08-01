# Getting Started

### Deploy on TrueFoundry

To be able to use **Ask Questions** on your own documents, follow the steps below:

1. Register at TrueFoundry, follow: https://docs.truefoundry.com/docs/installation-and-setup

   - Fill up the form and register as an organization (let's say <org_name>)
   - On `Submit`, you will be redirected to your dashboard endpoint ie https://<org_name>.truefoundry.cloud
   - Complete your email verification
   - Login to the platform at your dashboard endpoint ie. https://<org_name>.truefoundry.cloud

   `Note: Keep your dashboard endpoint handy, we will refer it as "TFY_HOST" and it should have structure like "https://<org_name>.truefoundry.cloud"`

2. Setup a cluster, use TrueFoundry managed for quick setup

   - Give a unique name to your **[Cluster](https://docs.truefoundry.com/docs/workspace)** and click on **Launch Cluster**
   - It will take few minutes to provision a cluster for you
   - On **Configure Host Domain** section, click `Register` for the pre-filled IP
   - Next, `Add` a **Docker Registry** to push your docker images to.
   - Next, **Deploy a Model**, you can choose to `Skip` this step

3. Add a **Storage Integration**

4. Create a **ML Repo**

   - Navigate to **ML Repo** tab
   - Click on `+ New ML Repo` button on top-right
   - Give a unique name to your **ML Repo** (say 'docs-qa-llm')
   - Select **Storage Integration**
   - On `Submit`, your **ML Repo** will be created

   For more details: [link](https://docs.truefoundry.com/docs/creating-ml-repo-via-ui)

5. Create a **Workspace**

   - Navigate to **Workspace** tab
   - Click on `+ New Workspace` button on top-right
   - Select your **Cluster**
   - Give a name to your **Workspace** (say 'docs-qa-llm')
   - Enable **ML Repo Access** and `Add ML Repo Access`
   - Select your **ML Repo** and role as **Project Admin**
   - On `Submit`, a new **Workspace** will be created. You can copy the **Workspace FQN** by clicking on **FQN**.

   For more details: [link](https://docs.truefoundry.com/docs/installation-and-setup#5-creating-workspaces)

6. Generate an **API Key**

   - Navigate to **Settings > API Keys** tab
   - Click on `Create New API Key`
   - Give any name to the **API Key**
   - On `Generate`, **API Key** will be gererated.
   - **Please save the value or download it**

`Note: we will refer it as "TFY_API_KEY"`

For more details: https://docs.truefoundry.com/docs/generate-api-key

7. In order to use default OpenAI embedder. Please get an **OpenAI API Key**. You can get your API Key [here](https://platform.openai.com/account/api-keys)

8. Open your Terminal on parent folder

9. Install our **servicefoundry** cli

```

pip install servicefoundry

```

10. Login from cli

```
sfy login --host <paste your TFY_HOST here>
```

11. Fetch your **Workspace FQN** for the workspace we created at **Step 5**

12. Setup `Vector DB`, in our case we will deploy `QDrant`

```
servicefoundry deploy --workspace_fqn <paste your Workspace FQN here> --file qdrant.yaml --no-wait
```

13. Deploy `Indexer` Job

- Edit the `indexer.yaml` and add following environment variables (**Please replace your workspace name with the placeholder**)

```
env:
    QDRANT_URL: qdrant.<workspace_name>.svc.cluster.local
```

- Deploy the `Indexer` job

```
sfy deploy --workspace_fqn <paste your Workspace FQN here> --file indexer.yaml --no-wait
```

For more details: [link](https://docs.truefoundry.com/docs/introduction-to-job)

14. Deploy `Backend` service

- Edit `serve.yaml` and add the values of environment variables (**Please fill in the placeholders with required information**)

```
env:
    ML_REPO: <paste your ML_Repo name>
    QDRANT_URL: qdrant.<workspace_name>.svc.cluster.local
    TFY_API_KEY: <TFY_API_KEY>
    TFY_HOST: <TFY_HOST>
...
```

- Deploy the `Backend` service

```
sfy deploy --workspace_fqn <paste your workspace fqn here> --file serve.yaml --no-wait
```

15. Deploy `Frontend` service

- Fetch `host` for your frontend: navigate to **Integrations > Clusters**, copy the `Base Domain URL` from your cluster card
- Edit frontend.yaml and add `host`

```
ports:
- host: <host>
...
```

- Fetch `JOB_FQN`: navigate to **Deployments > Jobs**, click on your job `llm-qa-indexer` and copy the `Application FQN` from the details

- Edit `frontend.yaml` and add the values of environment variables (**Please fill in the placeholders with required information**)

```
env:
    JOB_FQN: <JOB_FQN>
    ML_REPO: <ML_Repo name>
    TFY_API_KEY: <TFY_API_KEY>
    BACKEND_URL: http://llm-qa-backend.<workspace_name>.svc.cluster.local:8000
    TFY_HOST: <TFY_HOST>
...
```

- Deploy the `Frontend` service

```
sfy deploy --workspace_fqn <paste your Workspace FQN here> --file frontend.yaml --no-wait
```

16. Visit your QnA playground

- Navigate to **Deployments > Services**
- Click on the `Endpoint` for your service

```
Note: It may take few minutes for the `Endpoint` to be available
```

```

```
