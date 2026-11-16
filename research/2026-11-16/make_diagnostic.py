"""Regenerate synthetic Gaussian shutter jitter sensitivity plot."""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from jitter_audit import mean_transmission,correlated_jitter_quadrature

jitter=np.linspace(0,0.06,31)
ind=[mean_transmission([0.2,0.46],[0.06,0.08],[0.01,-0.02],[j,j]) for j in jitter]
corr=[correlated_jitter_quadrature([0.2,0.46],[0.06,0.08],[0.01,-0.02],[j,j],0.6) for j in jitter]
fig,ax=plt.subplots()
ax.plot(jitter,ind,label="Independent axes")
ax.plot(jitter,corr,label="Correlated axes (rho=0.6)")
ax.set(xlabel="Assumed pointing jitter sigma (same units as aperture)",ylabel="Mean conditional geometric transmission",title="Synthetic shutter jitter sensitivity")
ax.legend()
fig.tight_layout()
fig.savefig("synthetic_jitter_sensitivity.png",dpi=160)
