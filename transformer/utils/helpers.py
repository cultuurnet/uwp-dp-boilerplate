from os import getenv


def get_environment_variable(var_name: str, default=None):
    """
    Retrieve an environment variable value or return default if not set.
    """
    value = getenv(var_name)
    if value:
        return value
    if default is None:
        raise EnvironmentError(f"Environment variable {var_name} is not set")
    return default

def get_input_port_environment_variable(input_port_name: str, var_name:str) -> str:
    return get_environment_variable(f"INPUT.{input_port_name}.{var_name}")

def get_output_port_environment_variable(output_port_name: str, var_name:str) -> str:
    return get_environment_variable(f"OUTPUT.{output_port_name}.{var_name}")
