from typing import Sequence

import polars as pl

from clickhouse_connect import common
from clickhouse_connect.driver import create_client

from ..base_port import BasePort


class ClickhouseOutputPort(BasePort):
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
        self._client.command(f"TRUNCATE TABLE `{self.table}`")

    def insert_rows(self, rows: Sequence[tuple], column_names: Sequence[str], batch_size: int = DEFAULT_BATCH_SIZE):
        for i in range(0, len(rows), batch_size):
            batch = rows[i:i + batch_size]
            if not batch:
                continue
            self._client.insert(table=self.table, data=batch, column_names=list(column_names))

    def insert_polars_dataframe(self, df: pl.DataFrame, batch_size: int = DEFAULT_BATCH_SIZE):
        column_names = df.columns
        for i in range(0, len(df), batch_size):
            batch = df.slice(i, batch_size)
            self._client.insert(table=self.table, data=batch.rows(), column_names=column_names)

    def query(self, query: str) -> pl.DataFrame:
        result = self._client.query(query)
        return pl.DataFrame(result.result_set, schema=result.column_names, orient="row")

    def close(self):
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
