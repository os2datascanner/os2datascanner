import json
import pathlib


class LoaderError(Exception):
    pass


class DatasetNotFoundError(LoaderError):
    pass


_HERE = pathlib.Path(__file__).parent


class Loader:
    def __init__(self, *categories):
        self._datasets = {}

        for c in categories:
            self.load_category()

    def categories(self):
        return self._datasets.keys()

    def datasets(self, category):
        return self._datasets.get(category, {}).keys()

    def get_category(self, category):
        return self._datasets.get(category)

    def get_dataset(self, category, dataset):
        cat = self.get_category(category)
        return cat.get(dataset) if cat else None

    def load_category(self, category):
        try:
            category_folder = _HERE.joinpath(category)
            for f in category_folder.iterdir():
                if f.is_file() and f.name.endswith(".jsonl"):
                    self.load_dataset(category, f.stem)
        except FileNotFoundError:
            raise DatasetNotFoundError(category, None)

    def load_dataset(self, category, dataset):
        try:
            dataset_file = _HERE.joinpath(category, dataset + ".jsonl")
            entries = []
            for line in dataset_file.open("rt"):
                entries.append(json.loads(line))
            self._datasets.setdefault(category, {})[dataset] = entries
            return entries
        except FileNotFoundError:
            raise DatasetNotFoundError(category, dataset)


common = Loader()
