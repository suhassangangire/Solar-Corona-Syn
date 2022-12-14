"""
Command Line Interface
"""
import os
from argparse import ArgumentParser

import Sun-Corona-Syn.driver


def main():
    psr = ArgumentParser(
        description="RadVel: The Radial Velocity Toolkit", prog='RadVel'
    )
    psr.add_argument('--version',
                     action='version',
                     version="%(prog)s {}".format(radvel.__version__),
                     help="Print version number and exit."
                     )

    subpsr = psr.add_subparsers(title="subcommands", dest='subcommand')

    # In the parent parser, we define arguments and options common to
    # all subcommands.
    psr_parent = ArgumentParser(add_help=False)
    psr_parent.add_argument(
        '-d', dest='outputdir', type=str,
        help="Working directory. Default is the same as the \
        configuration file (without .py)"
    )
    psr_parent.add_argument('-s', '--setup',
                            dest='setupfn', type=str,
                            help="Setup file."
                            )
    psr_parent.add_argument('--decorr',
                            dest='decorr',
                            action='store_true',
                            default=False,
                            help="Include decorrelation in likelihood."
                            )

    # Fitting
    psr_fit = subpsr.add_parser('fit', parents=[psr_parent],
                                description="Perform max-likelihood fitting"
                                )
    psr_fit.set_defaults(func=radvel.driver.fit)

    # Plotting
    psr_plot = subpsr.add_parser('plot', parents=[psr_parent],)
    psr_plot.add_argument('-t', '--type',
                          type=str, nargs='+',
                          choices=['rv', 'auto', 'corner', 'trend', 'derived'],
                          help="type of plot(s) to generate"
                          )
    psr_plot.add_argument('--plotkw', dest='plotkw', action='store', default="{}", type=eval,
                          help='''Dictionary of keywords sent to MultipanelPlot or GPMultipanelPlot.
E.g. --plotkw "{'yscale_auto': True}"' ''')
    psr_plot.add_argument('--gp',
                          dest='gp',
                          action='store_true',
                          default=False,
                          help="Make a multipanel plot with GP bands. For use only with GPLikleihood objects"
                          )

    psr_plot.set_defaults(func=radvel.driver.plots)

    # MCMC
    psr_mcmc = subpsr.add_parser('mcmc', parents=[psr_parent],
                                 description="Perform MCMC exploration"
                                 )
    psr_mcmc.add_argument('--nsteps', dest='nsteps', action='store', default=10000, type=float,
                          help='Number of steps per chain [10000]',)
    psr_mcmc.add_argument('--nwalkers', dest='nwalkers', action='store', default=50, type=int,
                          help='Number of walkers. [50]',
                          )
    psr_mcmc.add_argument('--nensembles', dest='ensembles', action='store', default=8, type=int,
                          help="Number of ensembles. Will be run in parallel on separate CPUs [8]"
                          )
    psr_mcmc.add_argument('--minAfactor', dest='minAfactor', action='store', default=40, type=float,
                          help="Minimum factor between autocorrelation time and number of samples for chains to be deemed well-mixed [50]"
                          )
    psr_mcmc.add_argument('--maxArchange', dest='maxArchange', action='store', default=.03, type=float,
                          help="Max relative-change in autocorrelation time for chains to be deemed well-mixed [.07]"
                          )
    psr_mcmc.add_argument('--maxGR', dest='maxGR', action='store', default=1.01, type=float,
                          help="Maximum G-R statistic for chains to be deemed well-mixed and halt the MCMC run [1.01]"
                          )
    psr_mcmc.add_argument('--burnGR', dest='burnGR', action='store', default=1.03, type=float,
                          help="Maximum G-R statistic to stop burn-in period [1.03]. Burn-in ends once burnGr or burnAfactor are reached."
                          )
    psr_mcmc.add_argument('--burnAfactor', dest='burnAfactor', action='store', default=25, type=float,
                          help='Minimum autocorrelation time factor to stop burn-in period [25]. Burn-in ends once burnGr or burnAfactor are reached.'
                          )
    psr_mcmc.add_argument('--minTz', dest='minTz', action='store', default=1000, type=int,
                          help="Minimum Tz to consider well-mixed [1000]"
                          )
    psr_mcmc.add_argument('--minsteps', dest='minsteps', action='store', default=1000, type=int,
                          help="Minimum number of steps per walker before convergence tests are performed [1000].\
Convergence checks will start after the minsteps threshold or the minpercent threshold has been hit."
                          )
    psr_mcmc.add_argument('--minpercent', dest='minpercent', action='store', default=5, type=float,
                          help="Minimum percentage of steps before convergence tests are performed [5]. \
Convergence checks will start after the minsteps threshold or the minpercent threshold has been hit."
                          )
    psr_mcmc.add_argument('--thin', dest='thin', action='store', default=10, type=int,
                          help="Save one sample every N steps [default=10, save every 10th sample]"
                          )
    psr_mcmc.add_argument('--serial', dest='serial', action='store', default=False, type=bool,
                          help='''If True, run MCMC in serial instead of parallel. [False]'''
                          )
    psr_mcmc.add_argument('--save', dest='save', action='store_true',
                          help='If set, MCMC chains will be saved to be continued in a future run [False]'
                          )
    psr_mcmc.add_argument('--proceed', dest='proceed', action='store_true',
                          help='If True, MCMC chains will resume from the previous run'
                          )
    psr_mcmc.set_defaults(func=radvel.driver.mcmc)

    # Derive physical parameters
    psr_physical = subpsr.add_parser('derive', parents=[psr_parent],
                                     description="Multiply MCMC chains by physical parameters. MCMC must"
                                     + "be run first"
                                     )

    psr_physical.set_defaults(func=radvel.driver.derive)

    # Information Criteria comparison (BIC/AIC)
    psr_ic = subpsr.add_parser('ic', parents=[psr_parent],)
    psr_ic.add_argument('-t', '--type', type=str, nargs='+', default='trend',
                        choices=['nplanets', 'e', 'trend', 'jit', 'gp'],
                        help="parameters to include in BIC/AIC model comparison"
                        )

    psr_ic.add_argument('-m', '--mixed', dest='mixed', action='store_true',
                        help="flag to compare all models with the fixed parameters mixed and matched rather than"
                        + " treating each model comparison separately. [default=True]"
                        )
    psr_ic.add_argument('-u', '--un-mixed', dest='mixed', action='store_false',
                        help="flag to treat each model comparison separately (without mixing them) rather "
                        + "than comparing all models with the fixed parameters mixed and matched. [default=False]"
                        )
    psr_ic.add_argument('-f', '--fixjitter', dest='fixjitter', action='store_true',
                        help="flag to fix the stellar jitters at the nominal model best-fit value [default=False]"
                        )
    psr_ic.add_argument('-n', '--no-fixjitter', dest='fixjitter', action='store_false',
                        help="flag to let the stellar jitters float during model comparisons [default=True]"
                        )
    psr_ic.add_argument('--simple', dest='simple', action='store_true',
                        help="calculate goodness of fit statistics for the current model and exit [default=False]"
                        )
    psr_ic.add_argument('-v', '--verbose', dest='verbose', action='store_true',
                        help="Print some more detail [default=False]"
                        )
    psr_ic.set_defaults(func=radvel.driver.ic_compare, fixjitter=False, unmixed=False, mixed=True, verbose=False)

    # Tables
    psr_table = subpsr.add_parser('table', parents=[psr_parent],)
    psr_table.add_argument('-t', '--type', type=str, nargs='+',
                           choices=['params', 'priors', 'rv', 'ic_compare', 'derived', 'crit'],
                           help="type of tables(s) to generate"
                           )
    psr_table.add_argument('--header', action='store_true',
                           help="include latex column header. Default just prints data rows"
                           )
    psr_table.add_argument('--name_in_title', dest='name_in_title', action='store_true', default=False,
                           help='''Include star name in table headers. Default just prints \
descriptive titles without star name [False]'''
                           )

    psr_table.set_defaults(func=radvel.driver.tables)

    # Report
    psr_report = subpsr.add_parser('report', parents=[psr_parent],
                                   description="Merge output tables and plots into LaTeX report"
                                   )
    psr_report.add_argument('--comptype', dest='comptype', action='store', default='ic', type=str,
                            help='Type of model comparison table to include. Default: ic')

    psr_report.add_argument('--latex-compiler', default='pdflatex', type=str, help='Path to latex compiler')

    psr_report.set_defaults(func=radvel.driver.report)

    args = psr.parse_args()

    if args.outputdir is None:
        setupfile = args.setupfn
        print(setupfile)
        system_name = os.path.basename(setupfile).split('.')[0]
        outdir = os.path.join('./', system_name)
        args.outputdir = outdir

    if not os.path.isdir(args.outputdir):
        os.mkdir(args.outputdir)

    args.func(args)


if __name__ == '__main__':
    main()
