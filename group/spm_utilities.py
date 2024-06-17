import os
from typing import List

from data.utilities import list2spm_text_column
from group.SPMConstants import SPMConstants
from utility.images.images import mid_1based

import numpy as np


class ResultsParams:
    """
    Parameters for statistical results.

    Parameters
    ----------
    multcorr : str, optional
        Type of multiple comparison correction.
        Options: "FWE", "Bonferroni", "None".
        Default: "FWE"
    pvalue : float, optional
        Threshold p-value for statistical significance.
        Default: 0.05
    clustext : str, optional
        Type of text for cluster-level results.
        Options: "none", "en_corr", "en_nocorr".
        Default: None

    Returns
    -------
    None

    """

    def __init__(self, multcorr: str = "FWE", pvalue: float = 0.05, clustext: int = 0):
        self.mult_corr = multcorr
        self.pvalue = pvalue
        self.cluster_extend = clustext


class CatConvResultsParams(ResultsParams):
    """
    Parameters for categorical conversion results.

    Parameters
    ----------
    multcorr : str, optional
        Type of multiple comparison correction.
        Options: "FWE", "Bonferroni", "None".
        Default: "FWE"
    pvalue : float, optional
        Threshold p-value for statistical significance.
        Default: 0.05
    clustext : str, optional
        Type of text for cluster-level results.
        Options: "none", "en_corr", "en_nocorr".
        Default: None

    Returns
    -------
    None

    """
    def __init__(self, multcorr:str="FWE", pvalue=0.05, clustext:str="none"):
        if clustext is None:
            clustext = "none"
        else:
            if clustext not in ["none", "en_corr", "en_nocorr"]:
                raise Exception("Error in CatConvResultsParams: clustext param (" + clustext + ") is not one of: none, en_corr, en_nocorr")
        super().__init__(multcorr, pvalue, clustext)


class SubjResultsParam(ResultsParams):
    """
    Parameters for statistical results of a single subject.

    Parameters
    ----------
    multcorr : str, optional
        Type of multiple comparison correction.
        Options: "FWE", "Bonferroni", "None".
        Default: "FWE"
    pvalue : float, optional
        Threshold p-value for statistical significance.
        Default: 0.05
    clustext : str, optional
        Type of text for cluster-level results.
        Options: "none", "en_corr", "en_nocorr".
        Default: None
    sessrep : str, optional
        Type of session representation.
        Options: "none", "en_corr", "en_nocorr".
        Default: "none"

    Returns
    -------
    None

    """
    def __init__(self, multcorr:str, pvalue:float, clustext:int=0, sessrep:str="none"):
        super().__init__(multcorr, pvalue, clustext)
        self.sessrep    = sessrep


class Contrast:
    """
    A class to represent a contrast in a neuroimaging analysis.

    Parameters
    ----------
    name : str
        The name of the contrast.
    weights : list of float
        The weights of the conditions or regressors in the contrast.
    type : bool
        Whether the contrast is a t-contrast or an f-contrast.
    sessrep : str, optional
        The session representation of the contrast. Options: "none", "en_corr", "en_nocorr".
    """
    def __init__(self, name:str, weights:str, _type:bool, sessrep:str="none"):
        self.name       = name
        self.weights    = weights
        self.type       = _type
        self.sessrep    = sessrep


class TContrast(Contrast):
    """
    A class to represent a t-contrast in a neuroimaging analysis.

    Parameters
    ----------
    name : str
        The name of the contrast.
    weights : list of float
        The weights of the conditions or regressors in the contrast.
    sessrep : str, optional
        The session representation of the contrast. Options: "none", "en_corr", "en_nocorr".
    """
    def __init__(self, name:str, weights:str, sessrep:str="none"):
        super().__init__(name, weights, True, sessrep)


class FContrast(Contrast):
    """
    A class to represent an f-contrast in a neuroimaging analysis.

    Parameters
    ----------
    name : str
        The name of the contrast.
    weights : str
        The weights of the conditions or regressors in the contrast.
    sessrep : str, optional
        The session representation of the contrast. Options: "none", "en_corr", "en_nocorr".

    """
    def __init__(self, name:str, weights:str, sessrep:str="none"):
        super().__init__(name, weights, False, sessrep)


class SubjCondition:
    """
    A class to represent a single subject's condition.

    Parameters
    ----------
    name : str
        The name of the condition.
    onsets : list of float
        The onset times of the condition.
    duration : float or list of float, optional
        The duration of the condition.
        If a list, it should be the same length as onsets.
        If 0, it will be set to the duration between adjacent onsets.
        Default: 0
    orth : str, optional
        The orthogonalization value of the condition.
        Options: "1", "-1".
        Default: "1"
    """
    def __init__(self, name:str, onsets: np.ndarray, duration:str= "0", orth:str= "1"):
        self.name        = name
        self._onsets     = onsets
        self._duration   = duration
        self._orth       = str(orth)

    @property
    def duration(self) -> str:
        """
        The duration of the condition.
        Returns
        -------
        duration : float or [list of float]
            The duration of the condition.
        """
        if isinstance(self._duration, np.ndarray):
            text = "[" + list2spm_text_column(self._duration) + "]"
        else:
            text = str(self._duration)
        return text.replace("\n", " ")

    @property
    def onsets(self) -> str:
        """
        The onset times of the condition.

        Returns
        -------
        onsets : list of float, coded as string, without trailing square brackets[]
            The onset times of the condition.
        """
        datas = []
        if self._onsets.shape[0] == 1:
            # data are in the other dimension
            for n in self._onsets[0]:
                datas.append(n)
        return "[" + list2spm_text_column(datas) + "]"

    @property
    def orth(self):
        """
        The orthogonalization value of the condition.

        Returns
        -------
        orth : str
            The orthogonalization value of the condition.
        """
        return str(self._orth)


class Peak:
    """
    A class to represent a peak in a statistical map.

    Parameters
    ----------
    pfwe : float
        The p-value from the family-wise error (FWE) correction.
    pfdr : float
        The p-value from the false discovery rate (FDR) correction.
    t : float
        The t-value of the peak.
    zscore : float
        The z-score of the peak.
    punc : float
        The p-uncorrected value of the peak.
    x : float
        The x coordinate of the peak.
    y : float
        The y coordinate of the peak.
    z : float
        The z coordinate of the peak.
    """

    def __init__(self, pfwe:float, pfdr:float, t:float, zscore:float, punc:float, x:float, y:float, z:float):
        self.pfwe = pfwe
        self.pfdr = pfdr
        self.t = t
        self.zscore = zscore
        self.punc = punc
        self.x = x
        self.y = y
        self.z = z


class Cluster:
    """
    A class to represent a cluster in a statistical map.

    Parameters
    ----------
    _id : int
        The ID of the cluster.
    pfwe : float
        The p-value from the family-wise error (FWE) correction.
    pfdr : float
        The p-value from the false discovery rate (FDR) correction.
    k : int
        The size of the cluster.
    punc : float
        The p-uncorrected value of the cluster.
    firstpeak : Peak
        The first peak in the cluster.
    """

    def __init__(self, _id:int, pfwe:float, pfdr:float, k:int, punc:float, firstpeak:Peak):
        """
        Initialize a Cluster object.
        """
        self.id = _id
        self.pfwe = pfwe
        self.pfdr = pfdr
        self.k = k
        self.punc = punc
        self.peaks = []
        self.peaks.append(firstpeak)

    def add_peak(self, peak):
        """
        Add a peak to the cluster.
        """
        self.peaks.append(peak)


class Regressor:
    """
    A class to represent a regressor in a neuroimaging analysis.

    Parameters
    ----------
    name : str
        The name of the regressor.
    isNuisance : bool
        Whether the regressor is a nuisance or not.
    """
    def __init__(self, name, isNuisance):
        self.name       = name
        self.isNuisance = isNuisance


class Covariate(Regressor):
    """
    A class to represent a covariate in a neuroimaging analysis.

    Parameters
    ----------
    name : str
        The name of the covariate.
    """
    def __init__(self, name):
        super().__init__(name, False)


class Nuisance(Regressor):
    """
    A class to represent a nuisance regressor in a neuroimaging analysis.

    Parameters
    ----------
    name : str
        The name of the nuisance regressor.
    isNuisance : bool
        Whether the regressor is a nuisance or not.

    """
    def __init__(self, name):
        super().__init__(name, True)


class FmriProcParams:
    """
    Parameters for fMRI processing.

    Parameters
    ----------
    tr : float
        Repetition time of the scanner.
    nsl : int
        Number of slices in the volume.
    sl_tim : list of float
        Slice timing values.
    st_ref : str
        Reference slice for slice timing.
        Options: "first", "last".
    time_bins : list of float
        Time points for regressors.
    time_onset : list of float, optional
        Time points for onsets.
        If None, it will be set to the middle of time_bins.
    acq_sch : int, optional
        Acquisition scheme.
        Options: 0 (single-shot), 1 (multi-shot).
        Default: 0
    hpf : int, optional
        High-pass filter cutoff.
        Default: 128
    hrf_deriv : bool, optional
        Whether to use HRF derivatives.
        Default: True
    ta : int, optional
        Temporal autocorrelation cutoff.
        Default: 0
    smooth : int, optional
        Kernel size for smoothing.
        Default: 6
    events_unit : str, optional
        Unit of onsets.
        Options: "secs", "samples".
        Default: "secs"

    Returns
    -------
    None
    """

    def __init__(self, tr, nsl, sl_tim, st_ref, time_bins, time_onset=None, acq_sch=0, hpf=128, hrf_deriv=True, ta=0, smooth=6, events_unit:str="secs"):
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
        self.hpf            = hpf
        self.hrf_deriv      = hrf_deriv
        self.ta             = ta
        self.smooth         = smooth
        self.events_unit    = events_unit


class GrpInImages:
    """
    A class to represent group-level input images for a neuroimaging analysis.

    Parameters
    ----------
    type : int
        The type of images. using SPMConstants
        Options: CT, VBM_DARTEL, GYR, SDEP, VBM, FMRI".
    folder : str, optional
        The folder containing the images.
        Only used for "dartel" and "vbm" types.
    name : str, optional
        The name of the images.
        Only used for "ct" type.
    """

    valid_type = [SPMConstants.VBM, SPMConstants.VBM_DARTEL, SPMConstants.CT, SPMConstants.FMRI, SPMConstants.GYR, SPMConstants.SDEP]

    def __init__(self, type:int, folder=None, name=None):
        """
        Initialize a GroupLevelInputImages object.
        """
        self.type = type
        self.folder = folder
        self.name = name

        # folder is:
        # fmri          :   name of subject's fmri subfolder of (SUBJ_LABEL/sX/fmri/stats/)
        # ct/gyr/sdep   :   [None] always located in mpr/cat/surf
        # vbm_dartel    :   fullpath of a group-analysis folder
        # vbm           :   fullpath of a group-analysis folder

        if (self.type == SPMConstants.VBM or self.type == SPMConstants.VBM_DARTEL or
           (self.type == SPMConstants.CT and self.folder is not None) or (self.type == SPMConstants.GYR and self.folder is not None) or (self.type == SPMConstants.SDEP and self.folder is not None)):
            if not os.path.isdir(self.folder):
                raise Exception("Error in GroupLevelInputImages: not-existing images folder (" + self.folder + "), analysis type (" + str(type) + ")")

        if self.type not in self.valid_type:
            raise Exception("Error in GroupLevelInputImages: invalid images type (" + str(type) + ")")
