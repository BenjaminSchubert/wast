import logging
import shutil
import subprocess
from typing import Dict, List, Optional

from ._config import Config
from ._exceptions import (
    CommandNotFoundException,
    CommandNotInEnvironment,
    UnavailableInterpreterException,
)
from ._subproc import run

LOGGER = logging.getLogger(__name__)


class VenvRunner:
    def __init__(self, name: str, python: str, config: Config) -> None:
        self._original_python = python
        self._path = (
            config.venvs_path / f"{name}-{python}".replace(":", "-")
        ).resolve()
        self._python = str(self._path / "bin/python")
        self._config = config

    def prepare(self) -> None:
        if shutil.which(self._original_python) is None:
            raise UnavailableInterpreterException(self._original_python)

        if self._path.exists():
            LOGGER.debug("venv already exists. Reusing")
            return

        run(
            [self._original_python, "-m", "venv", str(self._path)],
            env=self._config.environ,
            silent_on_success=self._config.verbosity < 2,
        )

    def install(self, *packages: str) -> None:
        self.run(
            [self._python, "-m", "pip", "install", *packages],
            silent_on_success=self._config.verbosity < 2,
        )

    def run(
        self,
        command: List[str],
        env: Optional[Dict[str, str]] = None,
        external_command: bool = False,
        silent_on_success: bool = False,
    ) -> subprocess.CompletedProcess[None]:
        env = self._merge_env(self._config, env)
        self._validate_command(command[0], external_command, env)

        return run(
            command,
            env=env,
            silent_on_success=silent_on_success,
        )

    def _merge_env(
        self, config: Config, additional_env: Optional[Dict[str, str]] = None
    ) -> Dict[str, str]:
        env = config.environ.copy()
        env.update(
            {
                "VIRTUAL_ENV": str(self._path),
                "PATH": f"{self._path}/bin:{env['PATH']}",
            }
        )
        if additional_env is not None:
            env.update(additional_env)
        return env

    def _validate_command(
        self, command: str, external_command: bool, env: Dict[str, str]
    ) -> None:
        cmd = shutil.which(command, path=env["PATH"])

        if cmd is None:
            raise CommandNotFoundException(command, path=env["PATH"])

        command_in_venv = cmd.startswith(str(self._path / "bin"))

        if command_in_venv and external_command:
            LOGGER.warning(
                "The specified command %s is found in the virtual environment,"
                " but external_command=True",
                command[0],
            )
        if not external_command and not command_in_venv:
            raise CommandNotInEnvironment(command)