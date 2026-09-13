from pathlib import Path
from unittest.mock import patch
from submission_preflight import validate


def test_preflight_never_calls_model():
    root=Path(__file__).resolve().parents[2]
    with patch('urllib.request.urlopen',side_effect=AssertionError('network forbidden')):
        result=validate(root)
    assert result['requests'] == 250
    assert result['images'] == 11
