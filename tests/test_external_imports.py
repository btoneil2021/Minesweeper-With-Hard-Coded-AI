from minesweeper.external import __all__


def test_external_package_exports_expected_modules() -> None:
    assert "ScreenCapture" in __all__
    assert "TileClassifier" in __all__
    assert "ScreenBoardReader" in __all__
