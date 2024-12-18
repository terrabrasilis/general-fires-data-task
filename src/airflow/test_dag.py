from airflow.models import DAG
from airflow.operators.python import PythonVirtualenvOperator


def test_venv_func(par1, par2):

    print("******"*10)
    print(par1)
    print("******"*10)
    print(par2)
    print("******"*10)
    pass

with DAG(
    dag_id="venv_op_not_accepting_context_kwarg",
    schedule_interval=None,
) as dag:
    
    my_path='/opt/airflow/project/test'

    test = PythonVirtualenvOperator(
        task_id="test",
        venv_cache_path="/opt/airflow/venv/inpe/test",
        python_callable=test_venv_func,
        provide_context=True,
        op_kwargs={'par2': 'OTHER VALUE FOR PARAM', 'par1': f'{my_path}'}
    )