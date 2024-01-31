class FSLConFile:


    def __init__(self):

        self.ncontrasts = 0
        self.nwaves = 0

        self.matrix = []
        self.names = []
        self.pp_heights = []
        self.req_effect = []


    # define the text of a con file containing only the given ids
    def get_subset_text(self, ids) -> str:
        txt = ""
        for i, con_id in enumerate(ids):
            txt = txt + "/ContrastName" + str(i + 1) + "\t" + self.names[con_id] + "\n"
        txt = txt + "/NumWaves\t" + str(self.nwaves) + "\n"
        txt = txt + "/NumContrasts\t" + str(len(ids)) + "\n"
        txt = txt + self.pp_heights + "\n"
        txt = txt + self.req_effect + "\n"
        txt = txt + "\n"
        txt = txt + "/Matrix\n"
        for id, con_id in enumerate(ids):
            txt = txt + self.matrix[con_id] + "\n"

        return txt



