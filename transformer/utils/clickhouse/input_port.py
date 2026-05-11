import io
import json
import logging

import polars as pl
import requests
from requests.auth import HTTPBasicAuth

from ..base_port import BasePort


class ClickhouseInputPort(BasePort):
    """Input port for reading data from ClickHouse via HTTP.

    Requires environment variables configured as INPUT.{port_name}.{VAR_NAME}:
    - data_endpoint: ClickHouse HTTP endpoint URL
    - database: Database name
    - table: Table name
    - jsonCredentials: JSON string with 'username' and 'password' keys
    """

    def __init__(self, port_name: str):
        super().__init__("INPUT", port_name)

        try:
            self.data_endpoint = self.env_vars['data_endpoint']
            self.database = self.env_vars['database']
            self.table = self.env_vars['table']
            json_credentials = json.loads(self.env_vars['jsonCredentials'])
            self.username = json_credentials['username']
            self.password = json_credentials['password']
        except KeyError as e:
            raise EnvironmentError(
                f"Missing required environment variable for InputPort '{self.port_name}': {e.args[0]}"
            ) from e

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
