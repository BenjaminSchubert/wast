from .mixins import BaseFormatterTest


class TestBlack(BaseFormatterTest):
    wastfile = """\
from wast.predefined import black

black()
black(
    name="black:fix",
    additional_arguments=[],
    run_by_default=False,
)
"""
    autofix_step = "black:fix"
    invalid_file = "x =  1"
    valid_file = "x = 1\n"
