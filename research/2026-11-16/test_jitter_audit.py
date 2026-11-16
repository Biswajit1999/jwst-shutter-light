import pytest
from jitter_audit import mean_transmission,correlated_jitter_quadrature
W=[0.2,0.46]; S=[0.06,0.08]; MU=[0.01,-0.02]; J=[0.015,0.03]

def test_no_jitter():
    assert correlated_jitter_quadrature(W,S,MU,[0,0],0)==pytest.approx(mean_transmission(W,S,MU,[0,0]),abs=1e-12)

def test_independent_jitter():
    assert correlated_jitter_quadrature(W,S,MU,J,0,order=32)==pytest.approx(mean_transmission(W,S,MU,J),abs=1e-9)

def test_correlation_sign_symmetry():
    a=correlated_jitter_quadrature(W,S,[0,0],J,0.7)
    b=correlated_jitter_quadrature(W,S,[0,0],J,-0.7)
    assert a==pytest.approx(b,abs=1e-12)

def test_jitter_reduces_centered_throughput():
    assert mean_transmission(W,S,[0,0],J)<mean_transmission(W,S,[0,0],[0,0])

def test_invalid():
    with pytest.raises(ValueError): correlated_jitter_quadrature(W,S,MU,J,1)
    with pytest.raises(ValueError): mean_transmission(W,S,MU,[-1,0])
