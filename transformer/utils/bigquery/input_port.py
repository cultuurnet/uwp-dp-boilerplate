import json
import logging

from google.cloud import bigquery
from google.oauth2 import service_account
import polars as pl
from pprint import pprint

from ..base_port import BasePort


class BigQueryInputPort(BasePort):
    """Input port for reading data from BigQuery.

    Requires secretEnvironmentVariables.jsonCredentials to be configured in data-product.yaml.
    This secret is loaded into the environment as INPUT.{port_name}.jsonCredentials and contains
    a JSON string with Google service account credentials. Data is returned as Polars DataFrames,
    which are memory-efficient and recommended for resource-constrained cloud environments.
    """

    def __init__(self, port_name: str):
        super().__init__("INPUT", port_name)

        # Load Google service account credentials from secretEnvironmentVariables.jsonCredentials
        # The secret is loaded into the environment with the key: INPUT.{port_name}.jsonCredentials
        try:
            credentials_map = json.loads(
                self.env_vars['jsonCredentials']
            )
        except KeyError:
            raise EnvironmentError(
                f"configure secretEnvironmentVariables: jsonCredentials: to have json secrets for InputPort: {self.port_name}"
            )

        credentials = service_account.Credentials.from_service_account_info(
            credentials_map,
            scopes=["https://www.googleapis.com/auth/cloud-platform"],
        )
        self._client = bigquery.Client(credentials=credentials)
        

    def execute_query(self, query: str) -> pl.DataFrame:
        """Execute a BigQuery query and return results as a Polars DataFrame.

        Polars DataFrames are used for memory efficiency in resource-constrained environments.
        """
        logging.debug(query)
        job = self._client.query(query)
        return pl.from_arrow(job.result().to_arrow())

    def execute_count_query(self, query: str) -> int:
        """Execute a query and return the count of rows."""
        count_query = f"SELECT COUNT(*) AS count FROM ({query})"
        df = self.execute_query(count_query)
        return int(df[0, 0])

    def execute_paginated_query(self, query: str, limit: int, offset: int) -> pl.DataFrame:
        """Execute a query with pagination using LIMIT and OFFSET."""
        paginated_query = f"{query} LIMIT {limit} OFFSET {offset}"
        return self.execute_query(paginated_query)

    def full_table_ref(self, table: str) -> str:
        return f"`{self.project}.{self.resource}.{table}`"

    def __exit__(self):
        if not hasattr(self, "_client"):
            return
        self._client.close()
