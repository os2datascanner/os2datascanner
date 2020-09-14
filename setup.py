#!/usr/bin/env python3

import pathlib
import setuptools

def all_lines_of(*project_relative_path_fragments):
    return (pathlib.Path(__file__)
            .parent.joinpath(*project_relative_path_fragments)
            .read_text().splitlines())

setuptools.setup(
    install_requires=(
        all_lines_of("requirements",
                "python-requirements", "requirements-admin.txt") +
        all_lines_of("requirements",
                "python-requirements", "requirements-engine.txt")
    )
)
