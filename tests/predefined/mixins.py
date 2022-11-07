import re
from abc import ABC, abstractmethod
from pathlib import Path

import pytest


class BaseLinterTest(ABC):
    ESCAPE_CODE = re.compile(r"\x1b\[\d+m")

    @property
    @abstractmethod
    def wastfile(self) -> str:
        pass

    @property
    @abstractmethod
    def invalid_file(self) -> str:
        pass

    @property
    @abstractmethod
    def valid_file(self) -> str:
        pass

    def _make_project(self, path: Path, valid: bool = True) -> None:
        path.joinpath("wastfile.py").write_text(self.wastfile)

        token_file = path.joinpath("src/token.py")
        token_file.parent.mkdir(parents=True)
        if valid:
            token_file.write_text(self.valid_file)
        else:
            token_file.write_text(self.invalid_file)

    @pytest.fixture(scope="module")
    def cache(self, tmp_path_factory):
        return str(tmp_path_factory.mktemp(f"cache-{self.__class__.__name__}"))

    @pytest.mark.parametrize(
        "valid", [True, False], ids=["valid-project", "invalid-project"]
    )
    def test_basic(self, cli, tmp_path, valid, cache):
        self._make_project(tmp_path, valid=valid)

        if valid:
            cli(["--cache-path", cache])
        else:
            result = cli(["--cache-path", cache], raise_on_error=False)
            assert result.exit_code == 1

    @pytest.mark.parametrize(
        "enable_colors", [True, False], ids=["colors", "no-colors"]
    )
    def test_respects_color_settings(
        self, cli, tmp_path, cache, enable_colors
    ):
        self._make_project(tmp_path, valid=False)

        if enable_colors:
            args = ["--colors"]
        else:
            args = ["--no-colors"]

        result = cli(["--cache-path", cache, *args], raise_on_error=False)

        assert result.exit_code == 1
        if enable_colors:
            assert self.ESCAPE_CODE.search(result.stdout)
        else:
            assert not self.ESCAPE_CODE.search(result.stdout)


class BaseFormatterTest(BaseLinterTest):
    @property
    @abstractmethod
    def autofix_step(self) -> str:
        pass

    def test_does_not_modify_by_default(self, cli, tmp_path, cache):
        tmp_path.joinpath("wastfile.py").write_text(self.wastfile)

        token_file = tmp_path.joinpath("src/token.py")
        token_file.parent.mkdir()
        token_file.write_text(self.invalid_file)

        result = cli(["--cache-path", cache], raise_on_error=False)
        assert result.exit_code == 1

        assert token_file.read_text() == self.invalid_file

    def test_can_apply_fixes(self, cli, tmp_path, cache):
        tmp_path.joinpath("wastfile.py").write_text(self.wastfile)

        token_file = tmp_path.joinpath("src/token.py")
        token_file.parent.mkdir()
        token_file.write_text(self.invalid_file)

        cli(["--step", self.autofix_step, "--cache-path", cache])
        assert token_file.read_text() != self.invalid_file

        # And run the default step one last time to ensure it did fix everything
        cli(["--cache-path", cache])
