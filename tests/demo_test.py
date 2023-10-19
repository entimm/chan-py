import pytest


def add(a, b):
    return a + b

def test_add():
    assert add(1, 2) == 3
    assert add(5, 5) == 10

@pytest.fixture
def sample_data():
    return [1, 2, 3, 4, 5]

def test_mean(sample_data):
    assert sum(sample_data) / len(sample_data) == 3

@pytest.mark.parametrize("a,b,expected", [(1, 2, 3), (4, 5, 9), (10, 20, 30)])
def test_add(a, b, expected):
    assert add(a, b) == expected

@pytest.mark.skip(reason="Skipping this test for now.")
def test_skipped():
    assert False

@pytest.mark.xfail
def test_expected_failure():
    assert False