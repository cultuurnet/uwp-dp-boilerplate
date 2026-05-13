import io
import json
import logging

import polars as pl
import requests
from requests.auth import HTTPBasicAuth

from ..base_port import BasePort


class ClickhouseInputPort(BasePort):
    """Adapter for Clickhouse InputPort
    Manages connection to clichouse input port, it uses request library as clickhouse client does not support path in url
    Requires variables to be configured in data-products.yaml file:
    - data_endpoint: ClickHouse HTTP endpoint URL
    - database: Database name
    - table: Table name
    - jsonCredentials: "name_of_secrets_key" this name (name_of_secrets_key) needs to be set in secrets.yaml
        - secrets.yaml name_of_secrets_key: "JSON string with 'username' and 'password' keys"
    Info can be found in https://data-product-management.tst.uitwisselingsplatform.be/data-afnemen/output-port-credentials
    """

    def __init__(self, port_name: str):
        """
        pass the port name that is configured in data-product.yaml
        """
        super().__init__("INPUT", port_name)


        if "jsonCredentials" not in self.env_vars:
            raise EnvironmentError(
                f"Missing required environment variable 'jsonCredentials' for InputPort: {self.port_name}. "
                "You must set - jsonCredentials: \"name_of_secrets_key\" in your data-products.yaml file for this InputPort. "
                "The corresponding secrets.yaml file must also have a key 'name_of_secrets_key' with a JSON string containing 'username' and 'password' fields. "
                "See https://data-product-management.tst.uitwisselingsplatform.be/data-afnemen/output-port-credentials for details."
            ) from e

        try:
            self.data_endpoint = self.env_vars['data_endpoint']
            self.database = self.env_vars['database']
            self.table = self.env_vars['table']
            json_credentials = json.loads(self.env_vars['jsonCredentials'])
            self.username = json_credentials['username']
            self.password = json_credentials['password']
        except KeyError as e:
            raise EnvironmentError(
                f"In data-product.yaml file you must set inputPorts > {self.port_name}' > environmentVariables > {e.args[0]}"
            ) from e

        self.full_table_name = f"{self.database}.{self.table}"
        self._base_url = self.data_endpoint
        self._session = requests.Session()
        self._auth = HTTPBasicAuth(self.username, self.password)

    def query(self, query: str) -> pl.DataFrame:
        """Execute a query and return results as a Polars DataFrame."""
        logging.debug(query)
        resp = self._session.post(self._base_url, data=query, auth=self._auth, timeout=60)
        resp.raise_for_status()
        return pl.read_csv(io.StringIO(resp.text), separator="\t")

    def close(self):
        self._session.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
