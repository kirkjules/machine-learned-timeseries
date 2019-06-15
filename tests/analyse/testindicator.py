import os
import statistics
import unittest
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from htp.analyse import indicator


class TestIndicator(unittest.TestCase):

    def test_concat_fidelity_sma(self):
        
        # Generate test dataset.
        samples = 100
        time = np.linspace(0, 400, num=samples)
        datapoints = ([np.sin(t * samples * 2 * np.pi) for t in time])
        dates = pd.date_range("20130101", periods=samples)
        dataset = pd.DataFrame({"close": datapoints}, index=dates)
        
        # Returns a new dataframe with only one column.
        dataset_sma_fast = indicator.smooth_moving_average(dataset, period=5)
        # Returns a new dataframe with two columns.
        dataset_sma_fast_slow = indicator.smooth_moving_average(
            dataset, df2=dataset_sma_fast, period=10, concat=True)
        self.assertEqual(set(dataset_sma_fast.index),
                         set(dataset_sma_fast_slow.index))

    def test_sma_fidelity(self):
        
        # Generate test dataset.
        samples = 100
        time = np.linspace(0, 400, num=samples)
        datapoints = ([np.sin(t * samples * 2 * np.pi) for t in time])
        dates = pd.date_range("20130101", periods=samples)
        dataset = pd.DataFrame({"close": datapoints}, index=dates)

        s = []
        for i in range(5):
            s.append(dataset.iloc[i, 0])

        dataset_sma_fast = indicator.smooth_moving_average(dataset, period=5)

        self.assertEqual(np.round(statistics.mean(s), decimals=5),
                         np.round(dataset_sma_fast.iloc[4, 0], decimals=5))

    def test_file_generation(self):
        
        # Generate test dataset.
        samples = 100
        time = np.linspace(0, 400, num=samples)
        datapoints = ([np.sin(t * samples * 2 * np.pi) for t in time])
        dates = pd.date_range("20130101", periods=samples)
        dataset = pd.DataFrame({"close": datapoints}, index=dates)
        # Returns a new dataframe with only one column.
        dataset_sma_fast = indicator.smooth_moving_average(dataset, period=5)
        # Returns a new dataframe with two columns.
        dataset_sma_fast_slow = indicator.smooth_moving_average(
            dataset, df2=dataset_sma_fast, period=10, concat=True)
        dataset_sma_fast_slow.plot()
        fig = plt.gcf()
        fig.savefig("tests/analyse/output.png")
        self.assertIn("output.png", os.listdir("tests/analyse/"))
