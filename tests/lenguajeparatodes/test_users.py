from app import LoginForm
import pytest

@pytest.mark.parametrize(
    "password,valid",
    [
        ("", True),
        ("ABC", True),
        ("abc", True),
        ("QWEQWEQWEQWE", True),
        ("ADADASD", True),
    ]
)

def test_validate_login(password, valid):
    # Given
    form = LoginForm()
    data = {
        "username": "end",
        "password": password,
    }

    # When
    try:
        user = form.load(data)
        assert valid
        # Then
        assert user is not None
        assert user.username == data["username"]
        assert user.password == password
    except:
        assert not valid



