import pytest
from pydantic import ValidationError

from kinward.config import Settings


def test_blank_optional_setup_authorization_degrades_safely() -> None:
    assert Settings(setup_authorization="").setup_authorization is None
    assert Settings(setup_authorization="   ").setup_authorization is None
    with pytest.raises(ValidationError):
        Settings(setup_authorization="too-short")
