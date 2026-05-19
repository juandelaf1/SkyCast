import pytest
import math
from app.core.utils import haversine


class TestHaversine:
    def test_madrid_centro(self):
        dist = haversine(40.4168, -3.7038, 40.4168, -3.7038)
        assert dist == 0.0

    def test_madrid_alcala(self):
        dist = haversine(40.4168, -3.7038, 40.4821, -3.3644)
        assert 25 < dist < 35

    def test_simetric(self):
        d1 = haversine(40.0, -3.0, 41.0, -4.0)
        d2 = haversine(41.0, -4.0, 40.0, -3.0)
        assert abs(d1 - d2) < 0.001

    def test_poles(self):
        d = haversine(90.0, 0.0, 90.0, 180.0)
        assert d == pytest.approx(0.0, abs=1e-10)

    def test_equator(self):
        d = haversine(0.0, 0.0, 0.0, 180.0)
        assert 20000 < d < 20100

    def test_madrid_new_york(self):
        d = haversine(40.4168, -3.7038, 40.7128, -74.0060)
        assert 5700 < d < 5900

    def test_antipodal(self):
        d = haversine(0.0, 0.0, 0.0, 179.9)
        assert 19900 < d < 20100

    def test_madrid_barcelona(self):
        d = haversine(40.4168, -3.7038, 41.3874, 2.1686)
        assert 500 < d < 510