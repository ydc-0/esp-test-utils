from ..config import EnvConfig


class BaseEnv:
    def __init__(
        self,
        env_name: str,
        env_config_file: str,
    ):
        if not env_config_file:
            self.env_config = EnvConfig(env_name)
        else:
            self.env_config = EnvConfig(env_name, config_file=env_config_file)
        self._dut_list = []

    def setup(self):
        pass

    def teardown(self):
        pass

    def get_variable(self, name):
        return self.env_config.get_variable(name)

    def __enter__(self) -> 'BaseEnv':
        """Support using "with" statement (automatically called setup and teardown)"""
        self.setup()
        return self

    def __exit__(self, exc_type, exc_value, trace):  # type: ignore
        """Always close the serial and clean resources before exiting."""
        self.teardown()
