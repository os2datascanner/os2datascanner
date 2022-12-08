import re
from abc import ABC, abstractmethod


class ClassificationEngine:
    """A ClassificationEngine attempts to assign categories to a piece of input
    text."""

    class AbstractTerm(ABC):
        """An AbstractTerm (usually just known as a "term") represents an
        acceptance criterion for a text."""
        def __init__(self, weight: int):
            self.weight = weight

        @abstractmethod
        def matches(self, text: str) -> int:
            """Indicates how many different reasons this term has to accept a
            given text."""

    class BaseRegexTerm(AbstractTerm):
        """A BaseRegexTerm is a regular expression-based term: if a text
        contains one or more matches for the given regular expression, then it
        is accepted."""
        def __init__(self, weight: int, term: str, flags: int = 0):
            super().__init__(weight)
            self._re = re.compile(term, flags)

        def matches(self, text: str) -> int:
            return len(self._re.findall(text))

        def __repr__(self):
            return f"{self._re}"

    class RegexTerm(BaseRegexTerm):
        """A RegexTerm is a BaseRegexTerm with automatic escaping."""
        def __init__(self, weight: int, term: str, flags: int = 0):
            super().__init__(weight, re.escape(term), flags)

    class WordTerm(BaseRegexTerm):
        """A WordTerm is a BaseRegexTerm with automatic escaping and word
        boundaries."""
        def __init__(self, weight: int, term: str, flags: int = 0):
            super().__init__(weight, rf"\b{re.escape(term)}\b", flags)

        @classmethod
        def affixed(cls, weight, prefixes, word, suffixes):
            rx = r"\b"
            if prefixes:
                rx += "(" + "|".join(re.escape(p) for p in prefixes) + ")?"
            rx += re.escape(word)
            if suffixes:
                rx += "(" + "|".join(re.escape(s) for s in suffixes) + ")?"
            rx += r"\b"

            return ClassificationEngine.BaseRegexTerm(weight, rx)

    class Classification:
        """A Classification is a category to which texts can be assigned by a
        ClassificationEngine.

        A Classification consists of four groups of terms:

        * terms which must *not* be found in the input text;
        * terms which must be found in the input text;
        * terms of which at least one must be found in the input text; and
        * terms which may optionally appear in the input text.

        Each term in the latter three groups also contributes a weight, a
        score indicating the importance of the match. Classifications make a
        final decision about whether or not to accept a text on the basis of
        weight and match and term count threshold values."""
        def __init__(
                self,
                ident: str,
                label: str,
                threshold: int = 10,
                threshold_match_count: int = 1,
                threshold_term_count: int = 1):
            self.ident = ident
            self.label = label
            self.threshold = threshold
            self.threshold_match_count = threshold_match_count
            self.threshold_term_count = threshold_term_count

            self.all_of: list['ClassificationEngine.AbstractTerm'] = []
            self.at_least_one_of: list['ClassificationEngine.AbstractTerm'] = []
            self.any_of: list['ClassificationEngine.AbstractTerm'] = []
            self.none_of: list['ClassificationEngine.AbstractTerm'] = []

        def __repr__(self):
            return (f"Classification("
                    f"{self.ident!r}, {self.label!r},"
                    f" {self.threshold!r}, {self.threshold_match_count!r},"
                    f" {self.threshold_term_count!r})")

        def classify(self, text: str, *, rv: dict):  # noqa: CCR001
            """Checks whether or not this Classification accepts the given
            text. Returns a (total weight, number of matched terms) tuple if
            it does, and None if it doesn't."""
            weight = 0
            match_count = 0  # The number of total matches across all terms
            term_count = 0  # The number of total terms with matches

            def run_term(t: 'ClassificationEngine.AbstractTerm'):
                nonlocal weight, match_count, term_count

                rv = t.matches(text)
                if rv:
                    if t.weight is not None:
                        weight = (weight or 0) + (t.weight * rv)
                    match_count += rv
                    term_count += 1
                return rv

            # Don't use run_term here -- exclusion rules shouldn't contribute
            # anything to the weight
            if any(excl.matches(text) for excl in self.none_of):
                return None

            if not all(run_term(req) for req in self.all_of):
                return None

            if self.at_least_one_of:
                passed = False
                # We can't use any here because we don't want its short-
                # circuiting behaviour -- all of these terms should be able to
                # contribute to the total weight
                for a in self.at_least_one_of:
                    if run_term(a):
                        passed = True
                if not passed:
                    return None

            for a in self.any_of:
                run_term(a)

            if (weight >= self.threshold
                    and match_count >= self.threshold_match_count
                    and term_count >= self.threshold_term_count):
                return (weight, match_count, term_count)
            else:
                return None

    def __init__(self):
        self._classes = {}

    def add_classification(self, ident: str, *args, **kwargs):
        """Registers a new Classification with this ClassificationEngine and
        returns it."""
        c = ClassificationEngine.Classification(ident, *args, **kwargs)
        self._classes[ident] = c
        return c

    def get_classification(self, ident: str, default=None):
        return self._classes.get(ident, default)

    def register_result(self, results: dict, ident: str, weight: int):
        results[ident] = results.get(ident, 0) + weight

    def classify(self, text: str):
        """Attempts to assign one or more of the Classifications known to this
        ClassificationEngine to the provided text. Returns a sequence of
        (Classification, weight) pairs, ordered by descending weight."""
        rv = {}

        for klass in self._classes.values():
            c = klass.classify(text, rv=rv)
            if c is not None:
                weight, _, _ = c
                self.register_result(rv, klass.ident, weight)

        return sorted(
                ((self.get_classification(ident), weight)
                 for ident, weight in rv.items()),
                key=lambda item: item[1],
                reverse=True)
