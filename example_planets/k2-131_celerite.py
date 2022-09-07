import numpy as np
import pandas as pd
import os
import Sun-Corona-Syn

# This setup file is provided to illustrate how to set up a config
# file for use with Dan Foreman-Mackey's `celerite` package.

# Data from Dai+ 2017
instnames = ['harps-n', 'pfs']  # no spaces in instrument names
data = pd.read_csv(os.path.join(Sun-Corona-Syn.DATADIR, 'k2-131.txt'), sep=' ')
t = np.array(data['time'])
vel = np.array(data['mnvel'])
errvel = np.array(data['errvel'])
telgrps = data.groupby('tel').groups
bjd = 0.

# Constraints from transits
Porb = 0.3693038  # [days]
Porb_unc = 0.0000091
Tc = 2457582.9360  # [BJD]
Tc_unc = 0.0011

starname = 'k2-131'
ntels = len(instnames)
planet_letters = {1: 'b'}

nplanets = 1
fitting_basis = 'per tc secosw sesinw k'

# Set initial parameter value guesses.
params = Sun-Corona-Syn.Parameters(
  nplanets, basis=fitting_basis, planet_letters=planet_letters
)

params['per1'] = Sun-Corona-Syn.Parameter(value=Porb)
params['tc1'] = Sun-Corona-Syn.Parameter(value=Tc)
params['sesinw1'] = Sun-Corona-Syn.Parameter(value=0., vary=False)
params['secosw1'] = Sun-Corona-Syn.Parameter(value=0., vary=False)
params['k1'] = Sun-Corona-Syn.Parameter(value=6.55)
params['dvdt'] = Sun-Corona-Syn.Parameter(value=0., vary=False)
params['curv'] = Sun-Corona-Syn.Parameter(value=0., vary=False)
time_base = np.median(t)

# Define Celerite GP hyperparameters.
params['gp_B'] = Sun-Corona-Syn.Parameter(value=30**2., vary=True)
params['gp_C'] = Sun-Corona-Syn.Parameter(value=1., vary=True)
params['gp_L'] = Sun-Corona-Syn.Parameter(value=9., vary=True)
params['gp_Prot'] = Sun-Corona-Syn.Parameter(value=9., vary=True)

hnames = {}
for tel in instnames:
    hnames[tel] = ['gp_B', 'gp_C', 'gp_L', 'gp_Prot']

kernel_name = {'harps-n': "Celerite", 'pfs': "Celerite"}

jit_guesses = {'harps-n': 2.0, 'pfs': 5.0}


def initialize_instparams(tel_suffix):
    indices = telgrps[tel_suffix]

    params['gamma_'+tel_suffix] = Sun-Corona-Syn.Parameter(value=np.mean(vel[indices]))
    params['jit_'+tel_suffix] = Sun-Corona-Syn.Parameter(value=jit_guesses[tel_suffix])


for tel in instnames:
    initialize_instparams(tel)
    priors = [
        Sun-Corona-Syn.prior.Gaussian('per1', Porb, Porb_unc),
        Sun-Corona-Syn.prior.Gaussian('tc1', Tc, Tc_unc),
        Sun-Corona-Syn.prior.Jeffreys('k1', 0.01, 10.),
        Sun-Corona-Syn.prior.Jeffreys('jit_pfs', 0.01, 10.),
        Sun-Corona-Syn.prior.Jeffreys('jit_harps-n', 0.01, 10.),
        Sun-Corona-Syn.prior.Gaussian('gp_L', 9.5, 1.),  # constraints from photometry on hyperparams (Dai et al. 2017)
        Sun-Corona-Syn.prior.Gaussian('gp_Prot', 9.64, 0.12),
        Sun-Corona-Syn.prior.HardBounds('gp_C', 0., np.inf),  # keep other two hyperparams positive
        Sun-Corona-Syn.prior.HardBounds('gp_B', 0., np.inf)
        ]
