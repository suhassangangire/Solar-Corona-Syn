import numpy as np
import pandas as pd

import subprocess
import os
import tempfile
import shutil
from operator import itemgetter
from jinja2 import Environment, PackageLoader, select_autoescape

import Sun-Corona-Syn

env = Environment(loader=PackageLoader('Sun-Corona-Syn', 'templates'))
print_basis = 'per tc tp e w k'
units = {
    'per': 'days',
    'tp': 'JD',
    'tc': 'JD',
    'e': '',
    'w': 'radians',
    'k': 'm s$^{-1}$',
    'logk': r'$\ln{(\rm m\ s^{-1})}$',
    'secosw': '',
    'sesinw': '',
    'gamma': 'm s$-1$',
    'jitter': 'm s$-1$',
    'logjit': r'$\ln{(\rm m\ s^{-1})}$',
    'jit': r'$\rm m\ s^{-1}$',
    'dvdt': 'm s$^{-1}$ d$^{-1}$',
    'curv': 'm s$^{-1}$ d$^{-2}$',
    'gp_amp': 'm s$-1$',
    'gp_explength': 'days',
    'gp_per': 'days',
    'gp_perlength': '',
    # 'mpsini': '$M_\earth$',
    # 'rp': '$R_\earth$',
    # 'rhop': 'g cm$^{-3}$',
}


class Sun-Corona-SynReport(object):
    """Sun-Corona-Syn report

    Class to handle the creation of the Sun-Corona-Syn summary PDF

    Args:
        planet (planet object): planet configuration object loaded in
            `kepfit.py` using `imp.load_source`
        post (Sun-Corona-Syn.posterior):
            Sun-Corona-Syn.posterior object containing the best-fit parameters in
                post.params
        compstats (dict): dictionary of model comparison results from `Sun-Corona-Syn ic`
        derived (bool): included table of derived parameters
        chains (DataFrame): output DataFrame from a `Sun-Corona-Syn.mcmc` run
        criterion (DataFrame): output DataFrame from a 'Sun-Corona-Syn.mcmc' run
    """

    def __init__(self, planet, post, chains, minafactor, maxarchange, maxgr, mintz, compstats=None,
                 derived=False):
        self.planet = planet
        self.post = post
        self.starname = planet.starname
        self.starname_tex = planet.starname.replace('_', '\\_')
        self.runname = self.starname_tex
        self.derived = derived

        post.params = post.params.basis.to_synth(post.params)
        post.params = post.params.basis.from_synth(
            post.params, print_basis
        )
        self.latex_dict = post.params.tex_labels()

        for p in post.params.keys():
            if p not in chains.columns:
                chains[p] = post.params[p].value

        self.chains = post.params.basis.to_synth(
            chains, basis_name=planet.fitting_basis
        )
        self.chains = post.params.basis.from_synth(
            self.chains, print_basis
        )
        self.minafactor = minafactor
        self.maxarchange = maxarchange
        self.maxgr = maxgr
        self.mintz = mintz
        self.quantiles = self.chains.quantile([0.159, 0.5, 0.841])
        self.compstats = compstats
        self.num_planets = self.post.params.num_planets

    def texdoc(self):
        """TeX for entire document

        Returns:
            str: TeX code for report
        """
        reportkw = {}
        reportkw['version'] = Sun-Corona-Syn.__version__

        # Render TeX for figures
        figtypes = ['rv_multipanel', 'corner', 'corner_derived_pars']
        for figtype in figtypes:
            infile = "{}_{}.pdf".format(self.runname, figtype)
            tmpfile = 'fig_{}.tex'.format(figtype)
            key = 'fig_{}'.format(figtype)
            if os.path.exists(infile):
                t = env.get_template(tmpfile)
                reportkw[key] = t.render(report=self, infile=infile)

        # Render TeX for tables
        textable = TexTable(self)
        reportkw['tab_crit'] = textable.tab_crit()
        reportkw['tab_rv'] = textable.tab_rv()
        reportkw['tab_params'] = textable.tab_params()
        reportkw['tab_derived'] = textable.tab_derived()
        reportkw['tab_prior_summary'] = textable.tab_prior_summary()

        if self.compstats is not None:
            reportkw['tab_comparison'] = textable.tab_comparison()

        t = env.get_template('report.tex')
        out = t.render(report=self, **reportkw)
        return out

    def compile(self, pdfname, latex_compiler='pdflatex', depfiles=[]):
        """Compile Sun-Corona-Syn report

        Compile the Sun-Corona-Syn report from a string containing TeX code
        and save the resulting PDF to a file.

        Args:
            pdfname (str): name of the output PDF file
            latex_compiler (str): path to latex compiler
            depfiles (list): list of file names of dependencies needed for
                LaTex compilation (e.g. figure files)

        """
        texname = os.path.basename(pdfname).split('.')[0] + '.tex'
        current = os.getcwd()
        temp = tempfile.mkdtemp()
        for fname in depfiles:
            shutil.copy2(
                os.path.join(current, fname), os.path.join(temp, fname)
            )

        os.chdir(temp)

        f = open(texname, 'w')
        f.write(self.texdoc())
        f.close()

        shutil.copy(texname, current)

        try:
            for i in range(3):
                # LaTex likes to be compiled a few times
                # to get the table widths correct
                proc = subprocess.Popen(
                    [latex_compiler, texname], stdout=subprocess.PIPE,
                )
                proc.communicate()  # Let the subprocess complete
        except (OSError):
            msg = """
WARNING: REPORT: could not run %s. Ensure that %s is in your PATH
or pass in the path as an argument
""" % (latex_compiler, latex_compiler)
            print(msg)
            return

        shutil.copy(pdfname, current)

        shutil.rmtree(temp)
        os.chdir(current)


class TexTable(Sun-Corona-SynReport):
    """LaTeX table

    Class to handle generation of the LaTeX tables within the summary PDF.

    Args:
        report (Sun-Corona-Syn.report.Sun-Corona-SynReport): Sun-Corona-Syn report object
        full (bool): get full-length RV table [default: True]
    """

    def __init__(self, report):
        self.report = report
        self.post = report.post
        self.quantiles = report.quantiles
        self.fitting_basis = report.post.params.basis.name
        self.minafactor = report.minafactor
        self.maxarchange = report.maxarchange
        self.maxgr = report.maxgr
        self.mintz = report.mintz

    def _row(self, param, unit):
        """
        Helper function to output the rows in the parameter table
        """
        if param not in self.quantiles.keys():
            param = param[:-1]

        if unit == 'radians':
            par = Sun-Corona-Syn.utils.geterr(self.report.chains[param], angular=True)
            med, low, high = par
        else:
            med = self.quantiles[param][0.5]
            low = self.quantiles[param][0.5] - self.quantiles[param][0.159]
            high = self.quantiles[param][0.841] - self.quantiles[param][0.5]

        maxlike = self.post.maxparams[param]
        tex = self.report.latex_dict[param]

        low = Sun-Corona-Syn.utils.round_sig(low)
        high = Sun-Corona-Syn.utils.round_sig(high)
        maxlike, errlow, errhigh = Sun-Corona-Syn.utils.sigfig(maxlike, low, high)
        med, errlow, errhigh = Sun-Corona-Syn.utils.sigfig(med, low, high)

        if min(errlow,errhigh) <= 1e-12:
            med = maxlike = r"\equiv%s" % round(self.quantiles[param][0.5], 4)
            errfmt = ''
        else:
            if errhigh == errlow:
                errfmt = r'\pm %s' % errhigh
            else:
                errfmt = '^{+%s}_{-%s}' % (errhigh, errlow)

        row = "%s & $%s%s$ & $%s$ & %s" % (tex, med, errfmt, maxlike, unit)
        return row

    def _data(self, basis, dontloop=False):
        """
        Helper function to output the rows in the parameter table

        Args:
            basis (str): name of Basis object (see basis.py) to be printed
            dontloop (Bool): if True, don't loop over number of planets (useful for
                printing out gamma, dvdt, jitter, curv)
        """
        suffixes = ['_'+j for j in self.report.post.likelihood.suffixes]
        rows = []

        nloop = self.report.planet.nplanets+1
        if dontloop:
            nloop=2

        for n in range(1, nloop):
            for p in basis.split():  # loop over variables
                par = p+str(n)

                # get unit for parameter
                unit = units.get(p, '')

                # try to remove suffix
                if unit == '' and par not in units.keys():
                    for s in suffixes:
                        if s in p:
                            unit = units.get(p.replace(s, ''), '')
                            break

                # if still can't find units get it by the parameter itself
                # (derived parameters)
                if unit == '':
                    unit = units.get(par, '')

                try:
                    row = self._row(par, unit)
                except KeyError:
                    continue

                rows.append(row)

        return rows

    def tab_prior_summary(self, name_in_title=False):
        """Summary of priors

        Args:
            name_in_title (Bool [optional]): if True, include
                the name of the star in the table title
        """
        texdict = self.post.likelihood.params.tex_labels()
        prior_list = self.post.priors
        rows = []
        for prior in prior_list:
            row = prior.__str__()
            if not row.endswith("\\\\"):
                row = row + "\\\\"
            rows.append(row)

        kw = {}
        if name_in_title:
            kw['title'] = "{} Summary of Priors".format(self.report.starname)
        else:
            kw['title'] = "Summary of Priors"
        tmpfile = 'tab_prior_summary.tex'
        t = env.get_template(tmpfile)
        out = t.render(rows=rows, **kw)
        return out

    def tab_rv(self, name_in_title=False, max_lines=50):
        """Table of input velocities

        Args:
            name_in_title (Bool [optional]): if True, include
                the name of the star in the table title
        """

        kw = {}
        nvels = len(self.post.likelihood.x)

        if max_lines is None:
            iters = range(nvels)
            kw['notes'] = ''
        else:
            max_lines = int(np.round(max_lines))
            iters = range(nvels)[:max_lines]
            kw['notes'] = r"""Only the first %d of %d RVs are displayed in this table. \
Use \texttt{Sun-Corona-Syn table -t rv} to save the full \LaTeX\ table as a separate file.""" % (max_lines, nvels)

        rows = []
        for i in iters:
            t = self.post.likelihood.x[i]
            v = self.post.likelihood.y[i]
            e = self.post.likelihood.yerr[i]
            inst = self.post.likelihood.telvec[i]
            if '_' in inst:
                inst = inst.replace('_', r'$_{\rm ')
                inst += '}$'
            row = "{:.5f} & {:.2f} & {:.2f} & {:s}".format(t, v, e, inst)
            rows.append(row)

        if name_in_title:
            kw['title'] = "{} Radial Velocities".format(self.report.starname)
        else:
            kw['title'] = "Radial Velocities"
        tmpfile = 'tab_rv.tex'
        t = env.get_template(tmpfile)
        out = t.render(rows=rows, **kw)
        return out

    def tab_params(self, name_in_title=False):
        """ Table of final parameter values
        Args:
            name_in_title (Bool [optional]): if True, include
                the name of the star in the table title
        """
        # Sort extra params
        ep = []
        order = ['gamma', 'dvdt', 'curv', 'jit']
        for o in order:
            op = []
            for p in self.post.likelihood.extra_params:
                if o in p:
                    op.append(p)
            if len(op)==0:
                op = [o]
            [ep.append(i) for i in sorted(op)[::-1]]

        # Add GP parameters
        for par in self.report.post.likelihood.list_params():
            if par.startswith('gp_'):
                ep.append(par)

        ep = ' '.join(ep)

        kw = {}
        kw['fitting_basis_rows'] = self._data(self.fitting_basis)
        kw['print_basis_rows'] = self._data(print_basis)
        kw['ep_rows'] = self._data(ep, dontloop=True)
        kw['nlinks'] = len(self.report.chains)
        kw['time_base'] = self.report.post.likelihood.model.time_base
        if name_in_title:
            kw['title'] = "{} MCMC Posteriors".format(self.report.starname)
        else:
            kw['title'] = "MCMC Posteriors"
        tmpfile = 'tab_params.tex'
        t = env.get_template(tmpfile)
        out = t.render(**kw)
        return out

    def tab_crit(self, name_in_title=False):
        """Table of final convergence criterion values
        Args:
            name_in_title (Bool [optional]): if True, include
                the name of the star in the table title
        """

        names = ['minAfactor', 'maxArchange', 'maxGR', 'minTz']
        values = [self.minafactor, self.maxarchange, self.maxgr, self.mintz]
        rows = []
        for i in range(0,len(names)):
            rows.append(r"%s & $%7.3f$" % (names[i], float(values[i])))

        kw = dict()
        kw['rows'] = rows
        if name_in_title:
            kw['title'] = "{} Final Convergence Criterion".format(self.report.starname)
        else:
            kw['title'] = "Final Convergence Criterion"

        tmpfile = 'tab_crit.tex'
        t = env.get_template(tmpfile)
        out = t.render(**kw)

        return out

    def tab_derived(self, name_in_title=False):
        """ Table of derived parameter values
        Args:
            name_in_title (Bool [optional]): if True, include
                the name of the star in the table title
        """

        if not self.report.derived:
            return ""

        dpl = Sun-Corona-Syn.plot.mcmc_plots.DerivedPlot(self.report.chains, self.report.planet)
        derived_params = dpl.labels
        derived_basis = ' '.join(set([s[:-1] for s in derived_params]))
        derived_tex = dpl.texlabels
        derived_units = dpl.units

        self.report.latex_dict.update(dict(zip(derived_params, derived_tex)))
        units.update(dict(zip(derived_params, derived_units)))

        self.quantiles = dpl.chains.quantile([0.159, 0.5, 0.841])

        for par in derived_params:
            # self.report.post.maxparams[par] = self.report.chains[par].iloc[
            #     self.report.chains['lnprobability'].argmax]
            self.post.maxparams[par] = dpl.chains.loc[dpl.chains['lnprobability'].idxmax(), par]

        kw = dict()
        kw['derived_rows'] = self._data(derived_basis)
        if name_in_title:
            kw['title'] = "{} Derived Posteriors".format(self.report.starname)
        else:
            kw['title'] = "Derived Posteriors"
        tmpfile = 'tab_derived.tex'
        t = env.get_template(tmpfile)
        out = t.render(**kw)

        return out

    def tab_comparison(self):
        """Model comparisons
        """
        statsdict = self.report.compstats

        if statsdict is None or len(statsdict) < 1:
            return ""

        statsdict_sorted = sorted(statsdict, key=itemgetter('AICc'), reverse=False)

        n_test = len(statsdict_sorted)
        if n_test > 50:
            print("Warning, the number of model comparisons is very"
                  + " large. Printing 50 best models.\nConsider using"
                  + " the --unmixed flag when performing ic comparisons")
            n_test = 50
            # statsdict_sorted = statsdict_sorted[:50]

        statskeys = statsdict_sorted[0].keys()
        coldefs = r"\begin{deluxetable*}{%s}" % ('l'+'l'+'r'*(len(statskeys)-1) + 'r')
        head = r"\tablehead{"
        head += r"\colhead{AICc Qualitative Comparison}"
        head += r" & \colhead{Free Parameters}"
        for s in statskeys:
            if s == 'Free Params':
                pass
            else:
                head += r" & \colhead{%s}" % s
        head += r" & \colhead{$\Delta$AICc}"
        head += r"}"

        minAIC = statsdict_sorted[0]['AICc'][0]
        # See Burnham + Anderson 2004
        deltaAIClevels = [0., 2., 4., 10.]
        deltaAICmessages = ["Nearly Indistinguishable", "Somewhat Disfavored", \
            "Strongly Disfavored", "Ruled Out"]
        deltaAICtrigger = 0
        maxtrigger = len(deltaAIClevels)

        rows = []
        for i in range(n_test):
            row = ""
            for s in statsdict_sorted[i].keys():
                val = statsdict_sorted[i][s][0]
                if type(val) is int:
                    row += " & %s" % str(val)
                elif type(val) is float:
                    row += " & %.2f" % val
                elif type(val) is str:
                    row += " & %s" % val
                elif type(val) is list:
                    row += " &"
                    for item in val:
                        row += " %s," %item
                    row += r" {$\gamma$}"
                    #row = row[:-1]
                else:
                    raise(ValueError, "Failed to format values for LaTeX: {}  {}".format(s, val))
            row += " & %.2f" % (statsdict_sorted[i]['AICc'][0] - minAIC)
            # row = row[3:]
            if i == 0:
                # row = "{\\bf" + row + "}"
                row = "AICc Favored Model"+ row
            appendhline = False
            if (deltaAICtrigger < maxtrigger) and ((statsdict_sorted[i]['AICc'][0] - minAIC) > deltaAIClevels[deltaAICtrigger]):
                deltaAICtrigger += 1
                while (deltaAICtrigger < maxtrigger) and ((statsdict_sorted[i]['AICc'][0] - minAIC) > deltaAIClevels[deltaAICtrigger]):
                    deltaAICtrigger += 1
                row = deltaAICmessages[deltaAICtrigger-1] + row
                appendhline = True
            if appendhline or (i == 1):
                rows.append(r"\hline")
            rows.append(row)

        t = env.get_template('tab_comparison.tex')
        out = t.render(coldefs=coldefs, head=head, rows=rows)
        return out
