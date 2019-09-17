import pytest
import pandas as pd


@pytest.fixture
def number():
    return 5


@pytest.fixture
def setup():
    with pd.HDFStore("data/AUD_JPY_M15.h5") as store:
        data_mid = store["data_mid"]

    return data_mid
