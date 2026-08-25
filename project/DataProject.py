from __future__ import annotations

import os

from Project import Project
from data.SubjectsData import SubjectsData


class DataProject(Project):
    """
    Project variant for data-only analysis (no MRI tools required).
    Adds input_data_dir and output_data_dir alongside the project folder.
    """

    def __init__(self, proj_dir: str, data: str | SubjectsData = "data.xlsx"):
        self.input_data_dir  = os.path.join(proj_dir, "input_data")
        self.output_data_dir = os.path.join(proj_dir, "output_data")

        os.makedirs(self.input_data_dir,  exist_ok=True)
        os.makedirs(self.output_data_dir, exist_ok=True)

        super().__init__(proj_dir, data)
