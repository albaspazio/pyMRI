from __future__ import annotations
from typing import List

from myutility.images.Image import Image


class Tract(Image):


    def __new__(cls,  _path:str, _fa:float|None=None, _md:float|None=None, _ad:float|None=None, _rd:float|None=None):
        return super(Tract, cls).__new__(cls, _path)

    def __init__(self, _path:str, _fa:float|None=None, _md:float|None=None, _ad:float|None=None, _rd:float|None=None):

        super().__init__(_path, must_exist=True)

        # self.measures:List[str] = []
        self.fa = _fa
        self.md = _md
        self.ad = _ad
        self.rd = _rd

    def set_metric(self, name:str, value:float):
        if name == "FA":
            self.fa = value
        elif name == "MD":
            self.md = value
        elif name == "L1":
            self.ad = value
        elif name == "L23":
            self.rd = value

    def set_metrics(self, metrics:dict):
        for name in metrics.keys():
            if name == "FA":
                self.fa = metrics[name]
            elif name == "MD":
                self.md = metrics[name]
            elif name == "L1":
                self.ad = metrics[name]
            elif name == "L23":
                self.rd = metrics[name]

    def get_metric(self, name:str) -> float:
        if name == "FA":
            return self.fa
        elif name == "MD":
            return self.md
        elif name == "L1":
            return self.ad
        elif name == "L23":
            return self.rd
        elif name == "nvox":
            return self.nvoxels

    def get_metrics(self) -> List[float]:
        return [self.fa, self.md, self.ad, self.rd]

    def get_named_metrics(self) -> dict:
        return {"FA":self.fa, "MD":self.md, "L1":self.ad, "L23":self.rd}

    # def export(self, values:List[str]|None=None) -> str:
    #     if values is None:
    #         values =
