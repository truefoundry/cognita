python3 -m venv venv
source venv/bin/activate

pip install servicefoundry mlfoundry

servicefoundry login

mlfoundry create-project --name "My Project" --description "My Project Description" --project-id "my-project-id"

PYCMD=$(cat <<EOF
import mlfoundry as mlf

client = mlfoundry.get_client()

ml_repo = client.create_ml_repo(ml_repo="docs-qa")
EOF
)