# Example Keplerian fit configuration file

# Required packages for setup
import os
import pandas as pd
import numpy as np
import Sun-Corona-Syn

# Define global planetary system and dataset parameters
starname = 'HD164922'
nplanets = 2    # number of planets in the system
instnames = ['k', 'j', 'a']    # list of instrument names. Can be whatever you like (no spaces) but should match 'tel' column in the input file.
ntels = len(instnames)       # number of instruments with unique velocity zero-points
fitting_basis = 'per tc secosw sesinw logk'    # Fitting basis, see Sun-Corona-Syn.basis.BASIS_NAMES for available basis names
bjd0 = 0   # reference epoch for RV timestamps (i.e. this number has been subtracted off your timestamps)
planet_letters = {1: 'b', 2: 'c'}   # map the numbers in the Parameters keys to planet letters (for plotting and tables)


# Define prior centers (initial guesses) in a basis of your choice (need not be in the fitting basis)
anybasis_params = Sun-Corona-Syn.Parameters(nplanets,basis='per tc e w k', planet_letters=planet_letters)    # initialize Parameters object

anybasis_params['per1'] = Sun-Corona-Syn.Parameter(value=1206.3)      # period of 1st planet
anybasis_params['tc1'] = Sun-Corona-Syn.Parameter(value=2456779.)     # time of inferior conjunction of 1st planet
anybasis_params['e1'] = Sun-Corona-Syn.Parameter(value=0.01)          # eccentricity of 1st planet
anybasis_params['w1'] = Sun-Corona-Syn.Parameter(value=np.pi/2.)      # argument of periastron of the star's orbit for 1st planet
anybasis_params['k1'] = Sun-Corona-Syn.Parameter(value=10.0)          # velocity semi-amplitude for 1st planet
anybasis_params['per2'] = Sun-Corona-Syn.Parameter(value=75.771)      # same parameters for 2nd planet ...
anybasis_params['tc2'] = Sun-Corona-Syn.Parameter(value=2456277.6)
anybasis_params['e2'] = Sun-Corona-Syn.Parameter(value=0.01)
anybasis_params['w2'] = Sun-Corona-Syn.Parameter(value=np.pi/2.)
anybasis_params['k2'] = Sun-Corona-Syn.Parameter(value=1)

time_base = 2456778          # abscissa for slope and curvature terms (should be near mid-point of time baseline)
anybasis_params['dvdt'] = Sun-Corona-Syn.Parameter(value=0.0)         # slope: (If rv is m/s and time is days then [dvdt] is m/s/day)
anybasis_params['curv'] = Sun-Corona-Syn.Parameter(value=0.0)        # curvature: (If rv is m/s and time is days then [curv] is m/s/day^2)

# analytically calculate gamma if vary=False and linear=True
anybasis_params['gamma_k'] = Sun-Corona-Syn.Parameter(value=0.0)       # velocity zero-point for hires_rk
anybasis_params['gamma_j'] = Sun-Corona-Syn.Parameter(value=1.0)       # "                   "   hires_rj
anybasis_params['gamma_a'] = Sun-Corona-Syn.Parameter(value=0.0)       # "                   "   hires_apf

anybasis_params['jit_k'] = Sun-Corona-Syn.Parameter(value=2.6)        # jitter for hires_rk
anybasis_params['jit_j'] = Sun-Corona-Syn.Parameter(value=2.6)         # "      "   hires_rj
anybasis_params['jit_a'] = Sun-Corona-Syn.Parameter(value=2.6)         # "      "   hires_apf

# Convert input orbital parameters into the fitting basis
params = anybasis_params.basis.to_any_basis(anybasis_params,fitting_basis)

# Set the 'vary' attributes of each of the parameters in the fitting basis. A parameter's 'vary' attribute should
# be set to False if you wish to hold it fixed during the fitting process. By default, all 'vary' parameters
# are set to True.
params['dvdt'].vary = False
params['curv'].vary = False


# Load radial velocity data, in this example the data is contained in
# an ASCII file, must have 'time', 'mnvel', 'errvel', and 'tel' keys
# the velocities are expected to be in m/s
data = pd.read_csv(os.path.join(Sun-Corona-Syn.DATADIR,'164922_fixed.txt'), sep=' ')


# Define prior shapes and widths here.
priors = [
    Sun-Corona-Syn.prior.EccentricityPrior( nplanets ),           # Keeps eccentricity < 1
    Sun-Corona-Syn.prior.Gaussian('tc1', params['tc1'].value, 300.0),    # Gaussian prior on tc1 with center at tc1 and width 300 days
    Sun-Corona-Syn.prior.HardBounds('jit_k', 0.0, 10.0),
    Sun-Corona-Syn.prior.HardBounds('jit_j', 0.0, 10.0),
    Sun-Corona-Syn.prior.HardBounds('jit_a', 0.0, 10.0)
]


# optional argument that can contain stellar mass in solar units (mstar) and
# uncertainty (mstar_err). If not set, mstar will be set to nan.
stellar = dict(mstar=0.874, mstar_err=0.012)

