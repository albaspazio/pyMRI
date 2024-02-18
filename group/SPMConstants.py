class SPMConstants:
    """
    This class contains constants used throughout the SPM software.

    Attributes:
        MULTREGR (int): A constant for multiple regression analysis.
        OSTT (int): A constant for one-sample t-test analysis.
        TSTT (int): A constant for two-sample t-test analysis.
        OWA (int): A constant for one-way analysis of variance.
        TWA (int): A constant for two-way analysis of variance.
        VBM_DARTEL (int): A constant for VBM-DARTEL analysis.
        CAT (int): A constant for Cortical Thickness analysis.
        FMRI (int): A constant for functional MRI analysis.
        stats_types (list): A list of statistical analysis types.
        analysis_types (list): A list of analysis types.
    """

    MULTREGR = 1
    OSTT = 2
    TSTT = 3
    OWA = 4
    TWA = 5

    VBM_DARTEL = 11
    CAT = 12
    FMRI = 13

    stats_types = [MULTREGR, OSTT, TSTT, OWA, TWA]
    analysis_types = [VBM_DARTEL, CAT, FMRI]
