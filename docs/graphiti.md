# What is Graphiti?

`graphiti` is a utility for building complex URLs for interacting with
the Microsoft Graph API.

The idea is to have a builder object with an API in the style of an ORM
that one can pass down and modify to ones hearts contempt.

The code currently lives in `engine2/models/msgraph/graphiti`.

## How do I use `graphiti`?

`graphiti` uses types and recursion for modelling which easily allows 
for building long, complicated URLs. 

### A simple example

Say you want to access all the files in Microsoft OneDrive for a given user.
Let's call this user Bob. Bob's principal username is his email: `bob@graph.microsoft.com`
(in a Microsoft Graph context). 

Building a URL for retrieving all of Bob's files in OneDrive with `graphiti` looks like this:

```python
from os2datascanner.engine2.model.msgraph.graphiti.builder import MSGraphURLBuilder

builder = MSGraphURLBuilder()  # Instantiate a builder object.

url = builder.v1().users('bob@graph.microsoft.com').files()  # Add the v1.0, users and files endpoints.

url_as_string = url.build()  # --> https://graph.microsoft.com/v1.0/users/bob@graph.microsoft.com/files
```

Note that every endpoint function (like `.v1()` and `.files()` in the example above)
on the builder object returns a new node object allowing you to chain as many nodes
as you like. It essentially acts like an immutable, stack-like data structure.

If you change you mind about a node, the `.parent()` method returns a reference to 
the previous endpoint. With this operation, you pop off an endpoint of the stack
of URL endpoints, so to speak. Maybe you didn't want Bob's files. You just wanted
information about Bob's profile:

```python
from os2datascanner.engine2.model.msgraph.graphiti.builder import MSGraphURLBuilder

builder = MSGraphURLBuilder()  # Instantiate a builder object.

url_to_files = builder.v1().users('bob@graph.microsoft.com').files()  # Add the v1.0, users and files endpoints.

url_to_bob = url_to_files.parent()  # Remove '/files' --> https://graph.microsoft.com/v1.0/users/bob@graph.microsoft.com
```

### A more complex example with OData Query Parameters

According to the Microsoft Graph [Documentation](https://learn.microsoft.com/en-us/graph/query-parameters?tabs=http),
the Graph API supports system query options that are compatible with the
[OData v4 query language](https://docs.oasis-open.org/odata/odata/v4.0/errata03/os/complete/part2-url-conventions/odata-v4.0-errata03-os-part2-url-conventions-complete.html#_Toc453752356).

Of course, `graphiti` provides some utilities for manipulating these too.
Perhaps, we want to modify to URL to query Bob's OneDrive files with some OData parameters
for getting only the first five files as `.xml`.
The `ODataQueryBuilder` class is just the thing for this task:

```python
from os2datascanner.engine2.model.msgraph.graphiti.builder import MSGraphURLBuilder
from os2datascanner.engine2.model.msgraph.graphiti.query_parameters import ODataQueryBuilder

builder = MSGraphURLBuilder()  # Instantiate a URL builder object.

url = builder.v1().users('bob@graph.microsoft.com').files()  # Add the v1.0, users and files endpoints.
odata = ODataQueryBuilder()  # Instantiate a OData builder object.
params = odata.top(5).format('xml')

# Below returns 'https://graph.microsoft.com/v1.0/users/bob@graph.microsoft.com/files?$top=5&$format=xml'
url_as_string = params.build(url)
```

Note that the `build()`-method on `ODataQueryBuilder` wraps the graph node object, not the other way around.
This is done under the assumption that query parameters are specific to the context of the endpoint,
that a node object carries information about. In other words, not all query parameters are relevant/
interesting for all endpoints.
