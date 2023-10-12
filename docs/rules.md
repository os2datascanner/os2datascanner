# Conversions and rules

This document is a short overview of OS2datascanner's capabilities for scanning
data: how rules work, how combining rules works, and how objects discovered by
the scanner engine are converted into searchable representations. (Collectively
all of these capabilities are sometimes grouped together and referred to as the
_rule engine_.)

## What _is_ a rule, anyway?

Fundamentally, a rule is a test: one or more properties that an object under
scan (a file, or an email, or...) must have. In OS2datascanner, objects that
pass the test of the user-specified rule associated with a scanner are
considered to have _matches_, the problems displayed in the report module.

This description is very generic, because rules _are_ generic! Some of them
map nicely onto search criteria: "find Danish civil registration numbers", or
"find matches for the regular expression `[0-9]{16}`". Some of them are
filters: "does the metadata indicate that this thing's been modified since last
Thursday at 20:08:51 local time?", or "does OS2datascanner know of a way to
treat this thing as an image?". Yet others are logical operators, for combining
other rules together.

## Key concepts

There's quite a lot of overlap between the rule engine's concepts, which is
unfortunate from an explanatory perspective, but let's see what we can do.

### `OutputType`
 
OS2datascanner defines a simple list of types for representations in the
`OutputType` enumeration (`os2datascanner.engine2.conversions.types.OutputType`).
Each one of these types represents an item of data that a rule might want to
look at. Here are a few examples:

* the plain text content of an object;
* the date an object was last edited; or
* the headers associated with an email.

### The conversion registry

The `os2datascanner.engine2.conversions.registry` package defines a function,
`convert`, that takes a `Resource` and converts it to the requested type, which
must be a member of the `OutputType` enumeration. (The scan pipeline's
`processor` stage is essentially a glorified wrapper around the `convert`
function: it prepares the next representation required and sends it on to the
`matcher` stage.)

For example, if we have a text file handle `h`, we can write something like
this to get its contents as a string:

```python
>>> h = FilesystemHandle.make_handle("/home/alec/demo.txt")
>>> convert(h.follow(source_manager), OutputType.Text)
'This is the content of the file.'
```

The specific implementation of the conversion will normally vary based on the
type of the underlying object. Converting a text file to `OutputType.Text` is
just a matter of opening it in text mode and calling its `read` function;
converting an image file is trickier, and will involve a call to the Tesseract
OCR engine behind the scenes -- but you don't need to care about that, because
`convert` will automatically find the right implementation by interrogating
the `Resource`'s type:

```python
>>> h2 = FilesystemHandle.make_handle("/home/alec/demo.png")
>>> convert(h2.follow(source_manager), OutputType.Text)
'This text was extracted with OCR.'
```

(`convert` does have a `mime_override` parameter, but this is normally not used
outside of an interactive shell in a development environment.)

#### Contributing a conversion

The `os2datascanner.engine2.conversions.registry` package also defines a
decorator, `@conversion`, that can be used to contribute a conversion for a
specific MIME type (or a wildcard conversion, if MIME types aren't important).
You could, for example, define a simple conversion from PDF to plain text by
doing something like this:

```python
import subprocess
from os2datascanner.engine2.conversions.types import OutputType
from os2datascanner.engine2.conversions.registry import conversion


@conversion(OutputType.Text, "application/pdf")
def textify_pdf(r):
    with r.make_path() as p:
        result = subprocess.run(
                ["pdftotext", p, "-"],
                capture_output=True, check=True)
        return result.stdout.decode().strip()
```

#### When _not_ to contribute a conversion

OS2datascanner doesn't actually have anything like that explicit conversion
from PDF to text. It can scan PDF files, though, so how does that work?

There's a special piece of fallback logic in the pipeline's `processor` stage,
that handles missing conversions by trying to treat an object with no
conversion as a container for other objects. (Think of a Zip file: we _could_
convert it to hexadecimal gibberish and claim that that's a text
representation, but wouldn't it make more sense to open the Zip file and
actually look at its actual contents?)

In general, structured documents like PDF files or office documents shouldn't
have explicit conversions; instead, they should be defined as containers of
simpler documents. For example, OS2datascanner considers a PDF file to be a
container for zero or more pages, each of which is itself a container for a
text file and zero or more embedded images. This has several advantages:

* the caching infrastructure of `SourceManager` can be reused, so we don't need
  to run external commands more often than necessary
* decomposing file formats into simpler ones means that every document type can
  benefit from optimisations to the common conversion functions
* treating file formats as OS2datascanner containers means that our references
  can be very precise (the system can report a match in `image on page 5 of
  document.pdf` instead of just `document.pdf`)

(See `engine2.md` for more information on how to implement `Source`s.)

### `SimpleRule`s

The main consumer of conversions in the OS2datascanner pipeline is the
`matcher` stage, which is in charge of running one or more `SimpleRule`s before
going back to the `processor` to ask for more conversions.

A `SimpleRule` is a very straightforward thing. At its core, all it needs to
define is a class attribute that declares the representation that it expects
(again as an `OutputType`), and a `match()` method that looks at that
representation and yields zero or more `dict`s describing the matches that it
found.

If we wanted to write a rudimentary `SimpleRule` that looked for payment card
numbers, for example, it would look something like this:

```
def luhn_algorithm(num: str):
    """Computes the Luhn check digit for a given string of digits. (The last
    digit of virtually all credit and debit card numbers is a Luhn check
    digit.)"""
    double = (len(num) % 2 == 1)
    tot = 0
    for ch in num:
        v = int(ch) * (2 if double else 1)
        tot += sum(int(c) for c in str(v))
        double = not double
    return 10 - (tot % 10)


class CreditCardRule(SimpleRule):
    operates_on = OutputType.Text

    def __init__(self):
        self._expr = re.compile(
                r"[0-9]{4}([- ]?[0-9]{4}){3}")

    def match(self, representation: str):
        for mo in self._expr.finditer(representation):
            # Canonicalise the joiners away
            num = "".join(ch for ch in mo.group() if ch.isdigit())

            # See if the check digit is what we expect
            if str(luhn_algorithm(num[:-1])) == num[-1]:
                yield {
                    "match": num
                }
```

### (Complicated) `Rule`s

Quite a lot of OS2datascanner rules operate on several different types of
conversions and represent complex boolean expressions. That doesn't sit well
with `SimpleRule`, so how do _those_ work?

This is where the parent class of `SimpleRule`, `Rule`, comes in. `Rule`
doesn't actually have a `match()` method; instead, it has a method called
`split()`, which breaks the object down into three things:

* a `SimpleRule` (with a `match` method) to evaluate next, known as the _head_;
* a `Rule` to continue with _if and only if_ the `SimpleRule` produces some
  matches, known as the _positive continuation_; and
* a second `Rule` to continue with if and only if the `SimpleRule` _doesn't_
  produce any matches, known as the _negative continuation_.

That is, you can't call `match()` on a `Rule`, but you can ask it for something
you _can_ call `match()` on -- and what you should do next with the result.
This is enough to provide very efficient execution, using the technique known
as [short-circuiting](https://en.wikipedia.org/wiki/Short-circuit_evaluation):
the only representations that OS2datascanner needs to compute are the ones that
are required to reduce a `Rule` to a conclusion.

```
>>> rule = AndRule.make(RegexRule("dog"), RegexRule("cat"), CPRRule())
>>> (sr, pve, nve := rule.split())
(RegexRule("dog"), AndRule(RegexRule("cat"), CPRRule()), False)
>>> pve.split()  # If we find "dog", what would the next step be?
(RegexRule("cat"), CPRRule(), False)
```

(The thing that makes `SimpleRule`s simple is actually just their
implementation of `split()`: their positive and negative continuations are
always `True` and `False` respectively. That is to say, they don't need to
chain to another rule: they give you an answer immediately.)

```
>>> RegexRule("dog").split()
(RegexRule("dog"), True, False)
```

## Fitting it all together

So, to recap:

* objects can be converted into a specific representation (or recursively
  explored to find something that can be);
* `SimpleRule`s take a single representation and, according to their settings,
  find zero or more matches inside it;
  and
* `Rule`s bind together one or more `SimpleRule`s into something that can
  express a complex search term, and can always be broken apart to give you the
  next step.

### Pretending things aren't complicated

`Rule`s may not have a `match()` method, but they _do_ have a helper function
called `try_match()`. This takes a function that can produce representations on
demand (or a normal `dict` keyed on `OutputType` values) and reduces the rule
as far as possible, given the representations that are available:

```
>>> r = OrRule.make(CPRRule(), RegexRule("dog"))
>>> representations = {
...     OutputType.Text.value: "Oh, good, I see a dog here"
... }
>>> conclusion, rules = r.try_match(representations)
>>> conclusion
True
>>> rules
[(CPRRule(), []), (RegexRule("dog"), [{'match': 'dog', 'offset': 18, 'context':
'Oh, good, I see a dog here', 'context_offset': 18, 'sensitivity': None}])]
```

Note that you also get the results of all the rules that _didn't_ match when
you use `try_match()` -- it gives you a faithful view of all the work done to
arrive at the conclusion.

If your representation function can't provide a representation needed by
`try_match()`, then it'll do as much as it can and will return the fragment
that still needs to be evaluated...

```
>>> r = AndRule.make(LastModifiedRule("2023-08-01T00:00:00Z"), RegexRule("dog"))
>>> representations = {
...     OutputType.LastModified.value: "2023-08-01T00:01:00Z")
... }
>>> remaining, rules = r.try_match(representations)
>>> remaining
RegexRule("dog")
>>> rules
[(LastModifiedRule("2023-08-01T00:00:00Z"), [{"match": "2023-08-01T00:01:00Z"}])]
```

... so you can continue evaluation of the rule once the next representation is
ready:

```
>>> representations[OutputType.Text.value] = "Oh, good, I see a dog here"
>>> conclusion, more_rules = remaining.try_match(representations)
>>> conclusion
True
```

(In the OS2datascanner pipeline, this is why the `processor` and `matcher`
stages send messages back and forth: `matcher` asks `processor` for the next
representation rather than running the conversion itself.)

The last trick `try_match()` has up its sleeve is a cache. No matter how many
times a `SimpleRule` pops up during the execution of a `Rule`, `try_match()`
will only ever evaluate it once:

```
>>> r = AndRule.make(
...         *[RegexRule("dog") for _ in range(0, 5000)])  # Many rules...
>>> representations = {
...     OutputType.Text.value: (
...             "What a good dog this is " + ("lorem ipsum " * 15000))
... }  # ... on a large text
>>> r.try_match(representations)
(True, [(RegexRule("dog"), [{'match': 'dog', 'offset': 12, 'context': 'What a
good dog this is lorem ipsum lorem ipsum lorem ipsum lorem', 'context_offset':
12, 'sensitivity': None}])])
```

### Other helper functions

All of the logical operators have one peculiar feature: you're not supposed to
use their constructors. Instead, you should go through the factory class method
called `make`.

These factory methods (which are also used internally when `Rule`s get split)
allow the logical operators to do some simplification. A logical operator with
one argument, for example, is just reduced to that argument.

```
>>> ar = AndRule.make(CPRRule())
>>> or = OrRule.make(CPRRule())
>>> ar == or
True
```

This is also where short-circuiting is actually implemented. `AndRule` and
`OrRule` can detect `False` and `True` respectively to stop their evaluation:

```
>>> AndRule.make(True, CPRRule(), VeryComplicatedRule(), False)
False
>>> OrRule.make(False, False, CPRRule(), VeryComplicatedRule(), True)
True
```

(Strictly speaking, the `make` methods implement something stronger than
short-circuiting, as the element that forces a specific conclusion can occur
_anywhere_ in the list, not just at the beginning. In practice, though,
OS2datascanner only ever consumes things from the beginning of the rule.)

There's also one other convenience function: `make_if`. OS2datascanner uses
this to express conditional rules: the most common use of this in the codebase
is "if this file is an image, then its dimensions mustn't be too small or too
big". The implementation of this is simple enough to repeat here:

```
def make_if(predicate, then, else_):
    return OrRule.make(
        AndRule.make(predicate, then),
        AndRule.make(NotRule.make(predicate), else_),
    )
```

Note that the predicate -- the "if this file is an image" part in the example
above -- appears twice: once in a positive sense to gate the `then` branch, and
once in a negative sense to gate the `else_` branch. This may seem redundant,
but remember what `OrRule` means: without the negation, it would be possible to
escape into the `else_` branch _upon the failure of the `then` branch_, which
would be a rather useless conditional. ("If A then B, but if A and not B
then... oh well, keep going"?)

### Down but not up

One important detail to remember when building an OS2datascanner `Rule` is that
the `processor` stage is allowed to recurse down into an object to look for
more conversions, _but is not allowed to go back up again_. This makes the
pipeline much more efficient, but it does bring one small complication with it.

Let's say you have an office document of some kind. Its text contains a CPR
number, and it was last changed on the 1st of August 2023 at 10am. If you write
the following rule, though, it will always succeed. Why?

```
AndRule.make(
    CPRRule(),
    LastModifiedRule("2023-08-01T11:00:00Z")  # This is after 10am, surely?
)
```

The answer is that there's no direct conversion from your office document to
`OutputType.Text`, so we had to invoke an external tool to recursively explore
it, and that external tool's output files are fresh and so pass the
`LastModifiedRule` test. Argh!

The good news, though, is that an efficiently implemented rule won't be
impacted by this. If you reorder your rule to put cheap metadata tests at the
start and expensive content tests at the end, that'll make sure that all of the
metadata tests operate on the original file.

## Executing a `Rule`

Let's take a real, complex rule, one that OS2datascanner might generate in a
production system, and see how the system evaluates it:

```
AndRule(
    LastModifiedRule("2023-08-01T00:00:00Z"),
    OrRule(
        AndRule(
            HasConversionRule(OutputType.ImageDimensions),
            DimensionsRule(
                    range(32, 32),
                    range(16384, 16384),
                    min_dim=128),
        ),
        NotRule(
            HasConversionRule(OutputType.ImageDimensions),
        ),
    ),
    CPRRule(),
)
```

We might express this rule in English as "the object has been changed after
midnight on the 1st of August, and (if it's an image) then its dimensions are
between 32x128 or 128x32 and 16384x16384, and a CPR number has been found in
its text".

Let's also find all of the representation types we'll need to execute this
rule...

```
>>> def yield_required_representations(r: Rule):
...     sr, *continuations = r.split()
...     yield sr.operates_on
...     for c in continuations:
...         if not isinstance(c, bool):
...             yield from yield_required_representations(c)
... 
>>> set(yield_required_representations(rule))
{<OutputType.Text: 'text'>, <OutputType.LastModified: 'last-modified'>,
 <OutputType.ImageDimensions: 'image-dimensions'>}
```

... and specify some values for these:

```
>>> representations = {
...     OutputType.LastModified.value: "2023-08-01T00:01:00Z",
...     OutputType.ImageDimensions.value: None,
...     OutputType.Text.value: "My CPR number is 111111-1118"
... }
```

1. Split the rule:

   | `head` | +ve | -ve |
   | ------ | --- | --- |
   | `LastModifiedRule("2023-08-01T00:00:00Z")` | `AndRule(OrRule(...), CPRRule())` | `False` |

   As this rule is an `AndRule`, its positive continuation is "everything else"
   and its negative continuation is `False` -- that is, we can terminate
   execution immediately if the object is too old.

   We look at the `OutputType.LastModified` value and find a newer timestamp.
   We record that match and continue.

2. We found a match, so we split the positive continuation of the last rule:

   | `head` | +ve | -ve |
   | ------ | --- | --- |
   | `HasConversionRule(OutputType.ImageDimensions)` | `AndRule(DimensionsRule(...), CPRRule())` | `AndRule(NotRule(...), CPRRule())` |

   Can we convert this object to an image? `HasConversionRule` looks at the
   `OutputType.ImageDimensions` value, finds `None`, and concludes that we
   cannot. We record this lack of a match and continue.

3. Now we split the negative continuation of the last rule.

   | `head` | +ve | -ve |
   | ------ | --- | --- |
   | `HasConversionRule(OutputType.ImageDimensions)` | `False` | `CPRRule()` |

   As we discussed earlier, we have a `NotRule` here to make sure that images
   can't escape the dimensions test. We don't actually run `HasConversionRule`
   again, though, because we've already recorded its lack of a match.

   Note that `NotRule` has disappeared! It's done its job, though: splitting it
   has given us a positive continuation _that terminates immediately without a
   match_, while only the negative match represents further work.

   We reuse the lack of a match, from the last time we saw this
   `HasConversionRule` (not recording it a second time, though, because we
   don't need to), and continue.

4. Once again, we split the negative continuation of the last rule.

   | `head` | +ve | -ve |
   | ------ | --- | --- |
   | `CPRRule()` | `True` | `False` |

   OK, this is it; after executing this rule, we'll have arrived at our
   conclusion.

   `CPRRule` looks at our `OutputType.Text` value and finds a match:
   111111-1118! We record this match and... stop, because we've arrived at a
   `bool` conclusion.

5. We return the conclusion, along with all of the matches we found along the
   way.

```
>>> conclusion, matches = rule.try_match(representations)
>>> conclusion
True
>>> from pprint import pprint
>>> pprint(matches)
[(LastModifiedRule("2023-08-01T00:00:00Z"),
 [{'match': '2023-08-01T00:01:00+0000'}]),
(HasConversionRule(OutputType.ImageDimensions),
 []),
(CPRRule()),
 [{'context': 'My CPR number is XXXXXX-XXXX',
   'context_offset': 17,
   'match': '1111XXXXXX',
   'offset': 17,
   'probability': 1.0,
   'sensitivity': None}])]
```
