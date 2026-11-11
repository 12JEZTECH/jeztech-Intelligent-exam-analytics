from app.main import app
def test_health_registered():
    assert any(getattr(r,"path",None)=="/health" for r in app.routes)
