from .engine import ClassificationEngine, BonusClassificationEngine


def taxon_json_taxonomy_to_classification_engine(obj):  # noqa: CCR001
    """Attempts to build a ClassificationEngine object from a Taxon 3.x JSON
    taxonomy description.

    Note that the translation process is likely to be inaccurate and is known
    to be incomplete."""
    if ("system" not in obj
            or "versions" not in obj["system"]
            or "taxon_version" not in obj["system"]["versions"]
            or obj["system"]["versions"]["taxon_version"] != "3.x"):
        raise Exception("Unsupported JSON object")

    ce = BonusClassificationEngine(
            obj["system"]["score"]["firstClassExtraWeight"])
    for ident, class_ in obj["classes"].items():
        kl = ce.add_classification(
                ident, class_["title"],
                class_["thresholdWeight"],
                class_["thresholdCount"],
                class_["thresholdCountUnique"])
        for title, term in (class_["terms"] or {}).items():
            title_obj = ClassificationEngine.WordTerm.affixed(
                    term["weight"],
                    (term["prefix"] or "").split("|"),
                    title,
                    (term["suffix"] or "").split("|"))
            if term["required"]:
                kl.all_of.append(title_obj)
            elif term["requiredOr"]:
                kl.at_least_one_of.append(title_obj)
            else:
                kl.any_of.append(title_obj)

            if (requireText := term.get("requireText")):
                kl.all_of.extend(
                        ClassificationEngine.RegexTerm(None, frag)
                        for frag in requireText.split("||"))
            if (requireTerm := term.get("requireTerm")):
                kl.all_of.extend(
                        ClassificationEngine.WordTerm(None, frag)
                        for frag in requireTerm.split("||"))

            if (excludeOnText := term.get("excludeOnText")):
                kl.none_of.extend(
                        ClassificationEngine.RegexTerm(None, frag)
                        for frag in excludeOnText.split("||"))
            if (excludeOnTerm := term.get("excludeOnTerm")):
                kl.none_of.extend(
                        ClassificationEngine.WordTerm(None, frag)
                        for frag in excludeOnTerm.split("||"))

            # XXX: excludeOnClass?

    return ce
