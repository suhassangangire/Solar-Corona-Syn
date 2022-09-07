
# Sun-Corona-Syn

General Toolkit for Modeling Solar Coronas.

[![PyPI version](https://badge.fury.io/py/Sun-Corona-Syn.svg)](https://[badge.fury.io/py/Sun-Corona-Syn]([https://pypi.org/](https://pypi.org/)))
[![ASCL:1801.012](https://img.shields.io/badge/ascl-1801.012-blue.svg?colorB=262255)](http://ascl.net/1801.012)

[![Powered by emcee](https://img.shields.io/badge/powered_by-emcee-EB5368.svg?style=flat)](https://emcee.readthedocs.io)
[![Powered by AstroPy](https://img.shields.io/badge/powered_by-AstroPy-EB5368.svg?style=flat)](http://www.astropy.org)
[![Powered by celerite](https://img.shields.io/badge/powered_by-celerite-EB5368.svg?style=flat)](https://celerite.readthedocs.io)

## Attribution

Written by Suhas Sangangire


## Features

With Sun-Corona-Syn you can


- *Optimize*
  - leverages the suite of minimizers in [scipy.optimize](https://docs.scipy.org/doc/scipy/reference/optimize.html)
- *Run MCMC*
  - leverages the [emcee](http://dfm.io/emcee/) package for MCMC exploration of the posterior probability distribution
- *Visualize*
  - creates quicklook summary plots and statistics
 
Sun-Corona-Syn is

- *Flexible*
  - fix/float parameters that are indexed as strings (emulates [lmfit](https://github.com/lmfit/lmfit-py/) API)
  - convert between different parameterizations e.g. `e omega <-> sqrtecosw sqrtesinw`
  - incorporate RVs from multiple telescopes
- *Extensible* 
  - Object-oriented programing makes adding new likelihoods, priors, etc. easy
- *Scriptable*
  - Code can be run through a convenient Command-line Interface (CLI) 
- *Fast*
   - Kepler's equation solved in C (slower Python solver also included)
   - MCMC is multi-threaded


 Thank You.
