from src.judge.main import hello_world

def test_hello_world():
    message = hello_world()
    assert message == {"message": "Judge says hello"}
