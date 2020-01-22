import pytest
import pandas as pd


@pytest.fixture
def number():
    return 5


@pytest.fixture
def setup():
    with pd.HDFStore("data/EUR_USD/M15/price.h5") as store:
        data = store["M"]

    return data
