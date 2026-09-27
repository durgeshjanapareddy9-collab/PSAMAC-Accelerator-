"""Tests for the Python model (run with `make test-model`)."""

import numpy as np
import pytest

from model.approx_mul import N_MAX, approx_mul, compute_lut, dropped_weight, exact_lut

EXACT = exact_lut()
ALL_N = range(N_MAX + 1)


def test_n0_is_exact():
    """N = 0 drops nothing, so it must equal a*b for every pair."""
    assert np.array_equal(compute_lut(0), EXACT)


@pytest.mark.parametrize("n", ALL_N)
def test_error_never_negative(n):
    """Dropping bits can only lower the result: exact - approx >= 0."""
    assert (EXACT - compute_lut(n)).min() >= 0


@pytest.mark.parametrize("n", ALL_N)
def test_med_closed_form(n):
    """MED(N) = 0.25 * (sum of 2^(i+j) over i+j < N), over all 65,536 pairs."""
    med = (EXACT - compute_lut(n)).mean()
    assert med == pytest.approx(0.25 * dropped_weight(n), abs=1e-9)


@pytest.mark.parametrize("n", ALL_N)
def test_scalar_matches_lut(n):
    """The scalar function and the numpy LUT agree (spot-check 500 pairs)."""
    rng = np.random.default_rng(n)
    table = compute_lut(n)
    for a, b in rng.integers(0, 256, size=(500, 2)):
        assert approx_mul(int(a), int(b), n) == table[a, b]


def test_n4_edmax_49_for_256_pairs():
    """N = 4: largest error is 1 + 2*2 + 3*4 + 4*8 = 49, hit by 16 x 16 = 256 pairs
    (all pairs whose low four bits of a and of b are all ones)."""
    ed = EXACT - compute_lut(4)
    assert ed.max() == 49
    assert np.count_nonzero(ed == 49) == 256


def test_n4_plus_12_edmax_37_for_256_pairs():
    """N = 4 with a constant +12 added: errors now range from -12 to 37, so
    EDmax = |largest error| = 37, again for 256 pairs. This matches the EDmax
    and frequency reported for Design 1 in Rather et al. 2025 -- a sanity check,
    not proof that their design is exactly this."""
    ed = np.abs(EXACT - (compute_lut(4) + 12))
    assert ed.max() == 37
    assert np.count_nonzero(ed == 37) == 256
