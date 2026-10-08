def test_estructura_s0():
    from pathlib import Path

    assert Path(".github/workflows/ci.yml").is_file()
    assert Path(".github/CODEOWNERS").is_file()