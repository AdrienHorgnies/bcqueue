from unittest import TestCase

from processes import MapDoublePh
import numpy as np


class TestMap(TestCase):
    def test_get_next_state_prob_vector(self):
        """
        This test checks that test_get_next_state_prob_vector selects the right rows of the map and ph
        :return:
        """
        mapPh = MapDoublePh(np.random,
                            [[-1.3, 0.3], [0.5, -1.5]],
                            [[0.05, 0.95], [0.15, 0.85]],
                            [0.3, 0.7],
                            [[-0.1, 0.08], [0.06, -0.1]],
                            [0.2, 0.8],
                            [[-0.001, 0], [0, -0.001]],  # unused in this test
                            [0.1, 0.9])  # unused in this test

        actual = mapPh.get_next_state_prob_vector(mapPh.ph, 0, 0)
        expected = np.array([0, 0.3, 0.05, 0.95, 0, 0.08, 0.02])
        expected /= expected.sum()
        self.assertTrue(np.allclose(actual, expected))

        actual = mapPh.get_next_state_prob_vector(mapPh.ph, 1, 0)
        expected = np.array([0.5, 0, 0.15, 0.85, 0, 0.08, 0.02])
        expected /= expected.sum()
        self.assertTrue(np.allclose(actual, expected))

        actual = mapPh.get_next_state_prob_vector(mapPh.ph, 0, 1)
        expected = np.array([0, 0.3, 0.05, 0.95, 0.06, 0, 0.04])
        expected /= expected.sum()
        self.assertTrue(np.allclose(actual, expected))

        actual = mapPh.get_next_state_prob_vector(mapPh.ph, 1, 1)
        expected = np.array([0.5, 0, 0.15, 0.85, 0.06, 0, 0.04])
        expected /= expected.sum()
        self.assertTrue(np.allclose(actual, expected))
