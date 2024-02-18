class FSLConFile:
    """
    This class represents an FSL confounds file.

    Attributes:
        ncontrasts (int): The number of contrasts in the file.
        nwaves (int): The number of waves in the file.
        matrix (list): A list of contrast matrices.
        names (list): A list of contrast names.
        pp_heights (list): A list of p-values for the height threshold.
        req_effect (list): A list of required effects for each contrast.
    """

    def __init__(self):
        """
        Initialize an FSLConFile object.
        """
        self.ncontrasts = 0
        self.nwaves = 0
        self.matrix = []
        self.names = []
        self.pp_heights = []
        self.req_effect = []

    def get_subset_text(self, ids) -> str:
        """
        Get the text of a subset of the confounds file.

        Args:
            ids (list): A list of contrast IDs to include in the subset.

        Returns:
            str: The text of the subset confounds file.
        """
        txt = ""
        for i, con_id in enumerate(ids):
            txt = txt + f"/ContrastName{i + 1}\t{self.names[con_id]}\n"
        txt = txt + f"/NumWaves\t{self.nwaves}\n"
        txt = txt + f"/NumContrasts\t{len(ids)}\n"
        txt = txt + self.pp_heights + "\n"
        txt = txt + self.req_effect + "\n"
        txt = txt + "\n"
        txt = txt + "/Matrix\n"
        for id, con_id in enumerate(ids):
            txt = txt + self.matrix[con_id] + "\n"

        return txt



