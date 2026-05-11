from os import getenv


def get_environment_variable(var_name: str) -> str:
    """
    Retrieve an environment variable value or Raise an exception if the value is not set.
    """
    value = getenv(var_name)
    if value:
        return value
    raise EnvironmentError(f"Environment variable {var_name} not set, ")