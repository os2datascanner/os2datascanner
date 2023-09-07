# Extending OS2Datascanner

This document is a short guide to adding new sources of data to
OS2Datascanner's scanner engine, `engine2`.

> `engine2` is so called because it's the second major version of the
> OS2Datascanner engine. The first, used from 2014 to 2020, was built on the
> *Scrapy* web crawling framework.
>
> Most of the advanced functionality of the scanner engine is used by the
> pipeline. Some objects are also used in the administration system and in the
> report module. You can also just use it from your own Python scripts or from
> the shell, provided that all of its dependencies are installed in your local
> Python environment.


## Key scanner engine concepts

At the heart of the scanner engine is its *model*. The model consists of three
abstract base classes and a number of helper classes.

### `Source`

A `Source` represents a local or remote data source. It stores all of the
information needed to open, or connect to, a data source, and implements a
strategy for exploring that data source to find objects.

The `Source` API, as we'll soon see, is very minimal, and so can serve as a
wrapper around arbitrarily complicated interfaces.

`Source`s are *stateless*. They do have functions that create and operate on
state, but these can only be used along with an instance of a state management
class called `SourceManager`.


### `Handle`

A `Handle` is a reference to an object. The exploration strategy of a `Source`
produces these.

In general, an "object" is a user-recognisable leaf node in a hierarchy. For
example, `engine2`'s filesystem exploration code returns a `FilesystemHandle`
for each normal file it finds; folders are ignored.

The standard implementation of `Handle` has only two properties: a `Source` and
a `str` path to a specific object.

`Handle`s are roughly equivalent to URLs: they refer to the unique location of
an object, carry enough information to establish a connection to that object,
and have a standard serialisation form to enable them to be saved and sent
between different bits of the system. (Keeping URL-like objects, even after
removing Scrapy, was a deliberate design goal of `engine2`.)

Like `Source`s, `Handle`s are also stateless.


### `Resource`

A `Resource` is a *followed* `Handle`. That is, it's not just a *reference* to
an object: it represents an available object, with concrete operations that
have access to its metadata and content.

Just as a `Handle` can be considered as a `Source` and a path joined together,
a `Resource` is essentially a `Handle` bound to a `SourceManager`: a reference
to an object, and the state that allows that object to be accessed.


## Statelessness and equality

`engine2`'s objects are stateless because they're designed to be serialisable,
and the best way of making sure that state is kept consistent across space and
time is by not having it!

Many `engine2` classes override the Python `__eq__` and `__hash__` methods. For
example, objects that open an equivalent connection to an external resource
compare equal to each other:

    SMBCSource("//SERVER/Folder", username="alec", password="secret")
    == SMBCSource("//SERVER/Folder", username="alec", password="secret", driveletter="X")

Overriding equality in this way makes it possible to implement the following
logic to share and reuse connections:

```python
opened_sources = {}
def open_source(source):
    if source not in opened_sources:
        opened_sources = source.open()
    return opened_sources[source]
```

> (This won't actually work because `Source`s don't have an `open` method as
> part of their public API, but this is, in principle, what `SourceManager`
> does behind the scenes.)


## Adding a new data source

Supporting a new data source is a matter of implementing three classes: a
`Source` subclass, a `Resource` subclass, and a `Handle` subclass to join them
together.

> (Depending on the data source, it might make sense to implement more than one
> of each of these, but normally one is enough.)

Data sources are only interesting if they have some data to back them. A real
source would presumably be backed by a remote service of some kind, but to keep
things simple, we'll just use a toy file system stored in a Python dictionary:

```python
backing_store = {
    "alec:secretpassword": {
        "/home/alec/Documents/secrets.txt": {
            "type": "text/plain",
            "content": b"A big dog!"
        },
        "/home/alec/Downloads/smile.png": {
            "type": "image/png",
            "content": b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00'
                       b'\x08\x00\x00\x00\x08\x08\x02\x00\x00\x00Km)\xdc'
                       b'\x00\x00\x00*IDAT\x08\xd7c\xfc\xff\xff?\x036\xc0'
                       b'\x04\xa1\x18\x19\x19\xd1\x18L\x0c8\x00N\tF|v\xc0'
                       b'\xcdE\xb6\x86\x05\xcdN\xc2F\x01\x00\xc6#\t\x16'
                       b'\xd7\xf5M}\x00\x00\x00\x00IEND\xaeB`\x82'
        }
    }
}
```

"Authentication" against this data source will be performed by joining the
username and password together with a `:` in the middle and doing a dictionary
key lookup; exploration will then be a simple matter of iterating over the keys
in the resulting dictionary. Outside of `engine2`, here's what that might look
like:

```python
def explore(username, password):
    auth_string = "{0}:{1}".format(username, password)
    if not auth_string in backing_store:
        raise ValueError("Username or password incorrect")

    files = backing_store[auth_string]
    for path, descriptor in files.items():
        yield (path, descriptor["type"], descriptor["content"])
```


## The exploration strategy: `ToySource`

Let's translate that to `engine2`. The data source and its exploration strategy
will be modelled by a `Source` subclass, which will emit `Handle` references
that can be followed to their content through a `Resource`:

```python
from os2datascanner.engine2.model.core import (
        Source, ResourceUnavailableError)

class ToySource(Source):
    type_label = "toy"

    def __init__(self, username, password):
        self._username = username
        self._password = password
```

> The constructor of a `Source` should take all the information needed to open
> a connection and log in to a data source. Here, that's just a simple username
> and password; in the real world, it could be a username and password, or an
> API key, or an OAuth token.

Now we need to implement the exploration strategy, and the generator function
that creates the state object. In the real world, this function would open a
connection to a remote server, authenticate against it, yield a cookie of some
kind, and then clean up after it when the generator stops. Our toy example can
be much simpler:

```python
def _generate_state(self, source_manager):
    auth_string = "{0}:{1}".format(self._username, self._password)
    if not auth_string in backing_store:
        raise ResourceUnavailableError(self,
                "Username or password incorrect")
    else:
        yield backing_store[auth_string]
```

We never call this state function explicitly, though. Instead, `ToySource`
objects call the `SourceManager.open` method on themselves:

```python
def handles(self, source_manager):
    files = source_manager.open(self)
    for path, descriptor in files.items():
        yield ToyHandle(self, path)
```

`SourceManager.open` is the real version of the hypothetical `open_source`
function we saw earlier. It will either return a cached cookie or call
`_generate_state` to make a fresh one (which will itself then be cached).

> `SourceManager` implements a lot of `engine2`'s clever behaviour: for
> example, opening a `Source` might cause older `Source`s to be closed.
>
> `_generate_state` is an important internal API. Its return value (as returned
> by `SourceManager.open`) is also the entire interface between a `Source` and
> its `Resource` subclass, so that value must also expose everything needed to
> retrieve file data and metadata.
>
> Some classes make API guarantees for their `_generate_state` method.  For
> example, the `FilesystemSource` method states that it yields a directory
> path. This allows us to mix and match classes in weird ways: if another
> `Source` also puts objects in the filesystem and implements a compatible
> `_generate_state` method, then it can reuse the `FilesystemResource` class to
> give access to them. (See `os2datascanner.engine2.model.derived.pdf` for an
> example of this.)

The implementation of our `Source` is now substantially finished, but we can't
instantiate this object just yet:

```python
>>> ToySource()
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
TypeError: Can't instantiate abstract class ToySource with abstract methods
censor, to_json_object
```

> Note that we *don't* need to explicitly override `__eq__` and `__hash__` in
> our new class: inheriting from `Source` (or `Handle`) automatically gives us
> appropriate implementations of these methods.


### Censoring objects

`Source`s, in general, carry sensitive information. (Even our `ToySource` has a
username and password.) This sensitive information is necessary for the model
to do its job, but when we want to send objects to a lower-privilege system, we
want to be able to remove this information.

> This is what happens at the end of the pipeline: there's a stage, the
> *exporter*, that censors all `engine2` objects before serialising them and
> sending them to be stored in a database.

Both `Source` and `Handle` define an abstract method called `censor`.  This
method should return a version of the original object but with the sensitive
information stripped off:

```python
def censor(self):
    return ToySource(username=None, password=None)
```

The documentation for `Source` points out something important about these
objects:

> The resulting Source will not necessarily carry enough information to
> generate a meaningful state object, and so will not necessarily compare equal
> to this one.

That is, a censored `Source` is supposed to be *presentationally* equivalent to
the original one, but nothing more: it carries enough information to be able to
point a user at the right website or network drive, but not enough to actually
give access to any objects.)


### Serialisation

To give us as much flexibility as possible, to help with debugging, and to make
the system's internal messages human-readable, `engine2` requires that every
class explicitly define its serialised forms.

`Source`s *must* implement a method called `to_json_object` and *should*
implement a static method called `from_json_object`. The first of these returns
an object suitable for JSON serialisation, and the second is given a decoded
JSON object and returns a new `Source` of an appropriate type.

```
def to_json_object(self):
    return dict(**super().to_json_object(), **{
        "username": self._username,
        "password": self._password
    })
```

The `super` implementation of this function just returns the dict `{"type":
class.type_label}`. The `type` property is used elsewhere in the system to
determine what kind of object is being deserialised.

```python
@staticmethod
@Source.json_handler(type_label)
def from_json_object(obj):
    return ToySource(
            username=obj["username"],
            password=obj["password"])
```

`engine2` uses decorators a lot to manage internal registries of things. The
`Source.json_handler` decorator adds things to the registry behind the
`Source.from_json_object` function -- the pipeline uses this function to load
serialised `Source`s without having to know anything about them.

It's not important that a method with the specific name `from_json_object`
exists: what's important is that an appropriate method is added to the
internal registry.

With that, our new `Source` is ready!


## References: `ToyHandle`

The next thing to implement is `ToyHandle`. As this is a simple `Handle` (it
just binds a `Source` to a named object), the `Handle` base class will
implement almost everything for us:

```python
from os2datascanner.engine2.model.core import Handle

@Handle.stock_json_handler("toy")
class ToyHandle(Handle):
```

Since we don't store any properties other than a `Source` and a path, we can
use the `Handle.stock_json_handler` decorator, which automatically registers a
standard `from_json_object`-like function with the registry used by the
`Handle.from_json_object` function.

```python
type_label = "toy"
source_type = ToyResource
```

The `Handle` class defines a method, `follow`, that binds a `Handle` to a
`SourceManager` and returns a new `Resource`. The implementation of this
function is always the same: `return self.resource_type(self, source_manager)`.

(This is, of course, a forward reference to a class we haven't defined yet!
When we do eventually define `ToyResource`, it should sit between `ToySource`
and `ToyHandle`.)

```python
@property
def presentation(self):
    return self.relative_path
```

Because `engine2` objects can get quite complicated, the `Handle` API is also
used by the user interface components of OS2Datascanner to compute names for
things. This is the job of the `Handle.presentation` method: it should return
something that the user recognises as a name.

There's also an optional `Handle.presentation_url` method that returns a
user-friendly link to an object. The definition of "link" is deliberately a bit
fuzzy: for example, an message in an email account scanned over IMAP might have
a `presentation_url` implementation that points at a webmail system. We don't
need to define that here, though, since there are no meaningful links to Python
dictionary members.

```python
def censor(self):
    return ToyHandle(self.source.censor(), self.relative_path)
```

`Handle`s carry `Source` references, so they need to be censorable as well. (A
`Source` is supposed to be presentationally equivalent to its censored form,
which in turn means that `handle.presentation` is supposed to be equal to
`handle.censor().presentation`.)

`Handle` automatically provides a few other useful functions, like
`guess_type`, which returns an educated guess for the object's MIME type.

The default implementation of `Handle.guess_type` just looks at the name and
makes a decision based on the file extension, but this too can be overridden.
(Don't try to do anything too clever in this method, though --remember that
`Handle`s are just references and can't look at content.)


## Operations: `ToyResource`

We can now discover and point at objects in our toy filesystem. This is a good
start, but now we need to be able to do things to those objects: we need a
`Resource`.

More specifically, since our objects look like files, we need the subclass
`FileResource`, which takes care of some of the basics for us:

```python
from contextlib import contextmanager
from os2datascanner.engine2.model.core import FileResource

class ToyResource(FileResource):
    def __init__(self, handle, sm):
        super().__init__(handle, sm)
        self._entry = None

    def _get_entry(self):
        if not self._entry:
            self._entry = self._get_cookie()[self.handle.relative_path]
        return self._entry
```

`Resource`s are short-lived and not serialisable, so they're allowed to track
state. Here, for example, is a simple cache of the underlying dictionary entry.
(`Resource._get_cookie` is a utility method that calls
`SourceManager.open(self.handle.source)` on the `Resource`'s bound
`SourceManager`.)

```python
def get_last_modified(self):
    return super().get_last_modified()
```

Files in the `engine2` world always have a last modification date associated
with them. There *is* a default, naïve implementation of this method in
`FileResource`, which returns the time the method was first called; There are
virtually always better approaches available, though, so it's declared as an
abstract method to force subclasses to explicitly decide whether or not to use
it.

Our toy filesystem doesn't have enough information for us to do better, so
we'll just use the default implementation.

```python
def get_size(self):
    return len(self._get_entry()["content"])

@contextmanager
def make_stream(self):
    from io import BytesIO
    yield BytesIO(self._get_entry()["content"]
```

Here are the two methods at the heart of `FileResource`: `get_size`, which
retrieves a metadata property, and `make_stream`, which makes the file's
content available to the rest of the OS2datascanner system.

```python
@contextmanager
def make_path(self):
    from os2datascanner.engine2.model.utilities import (
            NamedTemporaryResource)
    with NamedTemporaryResource(self.handle.name) as ntr:
        with ntr.open("wb") as res:
            with self.make_stream() as s:
                res.write(s.read())
        yield ntr.get_path()
```

`FileResource` comes with a few other useful methods, such as `compute_type`, a
counterpart to `Handle.guess_type` that\'s actually allowed to look at the
content of the file.


## Trying it out

Now that our new data source is modelled, we can try it out by listing all of
its files:

```python
>>> from toy import *
>>> from os2datascanner.engine2.model.core import SourceManager
>>> sm = SourceManager()
>>> source = ToySource(username="alec", password="secretpassword")
>>> [h.relative_path for h in source.handles(sm)]
['/home/alec/Documents/secrets.txt', '/home/alec/Downloads/smile.png']
```

Then we can print more information about these files:

```python
>>> for h in source.handles(sm:
...     print(h.relative_path)
...     r = h.follow(sm)
...     print("\tSize: {0} bytes".format(r.get_size()))
...     if h.guess_type() == "text/plain":
...         print("\tContent:")
...         with r.make_stream() as fp:
...             print("\t\t{0}".format(fp.read().decode()))
...
/home/alec/Documents/secrets.txt
    Size: 10 bytes
    Content:
        A big dog!
/home/alec/Downloads/smile.png
    Size: 99 bytes
```

To see how the pipeline can work with data sources of all kinds without knowing
what they are, we can try working with the JSON form of `ToySource`:

```python
>>> import toy
>>> from os2datascanner.engine2.model.core import Source, SourceManager
>>> sm = SourceManager()
>>> generic_source = Source.from_json_object({
...         "type": "toy", "username": "alec",
...         "password": "secretpassword"})
>>> [h.relative_path for h in generic_source.handles(sm)]
['/home/alec/Documents/secrets.txt', '/home/alec/Downloads/smile.png']
```


## Wheels within wheels

The description of `Handle`s earlier glossed them as references to "objects".
But what *is* an object?

To some extent this depends on the `Source`. In a filesystem, an object is a
file: a named stream of bytes with some metadata. In an email account, an
object is an email. In a case management system, an object is a case.

But sometimes the lines are blurrier than that. For example, consider a Zip
file. It *is* a file: it's a stream of bytes with a name, a size, and some
metadata. It can also, however, be viewed as a container for other files, each
of which in turn also has these properties.

Let's put one into the toy filesystem and see what happens.

```python
backing_store["alec:secretpassword"]["/home/alec/hello.zip"] = {
    "type": "application/zip",
    "content": b"PK\x03\x04\x14\x00\x00\x00\x08\x00a~\xbdP4\x01\xd3p@"
               b"\x00\x00\x00C\x00\x00\x00\t\x00\x1c\x00hello.txtUT\t"
               b"\x00\x03E\x13\xd1^c\x12\xd1^ux\x0b\x00\x01\x04\xe8"
               b"\x03\x00\x00\x04\xe8\x03\x00\x00\xf3H\xcd\xc9\xc9\xd7"
               b"Q(\xcf/\xcaIQ\xe4\n\xc9\xc8,V\x00\xa2\xfc\xbc\x9cJ"
               b"\xaeD\x85\x92\xd4\xe2\x12=\xa0`jQ*H4/\x9f+/55E\xa1$_!"
               b")\x95+1'\xb1(75E\x8f\x0b\x00PK\x01\x02\x1e\x03\x14"
               b"\x00\x00\x00\x08\x00a~\xbdP4\x01\xd3p@\x00\x00\x00C"
               b"\x00\x00\x00\t\x00\x18\x00\x00\x00\x00\x00\x01\x00"
               b"\x00\x00\xa4\x81\x00\x00\x00\x00hello.txtUT\x05\x00"
               b"\x03E\x13\xd1^ux\x0b\x00\x01\x04\xe8\x03\x00\x00\x04"
               b"\xe8\x03\x00\x00PK\x05\x06\x00\x00\x00\x00\x01\x00"
               b"\x01\x00O\x00\x00\x00\x83\x00\x00\x00\x00\x00"
}
```

Since we know how our objects behave, we can skip the exploration strategy
altogether and manually construct a `ToyHandle` to this object:

```python
ToyHandle(
        ToySource(
                username="alec",
                password="secretpassword"),
        "/home/alec/hello.zip")
```

`ToyResource` doesn't expose a lot of operations, but it does return a Python
file object pointing at the content of the Zip file. As luck would have it, the
Python standard library has a module for working with Zip files:

```python
>>> from zipfile import ZipFile
>>> resource = handle.follow(sm)
>>> with resource.make_stream() as fp:
...     print(ZipFile(fp).infolist())
[<ZipInfo filename='hello.txt' compress_type=deflate filemode='-rw-r--r--'
file_size=67 compress_size=64>]
```

Is there a way of exploring this Zip file from inside `engine2`? If, for
example, the pipeline is asked to look for the text `illegal`, and it finds a
Zip file, then text conversion won't work -- the result would be binary
gibberish. But shouldn\'t there be some way to recurse into the Zip file and
look at the things inside it?

There is:

```python
>>> from os2datascanner.engine2.model.derived.zip import ZipSource
>>> [h.relative_path for h in ZipSource(handle).handles(sm)]
['hello.txt']
```

`engine2` has lots of sources that *are based on* `Handle`s. That is,
they implement the data source API for data that is itself retrieved
through `engine2`.

Here's the trick at the heart of `ZipSource`:

```python
class ZipSource(DerivedSource):

    # ...

    def _generate_state(self, sm):
        with self.handle.follow(sm).make_path() as r:
            with ZipFile(str(r)) as zp:
                yield zp
```

Given a handle that points at an object, we follow that handle, we download the
object's content to a file, and we open a `ZipFile` that points to that file --
and suddenly `engine2` can explore Zip files in exactly the same way that it
explores our toy filesystem.

Because all of the JSON-handling code gets contributed to central registries,
we can serialise and deserialise this `ZipSource` as well, even though it's
based on a `Handle` defined outside of the `engine2` core:

```python
>>> zs = ZipSource(handle)
>>> zs.to_json_object()
{'type': 'zip', 'handle': {'type': 'toy', 'source': {'type': 'toy',
'username': 'alec', 'password': 'secretpassword'}, 'path':
'/home/alec/hello.zip'}}
>>> zs2 == Source.from_json_object(zs.to_json_object())
>>> zs == zs2
True
>>> [h.relative_path for h in zs2.handles(sm)]
['hello.txt']
```


# Using the `url_explorer` demo

This is a small demo script which explorers a source, created from a supplied
`url`, and prints the found handles.

The two most common `url`-types would be `file:abspath to directory` or
`http://example.com`.

See `src/os2datascanner/engine2/demo/url_explorer.py`
