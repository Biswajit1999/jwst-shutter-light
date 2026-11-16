"""Gaussian PSF rectangular aperture; conditional on an open shutter."""
import math
import numpy as np
from scipy.special import ndtr
from numpy.polynomial.hermite import hermgauss

def _inside(width,sigma,centre):
    if width<=0 or sigma<=0 or not (np.isfinite(width) and np.isfinite(sigma) and np.all(np.isfinite(centre))):
        raise ValueError("positive finite width/sigma and finite offsets required")
    return ndtr((width/2-centre)/sigma)-ndtr((-width/2-centre)/sigma)

def mean_transmission(widths,psf_sigmas,mean_offsets,jitter_sigmas):
    vals=[np.asarray(x,float) for x in (widths,psf_sigmas,mean_offsets,jitter_sigmas)]
    if any(x.shape!=(2,) or not np.all(np.isfinite(x)) for x in vals):
        raise ValueError("finite length-two vectors required")
    w,s,mu,j=vals
    if np.any(w<=0) or np.any(s<=0) or np.any(j<0):
        raise ValueError("invalid width/PSF/jitter")
    return float(np.prod([_inside(w[k],math.hypot(s[k],j[k]),mu[k]) for k in range(2)]))

def correlated_jitter_quadrature(widths,psf_sigmas,mean_offsets,jitter_sigmas,rho,order=24):
    if not np.isfinite(rho) or abs(rho)>=1 or order<2:
        raise ValueError("require |rho|<1 and order>=2")
    w,s,mu,j=[np.asarray(x,float) for x in (widths,psf_sigmas,mean_offsets,jitter_sigmas)]
    if any(x.shape!=(2,) or not np.all(np.isfinite(x)) for x in (w,s,mu,j)) or np.any(w<=0) or np.any(s<=0) or np.any(j<0):
        raise ValueError("invalid aperture/PSF/jitter")
    nodes,weights=hermgauss(order)
    u=np.sqrt(2)*nodes[:,None]
    v=np.sqrt(2)*nodes[None,:]
    x=mu[0]+j[0]*u
    y=mu[1]+j[1]*(rho*u+np.sqrt(1-rho*rho)*v)
    fx=_inside(w[0],s[0],x)
    fy=_inside(w[1],s[1],y)
    return float(np.sum(weights[:,None]*weights[None,:]*fx*fy)/np.pi)
