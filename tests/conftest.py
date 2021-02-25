import pytest


@pytest.fixture(autouse=True)
def reset_di_adapters():
    from buvar import di

    assert di.buvar_adapters.get() == {}
    yield
    di.buvar_adapters.set(di.Adapters())
