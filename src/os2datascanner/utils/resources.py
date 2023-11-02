from pathlib import Path


def get_resource_folder():
    return Path(__file__).parent.parent.parent.parent / "resources"
