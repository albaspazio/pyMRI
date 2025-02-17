from __future__ import annotations
from typing import List

from myutility.images.Image import Image


class TractInfo:

    def __init__(self, _path:str, _fa:float|None=None, _md:float|None=None, _ad:float|None=None, _rd:float|None=None):

        self.path       = Image(_path)
        self.name       = self.path.name
        self.nvoxels    = self.path.get_nvoxels()

        self.fa = _fa
        self.md = _md
        self.ad = _ad
        self.rd = _rd

    def set_metric(self, name:str, value:float):
        if name == "FA":
            self.fa = value
        elif name == "MD":
            self.md = value
        elif name == "AD":
            self.ad = value
        elif name == "RD":
            self.rd = value

    def set_metrics(self, metrics:dict):
        for name in metrics.keys():
            if name == "FA":
                self.fa = metrics[name]
            elif name == "MD":
                self.md = metrics[name]
            elif name == "AD":
                self.ad = metrics[name]
            elif name == "RD":
                self.rd = metrics[name]

    def get_metric(self, name:str) -> float:
        if name == "FA":
            return self.fa
        elif name == "MD":
            return self.md
        elif name == "AD":
            return self.ad
        elif name == "RD":
            return self.rd

    def get_metrics(self) -> List[float]:
        return [self.fa, self.md, self.ad, self.rd]

    def get_named_metrics(self) -> dict:
        return {"FA":self.fa, "MD":self.md, "AD":self.ad, "RD":self.rd}

    # def export(self, values:List[str]|None=None) -> str:
    #     if values is None:
    #         values =
