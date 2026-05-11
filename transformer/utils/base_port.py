import os


class BasePort:
    """Base class for data product ports (INPUT or OUTPUT).

    Ports are defined in data-product.yaml and can have associated environment
    variables and secrets that are loaded into the system environment. This class
    extracts port-specific environment variables based on the port type and name.

    Environment variables are expected to follow the naming convention:
        {PORT_TYPE}.{PORT_NAME}.{VARIABLE_NAME}

    For example: INPUT.database.jsonCredentials or OUTPUT.warehouse.apiKey
    """

    def __init__(self, port_type, port_name):
        if port_type not in ("INPUT", "OUTPUT"):
            raise ValueError('port_type must be "INPUT" or "OUTPUT"')
        self.port_type = port_type
        self.port_name = port_name

        # Extract environment variables specific to this port from the system environment
        self.env_vars = {}
        for k, v in os.environ.items():
            if not k.startswith(f"{self.port_type}.{self.port_name.lower()}."):
                continue
            short_key = k.replace(f"{self.port_type}.{self.port_name.lower()}.", "")
            self.env_vars[short_key] = v
