"""A DAG to update the TerraBrasilis Active Fires database."""
from datetime import datetime
import pathlib
import sys
import pendulum
from airflow import DAG
from airflow.models import Variable

# used to load the location where base dag is
dag_dir = str(pathlib.Path(__file__).parent.resolve().absolute())
sys.path.append(dag_dir)

# used to load the location where code of taks are
project_dir = str(pathlib.Path(__file__).parent.parent.resolve().absolute())
sys.path.append(project_dir)

from fires_dag_operators import BaseDagOperators

# get a list of emails to send to, as a string in this format: email1@host.com,email2@host.com,email3@host.com
EMAIL_TO = Variable.get("GENERAL_EMAIL_TO")
if not EMAIL_TO:
    raise Exception(
        f"Missing GENERAL_EMAIL_TO variable into airflow configuration."
    )

DAG_KEY = "active_fires_update"
venv_path = f"/opt/airflow/venv/inpe/{DAG_KEY}"

EMAIL_TO = str(EMAIL_TO).split(",")
# Default arguments for all tasks. Precedence is the value at task instantiation.
task_default_args = {
    "start_date": pendulum.datetime(year=2025, month=2, day=20, tz="America/Sao_Paulo"),
    "owner": "airflow",
    "depends_on_past": False,
    "email": EMAIL_TO,
    "email_on_failure": True,
    "email_on_retry": False,
    "retries": 0,
}

# apply 'catchup':False to prevent backfills
with DAG(
    DAG_KEY,
    description="Update TerraBrasilis' active fire database",
    catchup=False,
    max_active_runs=1,
    schedule_interval="10 01 * * *",
    default_args=task_default_args,
) as dag:

    baseDag = BaseDagOperators(venv_path=venv_path, project_dir=project_dir)

    update_current_task = baseDag.update_current_task_operator()
    update_last_task = baseDag.update_last_task_operator()
    email_operator = baseDag.email_operator(datetime.today().strftime("%Y-%m-%d"), email_to=EMAIL_TO)
    update_current_task >> update_last_task >> email_operator
