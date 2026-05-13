import json
import logging

from google.cloud import bigquery
from google.oauth2 import service_account
import polars as pl
from pprint import pprint

from ..base_port import BasePort


class BigQueryInputPort(BasePort):
    """Adapter for BigQuery

    It manages secrets and connections to bigquery

    - jsonCredentials: "name_of_secrets_key" this name (name_of_secrets_key) needs to be set in secrets.yaml
        - secrets.yaml file: name_of_secrets_key: "JSON string with Google service account credentials" 
          Can be downloaded GCP console > **IAM & Admin** > **Service Accounts** > your account > **Keys** > **Add Key** > **Create new key** (JSON format)
    - The env vars that are set in data-products.yaml > inputPorts > {port_name} > environmentVariables are availble in self.env_vars

    Data is returned as Polars DataFrames, which are memory-efficient and recommended for resource-constrained cloud environments.
    It also has a a paginated query function to get results per page to manage the resource-constrained cloud environments
    """

    def __init__(self, port_name: str):
        super().__init__("INPUT", port_name)
        try:
            credentials_map = json.loads(
                self.env_vars['jsonCredentials']
            )
        except KeyError:
            raise EnvironmentError(
                f"Missing required environment variable 'jsonCredentials' for InputPort: {self.port_name}. "
                "You must set - jsonCredentials: \"name_of_secrets_key\" in your data-products.yaml file for this InputPort. "
                "The corresponding secrets.yaml file must also have a key 'name_of_secrets_key' with a Google service account credential JSON string. "
                "See GCP console > IAM & Admin > Service Accounts > your service account > Keys > Add Key > Create new key (JSON format)."
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

    def __exit__(self):
        if not hasattr(self, "_client"):
            return
        self._client.close()
