from .mixins import BaseFormatterTest


class TestUnimport(BaseFormatterTest):
    wastfile = """\
from wast.predefined import unimport

unimport()
unimport(
    name="unimport:fix",
    additional_arguments=["--diff", "--remove", "--check"],
    run_by_default=False,
)
"""

    autofix_step = "unimport:fix"
    invalid_file = "import os"
    valid_file = ""
