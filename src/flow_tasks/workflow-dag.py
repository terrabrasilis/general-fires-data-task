"""A DAG to update the TerraBrasilis Active Fires database."""
from datetime import datetime, timedelta
import pathlib
import sys
import pendulum
from airflow import DAG

# used to load the location where base dag is
dag_dir = str(pathlib.Path(__file__).parent.resolve().absolute())
sys.path.append(dag_dir)

# used to load the location where code of taks are
project_dir = str(pathlib.Path(__file__).parent.parent.resolve().absolute())
sys.path.append(project_dir)

from fires_dag_operators import BaseDagOperators

DAG_KEY = "general_fires_data"
venv_path=f"/opt/airflow/venv/inpe/{DAG_KEY}"

default_args = {
    "owner": "airflow",
    "start_date": pendulum.datetime(year=2025, month=2, day=20, tz="America/Sao_Paulo"),
    "email": ["afa.decarvalho@gmail.com"],
    "email_on_failure": True,
    "email_on_retry": False,
    "retry_delay": timedelta(minutes=5),
    "retries": 0,
    "dagrun_timeout": timedelta(minutes=1)
}

# apply 'catchup':False to prevent backfills
with DAG(
    DAG_KEY, catchup=False, max_active_runs=1, schedule_interval="10 01 * * *", default_args=default_args
) as dag:

    baseDag = BaseDagOperators(venv_path=venv_path, project_dir=project_dir)
    
    update_current_task = baseDag.update_current_task_operator()
    update_last_task = baseDag.update_last_task_operator()
    email_operator = baseDag.email_operator(datetime.today().strftime('%Y-%m-%d'))
    update_current_task >> update_last_task >> email_operator
