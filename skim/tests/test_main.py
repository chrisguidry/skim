def test_creates_app():
    from skim.__main__ import app
    assert app
    assert app.router is not None
