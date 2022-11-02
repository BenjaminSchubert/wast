def test_does_not_modify_files_by_default(cli, tmp_path):
    # This code is misformatted to trigger an error
    wastfile_content = """\
from wast.predefined import black
black()
"""
    wastfile_path = tmp_path.joinpath("wastfile.py")
    wastfile_path.write_text(wastfile_content)

    result = cli([], raise_on_error=False)
    assert result.exit_code == 1

    assert wastfile_path.read_text() == wastfile_content


def test_can_apply_fixes(cli, tmp_path):
    # This code is misformatted to trigger an error
    wastfile_content = """\
from wast.predefined import black
black(additional_arguments=[])
"""
    wastfile_path = tmp_path.joinpath("wastfile.py")
    wastfile_path.write_text(wastfile_content)

    cli([])
    assert wastfile_path.read_text() != wastfile_content
