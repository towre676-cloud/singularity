"""Empirical repeated-view signal/noise decomposition in physical coordinates.

Scientific dependencies are optional. This is not an exact quotient of actual
athlete behaviour: covariance estimates and independent-attempt assumptions can
fail. Return physical-coordinate posterior means, never mix eigen-coordinates
from different training folds.
"""
from __future__ import annotations
from dataclasses import dataclass
import numpy as np

@dataclass(frozen=True)
class ReliableModes:
    mean: np.ndarray
    signal: np.ndarray
    noise: np.ndarray
    eigenvalues: np.ndarray
    training_groups: tuple
    repeat_df: int
    clipped_nonpositive_modes: int
    calibrated: bool

    @classmethod
    def fit(cls, groups, *, training_groups, noise_ridge_fraction=.05):
        """One multichannel vector per independent attempt, not per speed gate."""
        if not 0<noise_ridge_fraction<=1:raise ValueError('noise ridge fraction must lie in (0,1]')
        allowed=set(training_groups)
        data={g:np.asarray(v,float) for g,v in groups.items() if g in allowed and len(v)}
        if not data:raise ValueError('no training attempt vectors')
        widths={v.shape[1] for v in data.values() if v.ndim==2}
        if len(widths)!=1 or any(v.ndim!=2 or not np.isfinite(v).all() for v in data.values()):
            raise ValueError('finite equal-width independent attempt vectors required')
        d=next(iter(widths));means=np.asarray([v.mean(axis=0) for v in data.values()])
        mean=means.mean(axis=0);df=sum(len(v)-1 for v in data.values())
        if df<2 or len(data)<3:
            return cls(mean,np.zeros((d,d)),np.eye(d),np.zeros(d),tuple(sorted(data)),df,d,False)
        noise=sum(((v-v.mean(axis=0)).T@(v-v.mean(axis=0)) for v in data.values()),np.zeros((d,d)))/df
        scale=max(float(np.trace(noise)/d),1e-10)
        noise=(noise+noise.T)/2 + noise_ridge_fraction*scale*np.eye(d)
        between=np.atleast_2d(np.cov(means,rowvar=False,ddof=1))-noise*np.mean([1/len(v) for v in data.values()])
        # Generalized S/N spectrum. Negative empirical signal modes are
        # explicitly recorded and clipped, not declared physically absent.
        e,u=np.linalg.eigh(noise);root=(u*np.sqrt(e))@u.T;invroot=(u*(1/np.sqrt(e)))@u.T
        lam,q=np.linalg.eigh(invroot@between@invroot)
        signal=root@(q*np.maximum(lam,0.))@q.T@root
        return cls(mean,(signal+signal.T)/2,noise,lam,tuple(sorted(data)),df,int(np.sum(lam<=0)),True)

    def posterior(self,attempts):
        x=np.asarray(attempts,float)
        d=len(self.mean)
        if x.size==0 or not self.calibrated:return self.mean.copy(),self.signal.copy()
        if x.ndim!=2 or x.shape[1]!=d or not np.isfinite(x).all():raise ValueError('incompatible attempt vectors')
        r=self.noise/len(x)
        gain=np.linalg.solve(self.signal+r,self.signal).T
        mean=self.mean+gain@(x.mean(axis=0)-self.mean)
        cov=self.signal-gain@self.signal
        return mean,(cov+cov.T)/2

    def receipt(self):
        return {'training_groups':len(self.training_groups),'repeat_degrees_of_freedom':self.repeat_df,
                'empirical_generalized_signal_noise_eigenvalues':self.eigenvalues.tolist(),
                'clipped_nonpositive_modes':self.clipped_nonpositive_modes,'calibrated':self.calibrated,
                'noise_covariance':self.noise.tolist(),'signal_covariance':self.signal.tolist(),
                'scope':'method-of-moments independent-attempt Gaussian working model; window correlation retained; physical-coordinate output; covariance clipping is an estimator, not a proof of absent biology'}
