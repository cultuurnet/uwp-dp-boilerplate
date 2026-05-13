from typing import Sequence
import warnings

import polars as pl

from clickhouse_connect import common
from clickhouse_connect.driver import create_client

from ..base_port import BasePort


class ClickhouseOutputPort(BasePort):
    """
    This is an adapter for clichhouse output port. 
    It loads important vars like database, auth_username, ... from env vars as properties & all env vars are availble under .env_vars
    I handles batched inputs
    Manages the connection to Clickhouse
    """

    DEFAULT_BATCH_SIZE = 500

    def __init__(self, port_name: str):
        """Initialize output port for ClickHouse.

        Args:
            port_name: The name of an output port defined in data-product.yaml.
                       Used to resolve connection settings from environment variables
                       (OUTPUT.{port_name}.host, OUTPUT.{port_name}.database, etc.).
        """
        super().__init__("OUTPUT", port_name)
        common.set_setting("autogenerate_session_id", False)
        
        try:
            self.auth_password = self.env_vars["AUTH_PASSWORD"]
            # self.auth_type = self.env_vars["AUTH_TYPE"] 
            self.auth_username = self.env_vars["AUTH_USERNAME"]
            self.database = self.env_vars["DATABASE"]
            self.host = self.env_vars["HOST"]
            self.http_port = self.env_vars["HTTP_PORT"]
            self.table = self.env_vars["TABLE"]
            # self.tcp_port = self.env_vars["TCP_PORT"]

            self.full_table_name = f"{self.database}.{self.table}"

        except KeyError as e:
            raise EnvironmentError(
                f"Missing required environment variable for OutputPort '{self.port_name}': {e.args[0]}"
            ) from e

        self._client = create_client(
            host=self.host,
            database=self.database,
            port=self.http_port,
            username=self.auth_username,
            password=self.auth_password
        )

    def truncate_table(self):
        """
        Empty table
        """
        self._client.command(f"TRUNCATE TABLE `{self.table}`")

    def insert_rows(self, rows: Sequence[tuple], column_names: Sequence[str], batch_size: int = DEFAULT_BATCH_SIZE):
        """
        Insert rows as sequence of tuples, not recommended, use insert_polars_dataframe
        """
        warnings.warn(
            "insert_rows is not recommended; use insert_polars_dataframe instead for better performance and memory efficiency.",
            UserWarning
        )
   
        for i in range(0, len(rows), batch_size):
            batch = rows[i:i + batch_size]
            if not batch:
                continue
            self._client.insert(table=self.table, data=batch, column_names=list(column_names))

    def insert_polars_dataframe(self, df: pl.DataFrame, batch_size: int = DEFAULT_BATCH_SIZE):
        """
        Insert rows as polars datafram (memory efficient)
        """
        column_names = df.columns
        for i in range(0, len(df), batch_size):
            batch = df.slice(i, batch_size)
            self._client.insert(table=self.table, data=batch.rows(), column_names=column_names)

    def query(self, query: str) -> pl.DataFrame:
        """
        Send a Query to output port and get result, can be handy to get latest record for example
        """
        result = self._client.query(query)
        return pl.DataFrame(result.result_set, schema=result.column_names, orient="row")

    def close(self):
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
