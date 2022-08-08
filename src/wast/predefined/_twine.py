import logging
import os
from typing import List, Optional

# XXX: All imports here should be done from the top level. If we need it,
#      users might need it
from .. import (
    Step,
    StepHandler,
    parametrize,
    register_managed_step,
    set_defaults,
)

LOGGER = logging.getLogger(__name__)


@set_defaults(
    {
        "dependencies": ["twine"],
        "additional_arguments": ["check", "--strict"],
        "passenv": [],
    }
)
class Twine(Step):
    def __init__(self) -> None:
        self.__name__ = "twine"

    def __call__(
        self,
        step: StepHandler,
        additional_arguments: List[str],
        passenv: List[str],
    ) -> None:
        sdists = step.get_artifacts("sdists")
        wheels = step.get_artifacts("wheels")
        if not sdists and not wheels:
            raise Exception("No sdists or wheels provided")

        env = {}
        for env_name in passenv:
            if env_name not in os.environ:
                LOGGER.warning(
                    "Asked to pass %s as environment variable, but variable is not present",
                    env_name,
                )
            else:
                env[env_name] = os.environ[env_name]

        step.run(["twine", *additional_arguments, *sdists, *wheels], env=env)


def twine(
    *,
    name: Optional[str] = None,
    additional_arguments: Optional[List[str]] = None,
    passenv: Optional[List[str]] = None,
    python: Optional[str] = None,
    requires: Optional[List[str]] = None,
    dependencies: Optional[List[str]] = None,
    run_by_default: Optional[bool] = None,
) -> None:
    """
    Run `twine`_ against the provided packages.

    This step will ask the steps it requires for :term:`artifacts<artifact>` named ``sdists`` and
    ``wheels`` and will run against those.

    :param name: The name to give to the step.
                 Defaults to :python:`"twine"`.
    :param additional_arguments: Additional arguments to pass to the ``twine``
                                 invocation.
                                 Defaults to :python:`["check", "--strict"]`.
    :param passenv: List of environment variables to pass to the ``twine``
                    invocation. Use this if, for example, you want to pass
                    ``TWINE_PASSWORD`` and ``TWINE_USERNAME``.
                    Defaults to :python:`[]`.
    :param python: The version of python to use.
                   Defaults to the version *wast* was installed with.
    :param requires: A list of other steps that this step would require.
    :param dependencies: Python dependencies needed to run this step.
                         Defaults to :python:`["twine"]`.
    :param run_by_default: Whether to run this step by default or not.
                           If :python:`True`, will default to :python:`True`

    :Examples:

        Examples here assume that you use the :py:func:`package` step like:

        .. code-block::

            # This creates a 'package' step
            wast.predefined.package()

        In order to make sure your distribution files are ready to be published:

        .. code-block::

            wast.predefined.twine(name="twine:check", requires=["package"])

        And if you want to be able to use ``wast -s twine:publish`` to publish:

        .. code-block::

            wast.predefined.twine(
                name="twine:upload",
                requires=["package", "twine:check"],
                additional_arguments=[
                    "upload",
                    "--verbose",
                    # This is not required, if you don't want to gpg-sign your
                    # distribution files
                    "--sign",
                    "--non-interactive",
                ],
                passenv=["TWINE_REPOSITORY", "TWINE_USERNAME", "TWINE_PASSWORD"],
                run_by_default=False,
            )
    """
    twine_ = Twine()

    if additional_arguments is not None:
        twine_ = parametrize(
            "additional_arguments", [additional_arguments], ids=[""]
        )(twine_)
    if passenv is not None:
        twine_ = parametrize("passenv", [passenv], ids=[""])(twine_)

    register_managed_step(
        twine_,
        dependencies,
        name=name,
        python=python,
        requires=requires,
        run_by_default=run_by_default,
    )
