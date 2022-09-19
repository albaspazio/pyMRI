import os
from data.utilities import list2spm_text_column
from utility.images.images import mid_1based


class ResultsParams:
    def __init__(self, multcorr="FWE", pvalue=0.05, clustext=0):
        self.mult_corr      = multcorr
        self.pvalue         = pvalue
        self.cluster_extend = clustext


class CatConvResultsParams:
    def __init__(self, multcorr="FWE", pvalue=0.05, clustext="none"):
        self.mult_corr      = multcorr
        self.pvalue         = pvalue    # "FWE" | "FDR" | "none"
        self.cluster_extend = clustext  # "none" | "en_corr" | "en_nocorr"


class SubjResults:
    def __init__(self, multcorr="FWE", pvalue=0.05, sessrep="none"):
        self.multcorr       = multcorr
        self.pvalue         = pvalue
        self.sessrep        = sessrep


class Contrast:
    def __init__(self, name, weights, _type, sessrep="none"):
        self.name       = name
        self.weights    = weights
        self.type       = _type
        self.sessrep    = sessrep

class TContrast(Contrast):
    def __init__(self, name, weights, sessrep="none"):
        super().__init__(name, weights, True, sessrep)


class FContrast(Contrast):
    def __init__(self, name, weights, sessrep="none"):
        super().__init__(name, weights, False, sessrep)


class SubjCondition:
    def __init__(self, name, onsets, duration="0", orth="1"):
        self.name        = name
        self._onsets     = onsets
        self._duration   = str(duration)
        self._orth       = str(orth)

    @property
    def duration(self):
        return str(self._duration)

    @property
    def onsets(self):
        return list2spm_text_column(self._onsets)

    @property
    def orth(self):
        return str(self._orth)


class Peak:

    def __init__(self, pfwe, pfdr, t, zscore, punc, x, y, z):
        self.pfwe   = pfwe
        self.pfdr   = pfdr
        self.t      = t
        self.zscore = zscore
        self.punc   = punc
        self.x      = x
        self.y      = y
        self.z      = z


class Cluster:

    def __init__(self, _id, pfwe, pfdr, k, punc, firstpeak):
        self.id     = _id
        self.pfwe   = pfwe
        self.pfdr   = pfdr
        self.k      = k
        self.punc   = punc
        self.peaks  = []
        self.peaks.append(firstpeak)

    def add_peak(self, peak):
        self.peaks.append(peak)


class Regressor:
    def __init__(self, name, isNuisance):
        self.name       = name
        self.isNuisance = isNuisance


class Covariate(Regressor):
    def __init__(self, name):
        super().__init__(name, False)


class Nuisance(Regressor):
    def __init__(self, name):
        super().__init__(name, True)


class FmriProcParams:
    def __init__(self, tr, nsl, sl_tim, st_ref, time_bins, time_onset=None, acq_sch=0, ta=0, smooth=6, events_unit="secs"):
        self.tr             = tr
        self.nslices        = nsl
        self.slice_timing   = sl_tim
        self.st_ref         = st_ref
        self.time_bins      = time_bins
        if time_onset is None:
            self.time_onset = mid_1based(time_bins)
        else:
            self.time_onset = time_onset
        self.acq_scheme     = acq_sch
        self.ta             = ta
        self.smooth         = smooth
        self.events_unit    = events_unit


class GrpInImages:

    valid_type = ["ct", "dartel", "vbm", "fmri"]

    def __init__(self, _type, _folder=None, _name=None):
        self.type       = _type
        self.folder     = _folder
        # folder is:
        # fmri:     name of subject's fmri subfolder
        # ct:       [None] always located in mpr/cat/surf
        # dartel:   fullpath of a group-analysis folder
        # vbm:      fullpath of a group-analysis folder

        self.name       = _name

        if self.type == "vbm" or self.type == "dartel" or (self.type == "ct" and self.folder is not None):
            if not os.path.isdir(self.folder):
                raise Exception("Error in GroupLevelInputImages: not-existing images folder (" + self.folder + "), analysis type (" + str(type) + ")")

        if self.type not in self.valid_type:
            raise Exception("Error in GroupLevelInputImages: invalid images type (" + str(type) + ")")
