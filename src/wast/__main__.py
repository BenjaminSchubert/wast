import importlib.util
import logging
import shutil
from argparse import (
    ArgumentParser,
    BooleanOptionalAction,
    Namespace,
    _AppendAction,
)
from contextlib import suppress
from contextvars import Context
from importlib.metadata import version
from typing import Any, List, Optional

from . import _pipeline
from ._config import Config
from ._exceptions import BaseWastException
from ._logging import setup_logging

LOGGER = logging.getLogger(__name__)


class _SplitAppendAction(_AppendAction):
    def __call__(
        self,
        parser: ArgumentParser,
        namespace: Namespace,
        values: Any,
        option_string: Optional[str] = None,
    ) -> None:
        items = getattr(namespace, self.dest, None)
        if items is None:
            items = []
        setattr(
            namespace,
            self.dest,
            [*items, *[v.strip() for v in values.split(",")]],
        )


def _parse_args(args: Optional[List[str]] = None) -> Namespace:
    parser = ArgumentParser()
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {version('wast')}"
    )

    parser.add_argument("--config", default="./wastfile.py")
    parser.add_argument(
        "-s",
        "--step",
        action=_SplitAppendAction,
        dest="steps",
        help="which step(s) to run",
    )
    parser.add_argument(
        "-o",
        "--only",
        action=_SplitAppendAction,
        dest="only_steps",
        help="Only run the specified step(s), even if they have dependencies",
    )
    parser.add_argument(
        "-e",
        "--except",
        action=_SplitAppendAction,
        dest="except_steps",
        help="Don't run the following step(s), even if they are required",
    )
    parser.add_argument(
        "-l",
        "--list",
        action="store_true",
        dest="list_only",
        help="Only list all available steps. Don't execute",
    )
    parser.add_argument(
        "--list-dependencies",
        action="store_true",
        help="When listing, also show step dependencies",
    )
    parser.add_argument(
        "-v", "--verbose", action="count", default=0, help="Be more verbose"
    )
    parser.add_argument(
        "-q", "--quiet", action="count", default=0, help="Be more quiet"
    )
    parser.add_argument(
        "-j",
        "--jobs",
        type=int,
        help="Number of jobs to run in parallel (default: %(default)d)",
        default=1,
    )

    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--setup-only",
        action="store_true",
        help="Only run setup actions, don't run",
    )
    group.add_argument(
        "--no-setup",
        action="store_true",
        help="Don't run setup actions, only the rest",
    )

    parser.add_argument(
        "--ff",
        "--fail-fast",
        dest="fail_fast",
        action="store_true",
        help="Stop at the first error",
    )

    parser.add_argument(
        "-c",
        "--clean",
        action="store_true",
        help="Clear the cache before running",
    )

    parser.add_argument(
        "--colors",
        action=BooleanOptionalAction,
        help=(
            "Force or prevent a colored output"
            " (default: true if stdin is a tty, false otherwise)"
        ),
    )
    parser.add_argument(
        "--cache-path",
        help="Directory where to store the persistent cache (default: %(default)s)",
        default="./.wast",
    )
    parser.add_argument(
        "--skip-missing-interpreters",
        action="store_true",
        help="Don't report a missing interpreter as a failure, and skip the step instead",
    )

    return parser.parse_args(args)


def _load_user_config(
    pipeline: _pipeline.Pipeline, config_file: str
) -> _pipeline.Pipeline:
    _pipeline.set_pipeline(pipeline)

    spec = importlib.util.spec_from_file_location("wastfile", config_file)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    return pipeline


def _execute_pipeline(
    config: Config,
    steps: Optional[List[str]],
    only_steps: Optional[List[str]],
    except_steps: Optional[List[str]],
    clean: bool,
    list_only: bool,
    list_dependencies: bool,
) -> None:
    pipeline = _pipeline.Pipeline(config)

    context = Context()
    pipeline = context.run(_load_user_config, pipeline, config.user_config)
    LOGGER.debug("Pipeline definition found at %s", config.user_config)

    if list_only or list_dependencies:
        pipeline.list_all_steps(
            steps, only_steps, except_steps, list_dependencies
        )
        return

    if clean:
        LOGGER.debug("Cleaning workspace")
        with suppress(FileNotFoundError):
            shutil.rmtree(config.cache_path)

    pipeline.execute(steps, only_steps, except_steps)


def main(sys_args: Optional[List[str]] = None) -> None:
    args = _parse_args(sys_args)
    verbosity = args.verbose - args.quiet
    config = Config(
        args.config,
        args.cache_path,
        verbosity,
        args.colors,
        args.jobs,
        args.skip_missing_interpreters,
        args.no_setup,
        args.setup_only,
        args.fail_fast,
    )
    setup_logging(logging.INFO - 10 * verbosity, config.colors)

    try:
        _execute_pipeline(
            config,
            args.steps,
            args.only_steps,
            args.except_steps,
            args.clean,
            args.list_only,
            args.list_dependencies,
        )
    except BaseWastException as exc:
        LOGGER.error("%s", exc)
        raise SystemExit(exc.exit_code) from exc
