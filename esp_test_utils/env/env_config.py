import logging
import os
import pathlib
from typing import Any
from typing import List

import yaml


class EnvConfig:
    ENV_CONFIG_FILE_NAME = 'EnvConfig.yml'
    # Set env config file directly
    TEST_ENV_CONFIG_FILE = os.getenv('TEST_ENV_CONFIG_FILE')
    # Find env config file from project root path
    # CI_PROJECT_DIR was set by gitlab CI
    PROJECT_ROOT_DIR = os.getenv('PROJECT_ROOT_DIR') or os.getenv('CI_PROJECT_DIR')

    # Allow input variables from terminal during local debugging
    ALLOW_INPUT = not os.getenv('CI')

    @classmethod
    def _search_dirs(cls) -> List[str]:
        search_dirs = []
        if cls.TEST_ENV_CONFIG_FILE:
            search_dirs.append(pathlib.Path(cls.TEST_ENV_CONFIG_FILE))
        if cls.PROJECT_ROOT_DIR:
            _proj_path = pathlib.Path(cls.PROJECT_ROOT_DIR)
            search_dirs.append(_proj_path)
            search_dirs.append(_proj_path / 'ci-test-runner-configs' / os.environ.get('CI_RUNNER_DESCRIPTION', '.'))
        # Add current directory
        search_dirs.append(pathlib.Path('.'))
        # Add home directory
        search_dirs.append(pathlib.Path(os.environ['HOME']) / 'test_env_config')
        return [str(d) for d in search_dirs if d.is_dir()]

    @classmethod
    def get_variable(cls, env_name: str, key: str, default: Any = None) -> Any:
        """
        Get test environment related variable, Never returns None!

        config file format:

            $PROJECT_ROOT_DIR/<EnvConfig.yml>
                ```
                <env_name>:
                    key: var
                    key2: var2
                <env_name2>:
                    key: var
                ```
        """
        env_name = env_name or 'default'
        config_file = ''
        config = {}
        for _dir in cls._search_dirs():
            if cls.ENV_CONFIG_FILE_NAME not in os.listdir(_dir):
                continue
            config_file = os.path.join(_dir, cls.ENV_CONFIG_FILE_NAME)

        if config_file:
            with open(config_file, 'r', encoding='utf-8') as f:
                data = yaml.load(f.read(), Loader=yaml.FullLoader)
            config = data[env_name]
        else:
            _msg = (
                'Can not find env file from:\n  ',
                '  \n'.join(cls._search_dirs()),
            )
            logging.warning(_msg)

        var = config.get(key, default)
        if var is None:
            logging.warning(f'Failed to get env variable {env_name}/{key}.')
            logging.info(cls.get_variable.__doc__)
            if not os.environ.get('CI_JOB_ID'):
                # Try to get variable from stdin
                var = input('You can input the variable now:')
            else:
                raise ValueError(f'Env variable not found: {env_name}/{key}')
        logging.debug(f'Got env variable {env_name}/{key}: {var}')
        return var
