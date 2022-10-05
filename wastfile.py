from pathlib import Path

import wast
import wast.predefined

REQUIREMENTS = "-rrequirements/requirements.txt"
TEST_REQUIREMENTS = "-rrequirements/requirements-test.txt"
OLDEST_SUPPORTED_PYTHON = "3.9"
SUPPORTED_PYTHONS = ["3.9", "3.10"]
PYTHON_FILES = ["src/", "tests/", "setup.py", "wastfile.py"]
ARTIFACTS_PATH = Path(__file__).parent.joinpath("_artifacts")

##
# Formatting
##
wast.predefined.isort(files=PYTHON_FILES)
wast.predefined.black()

# With auto fix
wast.predefined.isort(
    name="isort:fix",
    additional_arguments=["--atomic"],
    run_by_default=False,
    files=PYTHON_FILES,
)
wast.predefined.black(
    name="black:fix",
    additional_arguments=[],
    requires=["isort:fix"],
    run_by_default=False,
)
wast.register_step_group(
    name="fix", requires=["isort:fix", "black:fix"], run_by_default=False
)


##
# Linting
##
wast.predefined.mypy(
    files=PYTHON_FILES,
    dependencies=["mypy", "types-colorama", TEST_REQUIREMENTS],
    python=OLDEST_SUPPORTED_PYTHON,
)
wast.predefined.pylint(
    files=["src", "tests"],
    dependencies=[REQUIREMENTS, TEST_REQUIREMENTS, "pylint"],
    python=OLDEST_SUPPORTED_PYTHON,
)
wast.register_step_group("lint", ["mypy", "pylint"])

##
# Packaging
##
wast.predefined.package(
    isolate=False, dependencies=["build", "setuptools>=61.0.0", "wheel"]
)

##
# Testing
##
wast.predefined.pytest(
    dependencies=[TEST_REQUIREMENTS],
    requires=["package"],
    parametrize=wast.parametrize("python", SUPPORTED_PYTHONS),
)

##
# Reports
##
wast.predefined.coverage(
    reports=[
        ["report", "--show-missing"],
        ["html", f"--directory={ARTIFACTS_PATH / 'coverage/html'}"],
        ["xml", f"-o{ARTIFACTS_PATH / 'coverage/coverage.xml'}"],
    ],
    requires=["pytest"],
    dependencies=["coverage[toml]"],
)

##
# Publishing
##
# FIXME: this is wasteful as it will install the wheel in the venv, we don't
#        need this. We should be able to skip the seutp of dependents
wast.predefined.twine(name="twine:check", requires=["package"])
wast.predefined.twine(
    name="twine:upload",
    requires=["package", "twine:check"],
    additional_arguments=[
        "upload",
        "--verbose",
        "--sign",
        "--non-interactive",
    ],
    passenv=["TWINE_REPOSITORY", "TWINE_USERNAME", "TWINE_PASSWORD"],
    run_by_default=False,
)
