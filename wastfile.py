from pathlib import Path

import wast
import wast.predefined

REQUIREMENTS = "-rrequirements/requirements.txt"
DOCS_REQUIREMENTS = "-rrequirements/requirements-docs.txt"
TEST_REQUIREMENTS = "-rrequirements/requirements-test.txt"
TYPES_REQUIREMENTS = "-rrequirements/requirements-types.txt"
OLDEST_SUPPORTED_PYTHON = "3.9"
SUPPORTED_PYTHONS = ["3.9", "3.10", "3.11"]
PYTHON_FILES = ["docs", "src/", "tests/", "setup.py", "wastfile.py"]

ROOT_PATH = Path(__file__).parent
DOCS_SOURCES_PATH = ROOT_PATH / "docs"
ARTIFACTS_PATH = ROOT_PATH / "_artifacts"


##
# Formatting
##
wast.register_managed_step(wast.predefined.unimport())
wast.register_managed_step(wast.predefined.isort(files=PYTHON_FILES))
wast.register_managed_step(wast.predefined.docformatter(files=PYTHON_FILES))
wast.register_managed_step(wast.predefined.black())

# With auto fix
wast.register_managed_step(
    wast.predefined.unimport(
        additional_arguments=["--diff", "--remove", "--check", "--gitignore"],
    ),
    name="unimport:fix",
    run_by_default=False,
)
wast.register_managed_step(
    wast.predefined.isort(
        additional_arguments=["--atomic"], files=PYTHON_FILES
    ),
    name="isort:fix",
    run_by_default=False,
    requires=["unimport:fix"],
)
wast.register_managed_step(
    wast.predefined.docformatter(
        additional_arguments=["--recursive", "--in-place"], files=PYTHON_FILES
    ),
    name="docformatter:fix",
    run_by_default=False,
    requires=["isort:fix"],
)
wast.register_managed_step(
    wast.predefined.black(additional_arguments=[]),
    name="black:fix",
    requires=["isort:fix", "docformatter:fix"],
    run_by_default=False,
)
wast.register_step_group(
    name="fix",
    requires=["isort:fix", "docformatter:fix", "black:fix"],
    run_by_default=False,
)


##
# Linting
##
wast.register_managed_step(
    wast.predefined.mypy(files=PYTHON_FILES),
    dependencies=[
        "mypy",
        DOCS_REQUIREMENTS,
        TEST_REQUIREMENTS,
        TYPES_REQUIREMENTS,
    ],
    python=OLDEST_SUPPORTED_PYTHON,
)
wast.register_managed_step(
    wast.predefined.pylint(files=PYTHON_FILES),
    dependencies=[
        REQUIREMENTS,
        DOCS_REQUIREMENTS,
        TEST_REQUIREMENTS,
        "pylint",
    ],
    python=OLDEST_SUPPORTED_PYTHON,
)
wast.register_step_group("lint", ["mypy", "pylint"])

##
# Packaging
##
wast.register_managed_step(
    wast.predefined.package(isolate=False),
    dependencies=["build", "setuptools>=61.0.0", "wheel"],
)

##
# Testing
##
wast.register_managed_step(
    wast.parametrize("python", SUPPORTED_PYTHONS)(wast.predefined.pytest()),
    dependencies=[TEST_REQUIREMENTS],
    requires=["package"],
)

##
# Reports
##
wast.register_managed_step(
    wast.predefined.coverage(
        reports=[
            ["report", "--show-missing"],
            ["html", f"--directory={ARTIFACTS_PATH / 'coverage/html'}"],
            ["xml", f"-o{ARTIFACTS_PATH / 'coverage/coverage.xml'}"],
        ],
    ),
    requires=["pytest"],
    dependencies=["coverage[toml]"],
)

##
# Docs
##
# TODO: this technically doesn't clean the autogenerated api files, we should
#       clean them up on wast --clean.
wast.register_managed_step(
    wast.parametrize(
        ("builder", "output"),
        [
            ("html", ARTIFACTS_PATH / "docs"),
            ("linkcheck", None),
            ("spelling", None),
        ],
        ids=["html", "linkcheck", "spelling"],
    )(
        wast.predefined.sphinx(
            sourcedir=DOCS_SOURCES_PATH,
            warning_as_error=True,
        )
    ),
    name="docs",
    dependencies=[DOCS_REQUIREMENTS],
    requires=["package"],
    run_by_default=False,
)

##
# Publishing
##
# FIXME: this is wasteful as it will install the wheel in the venv, we don't
#        need this. We should be able to skip the seutp of dependents
wast.register_managed_step(
    wast.predefined.twine(), name="twine:check", requires=["package"]
)
wast.register_managed_step(
    wast.predefined.twine(
        additional_arguments=[
            "upload",
            "--verbose",
            "--sign",
            "--non-interactive",
        ],
    ),
    name="twine:upload",
    passenv=["TWINE_REPOSITORY", "TWINE_USERNAME", "TWINE_PASSWORD"],
    requires=["package", "twine:check"],
    run_by_default=False,
)
