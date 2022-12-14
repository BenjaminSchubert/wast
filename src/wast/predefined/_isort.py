from typing import List, Optional, Sequence

# XXX: All imports here should be done from the top level. If we need it,
#      users might need it
from .. import Step, StepRunner, build_parameters, set_defaults


@set_defaults(
    {
        "dependencies": ["isort[colors]"],
        "additional_arguments": ["--check-only", "--diff"],
        "files": ["."],
    }
)
class Isort(Step):
    def __init__(self) -> None:
        self.__name__ = "isort"

    def __call__(
        self,
        step: StepRunner,
        files: Sequence[str],
        additional_arguments: List[str],
    ) -> None:
        if step.config.colors:
            additional_arguments.append("--color")

        step.run(["isort", *additional_arguments, *files])


def isort(
    *,
    files: Optional[Sequence[str]] = None,
    additional_arguments: Optional[List[str]] = None,
) -> Step:
    """
    Run `the isort formatter`_ against your python source code.

    By default, it will depend on :python:`["isort[colors]"]`, when registered
    with :py:func:`wast.register_managed_step`.

    :param files: The list of files or directories to run ``isort`` against.
                  Defaults to :python:`["."]`.
    :param additional_arguments: Additional arguments to pass to the ``isort``
                                 invocation.
                                 Defaults to :python:`["--check-only", "--diff"]`.
    :return: The step so that you can add additional parameters to it if needed.

    .. tip::

        isort can be quite slow to find all files it needs to handle, you might
        want to limit the number of directories searched.

    :Examples:

        In order to verify your code but not change it, for a step
        named **isort**:

        .. code-block::

            wast.register_managed_step(
                wast.predefined.isort(files["src", "tests", "wastfile.py", "setup.py"])
            )

        Or, in order to automatically fix your code, but only if requested:

        .. code-block::

            wast.register_managed_step(
                wast.predefined.isort(
                    additional_arguments=["--atomic"],
                    files=["src,", "tests", "wastfile.py", "setup.py"],
                ),
                # NOTE: this name is arbitrary, you could omit it, or specify
                #       something else. We suffix in our documentation all
                #       operations that will have destructive effect on the source
                #       code by ``:fix``
                name="isort:fix",
                run_by_default=False,
            )
    """
    return build_parameters(
        files=files,
        additional_arguments=additional_arguments,
    )(Isort())
