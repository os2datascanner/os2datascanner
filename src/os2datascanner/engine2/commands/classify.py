import sys
import json

from ..utilities.classification.compat import (
        taxon_json_taxonomy_to_classification_engine)


def main(taxonomy, *files_to_scan):
    with open(taxonomy, "rt") as fp:
        engine = taxon_json_taxonomy_to_classification_engine(json.load(fp))

    for f in files_to_scan:
        print(f)
        with open(f, "rt") as fp:
            for classification, weight in engine.classify(fp.read())[:5]:
                print("\t", classification.ident, classification.label, weight)


if __name__ == "__main__":
    main(*sys.argv[1:])
