from .mixins import BaseFormatterTest


class TestDocformatter(BaseFormatterTest):
    wastfile = """\
from wast.predefined import docformatter

docformatter()
docformatter(
    name="docformatter:fix",
    additional_arguments=["--recursive", "--in-place"],
    run_by_default=False,
)
"""
    autofix_step = "docformatter:fix"
    invalid_file = '"""   Here are some examples."""'
    valid_file = '"""Here are some examples."""'
