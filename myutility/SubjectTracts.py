from typing import List

from myutility.images.Images import Images


class SubjectTracts(Images):

    def __new__(cls, name:str, value=None, must_exist:bool=False, msg:str=""):
        return super(SubjectTracts, cls).__new__(cls, value)

    def __init__(self, _name, value=None, must_exist=False, msg:str=""):
        super().__init__()
        self.name = _name


    @property
    def tract_names(self):
        return [tract.name for tract in self]

    def export_header(self, metrics:List[str]|None=None) -> str:

        if metrics is None:
            metrics = ["nvox","FA","MD","L1","L23"]

        hdr_out = "subj"

        for tract in self:
            for measure in metrics:
                hdr_out += f"\t{self[0].name}_{measure}"

        return hdr_out

    def export_data(self, metrics:List[str]|None=None) -> str:

        if metrics is None:
            metrics = ["nvox","FA","MD","L1","L23"]

        val_out = f"{self.name}"

        for tract in self:
            for measure in metrics:
                val_out += f"\t{tract.get_metric(measure)}"

        return val_out

