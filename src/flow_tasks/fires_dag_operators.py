import sys
from airflow.operators.python import PythonVirtualenvOperator
from airflow.operators.email import EmailOperator


class BaseDagOperators:

    def __init__(self, venv_path, project_dir):
        self.project_dir = project_dir
        self.venv_path = venv_path
        self.requirements = [
            "requests",
            "psycopg2-binary",
            "geopandas==0.13.2",
            "fiona==1.9.6",
            "geoalchemy2",
        ]

    def update_current_task_operator(self):

        def fnc_operator(project_dir):
            sys.path.append(project_dir)
            from tasks.update_database import UpdateDatabase

            try:
                aTask = UpdateDatabase()
                aTask.updateCurrentData()
            except Exception:
                raise Exception("updateLastData was failure")

        return PythonVirtualenvOperator(
            task_id="update_current_data_task",
            requirements=self.requirements,
            venv_cache_path=f"{self.venv_path}",
            python_callable=fnc_operator,
            provide_context=True,
            op_args=[f"{self.project_dir}"],
        )

    def update_last_task_operator(self):

        def fnc_operator(project_dir):
            sys.path.append(project_dir)
            from tasks.update_database import UpdateDatabase

            try:
                aTask = UpdateDatabase()
                aTask.updateLastData()
            except Exception:
                raise Exception("updateLastData was failure")

        return PythonVirtualenvOperator(
            task_id="update_last_data_task",
            requirements=self.requirements,
            venv_cache_path=f"{self.venv_path}",
            python_callable=fnc_operator,
            provide_context=True,
            op_args=[f"{self.project_dir}"],
        )

    def email_operator(self, updated_date, email_to: list):
        """Does working only with configurations on stack or in airflow.cfg"""

        return EmailOperator(
            task_id="send_email_task",
            mime_charset="utf-8",
            to=email_to,
            subject="Airflow - {{ dag_run.dag_id }}",
            html_content=f"""<h3>Aviso de execução</h3><p>A tarefa executou com <b>sucesso</b> em {updated_date}.</p>""",
        )
