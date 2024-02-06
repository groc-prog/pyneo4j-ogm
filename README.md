# Pyneo4j-OGM

[![PyPI](https://img.shields.io/pypi/v/pyneo4j-ogm?style=flat-square)](https://pypi.org/project/pyneo4j-ogm/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/pyneo4j-ogm?style=flat-square)](https://pypi.org/project/pyneo4j-ogm/)
[![PyPI - License](https://img.shields.io/pypi/l/pyneo4j-ogm?style=flat-square)](https://pypi.org/project/pyneo4j-ogm/)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/pyneo4j-ogm?style=flat-square)](https://pypi.org/project/pyneo4j-ogm/)

`pyneo4j-ogm` is a asynchronous `Object-Graph-Mapper` for [`Neo4j 5+`](https://neo4j.com/docs/) and [`Python 3.10+`](https://www.python.org/). It is inspired by [`beanie`](https://github.com/roman-right/beanie) and build on top of proven technologies like [`Pydantic 1.10+ and 2+`](https://docs.pydantic.dev/latest/) and the [`Neo4j Python Driver`](https://neo4j.com/docs/api/python-driver/current/index.html). It saves you from writing ever-repeating boilerplate queries and allows you to focus on the `stuff that actually matters`. It is designed to be simple and easy to use, but also flexible and powerful.

## 🎯 Features <a name="features"></a>

- [x] **Simple and easy to use**: pyneo4j-ogm is designed to be `simple and easy to use`, while also providing a solid foundation for some more `advanced use-cases`.
- [x] **Flexible and powerful**: pyneo4j-ogm is flexible and powerful. It allows you to do all sorts of things with your data, from `simple CRUD` operations to `complex queries`.
- [x] **Fully asynchronous**: pyneo4j-ogm is `fully asynchronous` and uses the `Neo4j Python Driver` under the hood.
- [x] **Supports Neo4j 5+**: pyneo4j-ogm supports `Neo4j 5+` and is tested against the latest version of Neo4j.
- [x] **Fully typed**: pyneo4j-ogm is `fully typed` out of the box.
- [x] **Powered by Pydantic**: pyneo4j-ogm is powered by `Pydantic` and uses it's powerful validation and serialization features under the hood.

## 📦 Installation <a name="installation"></a>

Using [`pip`](https://pip.pypa.io/en/stable/):

```bash
pip install pyneo4j-ogm
```

or when using [`Poetry`](https://python-poetry.org/):

```bash
poetry add pyneo4j-ogm
```

## 🚀 Quickstart <a name="quickstart"></a>

Before we can jump right in, we have to take care of some things:

- We need to define our models which will represent our nodes and relationships.
- We need to initialize a `Pyneo4jClient` instance that will be used to interact with the database.

So let's start with the first one. We are going to define a few models that will represent our `nodes and relationships` inside the graph. For this example, we will look at `Developers` and their `Coffee` consumption:

```python
from pyneo4j_ogm import (
    NodeModel,
    RelationshipModel,
    RelationshipProperty,
    RelationshipPropertyCardinality,
    RelationshipPropertyDirection,
    WithOptions,
)
from pydantic import Field
from uuid import UUID, uuid4


class Developer(NodeModel):
  """
  This class represents a `Developer` node inside the graph. All interaction
  with nodes of this type will be handled by this class.
  """
  uid: WithOptions(UUID, unique=True) = Field(default_factory=uuid4)
  name: str
  age: int

  coffee: RelationshipProperty["Coffee", "Consumed"] = RelationshipProperty(
    target_model="Coffee",
    relationship_model="Consumed",
    direction=RelationshipPropertyDirection.OUTGOING,
    cardinality=RelationshipPropertyCardinality.ZERO_OR_MORE,
    allow_multiple=True,
  )

  class Settings:
    # Hooks are available for all methods that interact with the database.
    post_hooks = {
      "coffee.connect": lambda self, *args, **kwargs: print(f"{self.name} chugged another one!")
    }


class Coffee(NodeModel):
  """
  This class represents a node with the labels `Beverage` and `Hot`. Notice
  that the labels of this model are explicitly defined in the `Settings` class.
  """
  flavor: str
  sugar: bool
  milk: bool

  developers: RelationshipProperty["Developer", "Consumed"] = RelationshipProperty(
    target_model=Developer,
    relationship_model="Consumed",
    direction=RelationshipPropertyDirection.INCOMING,
    cardinality=RelationshipPropertyCardinality.ZERO_OR_MORE,
    allow_multiple=True,
  )

  class Settings:
    labels = {"Beverage", "Hot"}

class Consumed(RelationshipModel):
  """
  Unlike the models above, this class represents a relationship between two
  nodes. In this case, it represents the relationship between the `Developer`
  and `Coffee` models. Like with node-models, the `Settings` class allows us to
  define some settings for this relationship.

  Note that the relationship itself does not define it's start- and end-nodes,
  making it reusable for other models as well.
  """
  liked: bool

  class Settings:
    type = "CHUGGED"
```

The models above are pretty straight forward. They are basically just `Pydantic` models with some sugar on top, though there are some special things to note:

- We are defining some model-specific settings inside the `Settings` class. These settings are used by `pyneo4j-ogm` to determine how to handle the model. For example, the `labels` setting of the `Coffee` model tells `pyneo4j-ogm` that this model should have the labels `Beverage` and `Hot` inside the graph. The `type` setting of the `Consumed` model tells `pyneo4j-ogm` that this relationship should have the type `CHUGGED` inside the graph.
- We are defining a `post_hook` for the `coffee` relationship of the `Developer` model. This hook will be called whenever a `Coffee` node is connected to a `Developer` node via the `coffee` relationship-property.
- We are defining a `uniqueness constraint` for the `uid` field of the `Developer` model. This will create a uniqueness constraint inside the graph for the `uid` field of the `Developer` model. This means that there can only be one `Developer` node with a specific `uid` inside the graph.

Now that we have our models defined, we can initialize a `Pyneo4jClient` instance that will be used to interact with the database. The client will handle most of the heavy lifting for us and our models, so let's initialize a new one and connect to the database:

```python
from pyneo4j_ogm import Pyneo4jClient

async def main():
  # We initialize a new `Pyneo4jClient` instance and connect to the database.
  client = Pyneo4jClient()
  await client.connect(uri="<connection-uri-to-database>", auth=("<username>", "<password>"))

  # To use our models for running queries later on, we have to register
  # them with the client.
  # **Note**: You only have to register the models that you want to use
  # for queries and you can even skip this step if you want to use the
  # `Pyneo4jClient` instance for running raw queries.
  await client.register_models([Developer, Coffee, Consumed])
```

Now we are ready to do some fun stuff with our models! For the sake of this [`quickstart guide`](#quickstart) we are going to keep it nice and simple, since a full-blown example would become way to long. So let's create a new `Developer` and some `Coffee` and give our developer something to drink!

```python
# Imagine your models have been defined above...

async def main():
  # And your client has been initialized and connected to the database...

  # We create a new `Developer` node and the `Coffee` he is going to drink.
  john = Developer(name="John", age=25)
  await john.create()

  cappuccino = Coffee(flavor="Cappuccino", milk=True, sugar=False)
  await cappuccino.create()

  # Here we create a new relationship between `john` and his `cappuccino`.
  # Additionally, we set the `liked` property of the relationship to `True`.
  await john.coffee.connect(cappuccino, {"liked": True}) # Will print `John chugged another one!`
```

### Full quickstart example

Now all you have to do is to start a Neo4j instance somewhere and get to work! We can put all of the steps together and end up with something like the code below:

```python
import asyncio
from pyneo4j_ogm import (
    NodeModel,
    Pyneo4jClient,
    RelationshipModel,
    RelationshipProperty,
    RelationshipPropertyCardinality,
    RelationshipPropertyDirection,
    WithOptions,
)
from pydantic import Field
from uuid import UUID, uuid4

class Developer(NodeModel):
  """
  This class represents a `Developer` node inside the graph. All interaction
  with nodes of this type will be handled by this class.
  """
  uid: WithOptions(UUID, unique=True) = Field(default_factory=uuid4)
  name: str
  age: int

  coffee: RelationshipProperty["Coffee", "Consumed"] = RelationshipProperty(
    target_model="Coffee",
    relationship_model="Consumed",
    direction=RelationshipPropertyDirection.OUTGOING,
    cardinality=RelationshipPropertyCardinality.ZERO_OR_MORE,
    allow_multiple=True,
  )

  class Settings:
    # Hooks are available for all methods that interact with the database.
    post_hooks = {
      "coffee.connect": lambda self, *args, **kwargs: print(f"{self.name} chugged another one!")
    }


class Coffee(NodeModel):
  """
  This class represents a node with the labels `Beverage` and `Hot`. Notice
  that the labels of this model are explicitly defined in the `Settings` class.
  """
  flavor: str
  sugar: bool
  milk: bool

  developers: RelationshipProperty["Developer", "Consumed"] = RelationshipProperty(
    target_model=Developer,
    relationship_model="Consumed",
    direction=RelationshipPropertyDirection.INCOMING,
    cardinality=RelationshipPropertyCardinality.ZERO_OR_MORE,
    allow_multiple=True,
  )

  class Settings:
    labels = {"Beverage", "Hot"}

class Consumed(RelationshipModel):
  """
  Unlike the models above, this class represents a relationship between two
  nodes. In this case, it represents the relationship between the `Developer`
  and `Coffee` models. Like with node-models, the `Settings` class allows us to
  define some settings for this relationship.

  Note that the relationship itself does not define it's start- and end-nodes,
  making it reusable for other models as well.
  """
  liked: bool

  class Settings:
    type = "CHUGGED"


async def main():
  # We initialize a new `Pyneo4jClient` instance and connect to the database.
  client = Pyneo4jClient()
  await client.connect(uri="<connection-uri-to-database>", auth=("<username>", "<password>"))

  # To use our models for running queries later on, we have to register
  # them with the client.
  # **Note**: You only have to register the models that you want to use
  # for queries and you can even skip this step if you want to use the
  # `Pyneo4jClient` instance for running raw queries.
  await client.register_models([Developer, Coffee, Consumed])

  # We create a new `Developer` node and the `Coffee` he is going to drink.
  john = Developer(name="John", age=25)
  await john.create()

  cappuccino = Coffee(flavor="Cappuccino", milk=True, sugar=False)
  await cappuccino.create()

  # Here we create a new relationship between `john` and his `cappuccino`.
  # Additionally, we set the `liked` property of the relationship to `True`.
  await john.coffee.connect(cappuccino, {"liked": True}) # Will print `John chugged another one!`

  # Be a good boy and close your connections after you are done.
  await client.close()

asyncio.run(main())
```

> **Note**: This script should run `as is`. You must change the `uri` and `auth` parameters in the `connect()` method call to match the one's you need and have a running Neo4j instance before starting the script.

This just scratches the surface of what `pyneo4j-ogm` can do. If you want to learn more about the library, you can check out the full [`Documentation`](#documentation).

## 📚 Documentation <a name="documentation"></a>

In the following we are going to take a closer look at the different parts of `pyneo4j-ogm` and how to use them. We will cover everything pyneo4j-ogm has to offer, from the `Pyneo4jClient` to the `NodeModel` and `RelationshipModel` classes all the way to the `Query filters` and `Auto-fetching relationship-properties`.

### Table of contents

- [Pyneo4j-OGM](#pyneo4j-ogm)
  - [🎯 Features ](#-features-)
  - [📦 Installation ](#-installation-)
  - [🚀 Quickstart ](#-quickstart-)
    - [Full quickstart example](#full-quickstart-example)
  - [📚 Documentation ](#-documentation-)
    - [Table of contents](#table-of-contents)
    - [Basic concepts ](#basic-concepts-)
      - [Pydantic and supported versions/features ](#pydantic-and-supported-versionsfeatures-)
    - [Pyneo4jClient ](#pyneo4jclient-)
      - [Connecting to the database ](#connecting-to-the-database-)
      - [Closing an existing connection ](#closing-an-existing-connection-)
      - [Registering models ](#registering-models-)
      - [Executing Cypher queries ](#executing-cypher-queries-)
      - [Batching cypher queries ](#batching-cypher-queries-)
      - [Using bookmarks (Enterprise Edition only) ](#using-bookmarks-enterprise-edition-only-)
      - [Manual indexing and constraints ](#manual-indexing-and-constraints-)
      - [Client utilities ](#client-utilities-)
    - [Models ](#models-)
      - [Indexes, constraints and properties ](#indexes-constraints-and-properties-)
      - [Reserved properties ](#reserved-properties-)
      - [Configuration settings ](#configuration-settings-)
        - [NodeModel configuration ](#nodemodel-configuration-)
        - [RelationshipModel configuration ](#relationshipmodel-configuration-)
      - [Available methods ](#available-methods-)
        - [Instance.update() ](#instanceupdate-)
        - [Instance.delete() ](#instancedelete-)
        - [Instance.refresh() ](#instancerefresh-)
        - [Model.find\_one() ](#modelfind_one-)
          - [Projections ](#projections-)
          - [Auto-fetching nodes ](#auto-fetching-nodes-)
          - [Raise on empty result ](#raise-on-empty-result-)
        - [Model.find\_many() ](#modelfind_many-)
          - [Filters ](#filters-)
          - [Projections ](#projections--1)
          - [Query options ](#query-options-)
          - [Auto-fetching nodes ](#auto-fetching-nodes--1)
        - [Model.update\_one() ](#modelupdate_one-)
          - [Returning the updated entity ](#returning-the-updated-entity-)
          - [Raise on empty result ](#raise-on-empty-result--1)
        - [Model.update\_many() ](#modelupdate_many-)
          - [Filters ](#filters--1)
          - [Returning the updated entity ](#returning-the-updated-entity--1)
        - [Model.delete\_one() ](#modeldelete_one-)
          - [Raise on empty result ](#raise-on-empty-result--2)
        - [Model.delete\_many() ](#modeldelete_many-)
          - [Filters ](#filters--2)
        - [Model.count() ](#modelcount-)
          - [Filters ](#filters--3)
        - [NodeModelInstance.create() ](#nodemodelinstancecreate-)
        - [NodeModelInstance.find\_connected\_nodes() ](#nodemodelinstancefind_connected_nodes-)
          - [Projections ](#projections--2)
          - [Query options ](#query-options--1)
          - [Auto-fetching nodes ](#auto-fetching-nodes--2)
        - [RelationshipModelInstance.start\_node() ](#relationshipmodelinstancestart_node-)
        - [RelationshipModelInstance.end\_node() ](#relationshipmodelinstanceend_node-)
      - [Serializing models ](#serializing-models-)
      - [Hooks ](#hooks-)
        - [Pre-hooks ](#pre-hooks-)
        - [Post-hooks ](#post-hooks-)
      - [Model settings ](#model-settings-)
    - [Relationship-properties ](#relationship-properties-)
      - [Available methods ](#available-methods--1)
        - [RelationshipProperty.relationships() ](#relationshippropertyrelationships-)
          - [Filters ](#filters--4)
          - [Projections ](#projections--3)
          - [Query options ](#query-options--2)
        - [RelationshipProperty.connect() ](#relationshippropertyconnect-)
        - [RelationshipProperty.disconnect() ](#relationshippropertydisconnect-)
          - [Raise on empty result ](#raise-on-empty-result--3)
        - [RelationshipProperty.disconnect\_all() ](#relationshippropertydisconnect_all-)
        - [RelationshipProperty.replace() ](#relationshippropertyreplace-)
        - [RelationshipProperty.find\_connected\_nodes() ](#relationshippropertyfind_connected_nodes-)
          - [Filters ](#filters--5)
          - [Projections ](#projections--4)
          - [Query options ](#query-options--3)
          - [Auto-fetching nodes ](#auto-fetching-nodes--3)
      - [Hooks with relationship properties ](#hooks-with-relationship-properties-)
    - [Queries ](#queries-)
      - [Filtering queries ](#filtering-queries-)
        - [Comparison operators ](#comparison-operators-)
        - [String operators ](#string-operators-)
        - [List operators ](#list-operators-)
        - [Logical operators ](#logical-operators-)
        - [Element operators ](#element-operators-)
        - [Pattern matching ](#pattern-matching-)
        - [Multi-hop filters ](#multi-hop-filters-)
      - [Projections ](#projections--5)
      - [Query options ](#query-options--4)
      - [Auto-fetching relationship-properties ](#auto-fetching-relationship-properties-)
    - [Logging ](#logging-)
    - [Running the test suite ](#running-the-test-suite-)

### Basic concepts <a name="basic-concepts"></a>

As you might have guessed by now, `pyneo4j-ogm` is a library that allows you to interact with a Neo4j database using Python. It is designed to make your life as simple as possible while also providing a solid foundation for some more advanced use-cases.

The basic concept boils down to the following:

- You define your models that represent your nodes and relationships inside the graph.
- You use these models to do all sorts of things with your data.

Of course, there is a lot more to it than that, but this is the basic idea. So let's take a closer look at the different parts of `pyneo4j-ogm` and how to use them.

> **Note:** All of the examples in this documentation assume that you have already connected to a database and registered your models with the client like shown in the [`quickstart guide`](#quickstart). The models used in the following examples will build upon the ones defined there. If you are new to [`Neo4j`](https://neo4j.com/docs/) or [`Cypher`](https://neo4j.com/docs/cypher-manual/current/) in general, you should get a basic understanding of how to use them before continuing.

#### Pydantic and supported versions/features <a name="pydantic-supported-version-features"></a>

`pyneo4j-ogm` currently supports both [`Pydantic V1`](https://docs.pydantic.dev/1.10/) and the latest version of [`Pydantic V2`](https://docs.pydantic.dev/2.5/). Most of the core features are pretty well supported (meaning most model methods and schema generation) for V2 and V1.

> **Note:** For schema generation to work with Pydantic V1, `Model.update_forward_refs() has to be called` in order for Pydantic to be able to generate the schemas for `RelationshipProperty` fields.

### Pyneo4jClient <a name="pyneo4jclient"></a>

This is where all the magic happens! The `Pyneo4jClient` is the main entry point for interacting with the database. It handles all the heavy lifting for you and your models, so you can focus on the stuff that actually matters. Since it is the brains of the operation, we have to initialize it before we can do anything else.

#### Connecting to the database <a name="connecting-to-the-database"></a>

Before you can run any queries, you have to connect to a database. This is done by calling the `connect()` method of the `Pyneo4jClient` instance. The `connect()` method takes a few arguments:

- `uri`: The connection URI to the database.
- `skip_constraints`: Whether the client should skip creating any constraints defined on models when registering them. Defaults to `False`.
- `skip_indexes`: Whether the client should skip creating any indexes defined on models when registering them. Defaults to `False`.
- `*args`: Additional arguments that are passed directly to Neo4j's `AsyncDriver.driver()` method.
- `**kwargs`: Additional keyword arguments that are passed directly to Neo4j's `AsyncDriver.driver()` method.

The `connect()` method returns the client instance itself, so you can chain it right after the instantiation of the class. Here is an example of how to connect to a database:

```python
from pyneo4j_ogm import Pyneo4jClient

client = Pyneo4jClient()
await client.connect(uri="<connection-uri-to-database>", auth=("<username>", "<password>"), max_connection_pool_size=10, ...)

# Or chained right after the instantiation of the class
client = await Pyneo4jClient().connect(uri="<connection-uri-to-database>", auth=("<username>", "<password>"), max_connection_pool_size=10, ...)
```

After connecting the client, you will be able to run any cypher queries against the database. Should you try to run a query without connecting to a database first, you will get a `NotConnectedToDatabase` exception.

#### Closing an existing connection <a name="closing-an-existing-connection"></a>

Once you are done working with a database and the client is no longer needed, you can close the connection to it by calling the `close()` method on the client instance. This will close the connection to the database and free up any resources used by the client. Remember to always close your connections when you are done with them, otherwise Santa won't bring you any presents!

```python
# Do some heavy-duty work...

# Finally done, so we close the connection to the database.
await client.close()
```

Once you closed the client, it will be seen as `disconnected` and if you try to run any further queries with it, you will get a `NotConnectedToDatabase` exception.

#### Registering models <a name="registering-models"></a>

As mentioned before, the basic concept is to work with models which reflect the nodes and relationships inside the graph. In order to work with these models, you have to register them with the client. You can do this by calling the `register_models()` method on the client and passing in your models as a list. Let's take a look at an example:

```python
# Create a new client instance and connect ...

await client.register_models([Developer, Coffee, Consumed])
```

This is a crucial step, because if you don't register your models with the client, you won't be able to work with them in any way. Should you try to work with a model that has not been registered, you will get a `UnregisteredModel` exception. This exception also gets raised if a database model defines a relationship-property with other (unregistered) models as a target or relationship model and then runs a query with said relationship-property. For more information about relationship-properties, see the [`Relationship-properties`](#relationship-properties) section.

If you have defined any indexes or constraints on your models, they will be created automatically when registering them. You can prevent this behavior by passing `skip_constraints=True` or `skip_indexes=True` to the `connect()` method. If you do this, you will have to create the indexes and constraints yourself.

If you don't register your models with the client, you will still be able to run cypher queries directly with the client, but you will `lose automatic model resolution` from queries. This means that, instead of resolved models, the raw Neo4j query results are returned.

#### Executing Cypher queries <a name="executing-cypher-queries"></a>

Node- and RelationshipModels provide many methods for commonly used cypher queries, but sometimes you might want to execute a custom cypher with more complex logic. For this purpose, the client instance provides a `cypher()` method that allows you to execute custom cypher queries. The `cypher()` method takes three arguments:

- `query`: The cypher query to execute.
- `parameters`: A dictionary containing the parameters to pass to the query.
- `resolve_models`: Whether the client should try to resolve the models from the query results. Defaults to `True`.

This method will always return a tuple containing a list of results and a list of variables returned by the query. Internally, the client uses the `.values()` method of the Neo4j driver to get the results of the query.

> **Note:** If no models have been registered with the client and resolve_models is set to True, the client will not raise any exceptions but rather return the raw query results.

Here is an example of how to execute a custom cypher query:

```python
results, meta = await client.cypher(
  query="CREATE (d:Developer {uid: '553ac2c9-7b2d-404e-8271-40426ae80de0', name: 'John', age: 25}) RETURN d.name as developer_name, d.age",
  parameters={"name": "John Doe"},
  resolve_models=False,  # Explicitly disable model resolution
)

print(results)  # [["John", 25]]
print(meta)  # ["developer_name", "d.age"]
```

#### Batching cypher queries <a name="batching-cypher-queries"></a>

Since Neo4j is ACID compliant, it is possible to batch multiple cypher queries into a single transaction. This can be useful if you want to execute multiple queries at once and make sure that either all of them succeed or none of them do. The client provides a `batch()` method that allows you to batch multiple cypher queries into a single transaction. The `batch()` method has to be called with a asynchronous context manager like in the following example:

```python
async with client.batch():
  # All queries executed inside the context manager will be batched into a single transaction
  # and executed once the context manager exits. If any of the queries fail, the whole transaction
  # will be rolled back.
  await client.cypher(
    query="CREATE (d:Developer {uid: $uid, name: $name, age: $age})",
    parameters={"uid": "553ac2c9-7b2d-404e-8271-40426ae80de0", "name": "John Doe", "age": 25},
  )
  await client.cypher(
    query="CREATE (c:Coffee {flavour: $flavour, milk: $milk, sugar: $sugar})",
    parameters={"flavour": "Espresso", "milk": False, "sugar": False},
  )

  # Model queries also can be batched together without any extra work!
  coffee = await Coffee(flavour="Americano", milk=False, sugar=False).create()
```

You can batch anything that runs a query, regardless of whether it is a raw cypher query, a model query or a relationship-property query. If any of the queries fail, the whole transaction will be rolled back and an exception will be raised.

#### Using bookmarks (Enterprise Edition only) <a name="using-bookmarks"></a>

If you are using the Enterprise Edition of Neo4j, you can use bookmarks to keep track of the last transaction that has been committed. This allows you to resume a transaction after a failure or a restart of the database. The client provides a `last_bookmarks` property that allows you to get the bookmarks from the last session. These bookmarks can be used in combination with the `use_bookmarks()` method. Like the `batch()` method, the `use_bookmarks()` method has to be called with a context manager. All queries run inside the context manager will use the bookmarks passed to the `use_bookmarks()` method. Here is an example of how to use bookmarks:

```python
# Create a new node and get the bookmarks from the last session
await client.cypher("CREATE (d:Developer {name: 'John Doe', age: 25})")
bookmarks = client.last_bookmarks

# Create another node, but this time don't get the bookmark
# When we use the bookmarks from the last session, this node will not be visible
await client.cypher("CREATE (c:Coffee {flavour: 'Espresso', milk: False, sugar: False})")

with client.use_bookmarks(bookmarks=bookmarks):
  # All queries executed inside the context manager will use the bookmarks
  # passed to the `use_bookmarks()` method.

  # Here we will only see the node created in the first query
  results, meta = await client.cypher("MATCH (n) RETURN n")

  # Model queries also can be batched together without any extra work!
  # This will return no results, since the coffee node was created after
  # the bookmarks were taken.
  coffee = await Coffee.find_many()
  print(coffee)  # []
```

#### Manual indexing and constraints <a name="manual-indexing-and-constraints"></a>

By default, the client will automatically create any indexes and constraints defined on models when registering them. If you want to disable this behavior, you can do so by passing the `skip_indexes` and `skip_constraints` arguments to the `connect()` method when connecting your client to a database.

If you want to create custom indexes and constraints, or want to add additional indexes/constraints later on (which should probably be done on the models themselves), you can do so by calling the `create_lookup_index()`, `create_range_index`, `create_text_index`, `create_point_index` and `create_uniqueness_constraint()` methods on the client.

First, let's take a look at how to create a custom index in the database. The `create_range_index`, `create_text_index` and `create_point_index` methods take a few arguments:

- `name`: The name of the index to create (Make sure this is unique!).
- `entity_type`: The entity type the index is created for. Can be either **EntityType.NODE** or **EntityType.RELATIONSHIP**.
- `properties`: A list of properties to create the index for.
- `labels_or_type`: The node labels or relationship type the index is created for.

The `create_lookup_index()` takes the same arguments, except for the `labels_or_type` and `properties` arguments.

The `create_uniqueness_constraint()` method also takes similar arguments.

- `name`: The name of the constraint to create.
- `entity_type`: The entity type the constraint is created for. Can be either **EntityType.NODE** or **EntityType.RELATIONSHIP**.
- `properties`: A list of properties to create the constraint for.
- `labels_or_type`: The node labels or relationship type the constraint is created for.

Here is an example of how to use the methods:

```python
# Creates a `RANGE` index for a `Coffee's` `sugar` and `flavour` properties
await client.create_range_index("hot_beverage_index", EntityType.NODE, ["sugar", "flavour"], ["Beverage", "Hot"])

# Creates a UNIQUENESS constraint for a `Developer's` `uid` property
await client.create_uniqueness_constraint("developer_constraint", EntityType.NODE, ["uid"], ["Developer"])
```

#### Client utilities <a name="client-utilities"></a>

The database client also provides a few utility methods and properties that can be useful when writing automated scripts or tests. These methods are:

- `is_connected()`: Returns whether the client is currently connected to a database.
- `drop_nodes()`: Drops all nodes from the database.
- `drop_constraints()`: Drops all constraints from the database.
- `drop_indexes()`: Drops all indexes from the database.

### Models <a name="models"></a>

As shown in the [`quickstart guide`](#quickstart), models are the main building blocks of `pyneo4j-ogm`. They represent the nodes and relationships inside the graph and provide a lot of useful methods for interacting with them.

A core mechanic of `pyneo4j-ogm` is serialization and deserialization of models. Every model method uses this mechanic under the hood to convert the models to and from the format used by the Neo4j driver.

> **Note:** The serialization and deserialization of models is handled automatically by `pyneo4j-ogm` and you don't have to worry about it.

This is necessary because the Neo4j driver can only handle certain data types, which means models with custom or complex data types have to be serialized before they can be saved to the database. Additionally, Neo4j itself does not support nested data structures. To combat this, nested dictionaries and Pydantic models are serialized to a JSON string before being saved to the database. But this causes some new issues, especially when trying to use dictionaries or Pydantic models as properties on a model. Since `pyneo4j-ogm` can't know whether a dictionary or Pydantic model is supposed to be serialized or not, it will just not accept lists with dictionaries or Pydantic models as properties on a model.

Filters for nested properties are also not supported, since they are stored as strings inside the database. This means that you can't use filters on nested properties when running queries with models. If you want to use filters on nested properties, you will to run a complex regular expression query.

#### Indexes, constraints and properties <a name="indexes-constraints-and-properties"></a>

Since `pyneo4j-ogm` is built on top of `Pydantic`, all of the features provided by `Pydantic` are available to you. This includes defining `properties` on your models. For more information about these features, please refer to the [`Pydantic documentation`](https://docs.pydantic.dev/latest/concepts/json_schema/#schema-customization).

On the other hand, `indexes and constraints` are handled solely by `pyneo4j-ogm`. You can define indexes and constraints on your models by using the `WithOptions` method wrapped around the type of the property. You can pass the following arguments to the `WithOptions` method:

- `property_type`: The datatype of the property. Must be a valid `Pydantic` type.
- `range_index`: Whether to create a range index on the property. Defaults to `False`.
- `text_index`: Whether to create a text index on the property. Defaults to `False`.
- `point_index`: Whether to create a point index on the property. Defaults to `False`.
- `unique`: Whether to create a uniqueness constraint on the property. Defaults to `False`.

> **Note:** Using the `WithOptions` without any index or constraint options will behave just like it was never there (but in that case you should probably just remove it).

```python
from pyneo4j_ogm import NodeModel, WithOptions
from pydantic import Field
from uuid import UUID, uuid4

class Developer(NodeModel):
  """
  A model representing a developer node in the graph.
  """
  # Using the `WithOptions` method on the type, we can still use all of the features provided by
  # `Pydantic` while also defining indexes and constraints on the property.
  uid: WithOptions(UUID, unique=True) = Field(default_factory=uuid4)
  name: WithOptions(str, text_index=True)
  # Has no effect, since no index or constraint options are passed
  age: WithOptions(int)
```

#### Reserved properties <a name="reserved-properties"></a>

Node- and RelationshipModels have a few pre-defined properties which reflect the entity inside the graph and are used internally in queries. These properties are:

- `element_id`: The element id of the entity inside the graph. This property is used internally to identify the entity inside the graph.
- `id`: The id of the entity inside the graph.
- `modified_properties`: A set of properties which have been modified on the

The `RelationshipModel` class has some additional properties:

- `start_node_element_id`: The element id of the start node of the relationship.
- `start_node_id`: The ID of the start node of the relationship.
- `end_node_element_id`: The element id of the end node of the relationship.
- `end_node_id`: The ID of the end node of the relationship.

#### Configuration settings <a name="configuration-settings"></a>

 Both `NodeModel` and `RelationshipModel` provide a few properties that can be configured. In this section we are going to take a closer look at how to configure your models and what options are available to you.

Model configuration is done by defining a inner `Settings` class inside the model itself. The properties of this class control how the model is handled by `pyneo4j-ogm`:

```python
class Coffee(NodeModel):
  flavour: str
  sugar: bool
  milk: bool

  class Settings:
    # This is the place where the magic happens!
```

There also is a special type of property called `RelationshipProperty`. This property can be used to define relationships between models. For more information about this property, see the [`Relationship-properties`](#relationship-properties) section.

##### NodeModel configuration <a name="node-model-configuration"></a>

The `Settings` class of a `NodeModel` provides the following properties:

| Setting name          | Type                          | Description                                                                                                                                                                                                                                                                                                                              |
| --------------------- | ----------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `pre_hooks`           | **Dict[str, List[Callable]]** | A dictionary where the key is the name of the method for which to register the hook and the value is a list of hook functions. The hook function can be synchronous or asynchronous. All hook functions receive the exact same arguments as the method they are registered for and the current model instance as the first argument. Defaults to `{}`. |
| `post_hooks`          | **Dict[str, List[Callable]]** | Same as **pre_hooks**, but the hook functions are executed after the method they are registered for. Additionally, the result of the method is passed to the hook as the second argument. Defaults to `{}`.                                                                                                                              |
| `labels`           | **Set[str]** | A set of labels to use for the node. If no labels are defined, the name of the model will be used as the label. Defaults to the `model name split by it's words`.                                                                                                                                                                                                                            |
| `auto_fetch_nodes` | **bool**     | Whether to automatically fetch nodes of defined relationship-properties when getting a model instance from the database. Auto-fetched nodes are available at the `instance.<relationship-property>.nodes` property. If no specific models are passed to a method when this setting is set to `True`, nodes from all defined relationship-properties are fetched. Defaults to `False`. |

> **Note:** Hooks can be defined for all methods that interact with the database. When defining a hook for a method on a relationship-property, you have to pass a string in the format `<relationship-property>.<method>` as the key. For example, if you want to define a hook for the `connect()` method of a relationship-property named `coffee`, you would have to pass `coffee.connect` as the key.

##### RelationshipModel configuration <a name="relationship-model-configuration"></a>

For RelationshipModels, the `labels` setting is not available, since relationships don't have labels in Neo4j. Instead, the `type` setting can be used to define the type of the relationship. If no type is defined, the name of the model name will be used as the type.

| Setting name          | Type                          | Description                                                                                                                                                                                                                                                                                                                              |
| --------------------- | ----------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `pre_hooks`           | **Dict[str, List[Callable]]** | A dictionary where the key is the name of the method for which to register the hook and the value is a list of hook functions. The hook function can be synchronous or asynchronous. All hook functions receive the exact same arguments as the method they are registered for and the current model instance as the first argument. Defaults to `{}`. |
| `post_hooks`          | **Dict[str, List[Callable]]** | Same as **pre_hooks**, but the hook functions are executed after the method they are registered for. Additionally, the result of the method is passed to the hook as the second argument. Defaults to `{}`.                                                                                                                              |
| `type`       | **str** | The type of the relationship to use. If no type is defined, the model name will be used as the type. Defaults to the `model name in all uppercase`. |

#### Available methods <a name="model-available-methods"></a>

Running cypher queries manually is nice, but code running them for you is even better. That's exactly what the model methods are for. They allow you to do all sorts of things with your models and the nodes and relationships they represent. In this section we are going to take a closer look at the different methods available to you.

But before we jump in, let's get one thing out of the way: All of the methods described in this section are `asynchronous` methods. This means that they have to be awaited when called. If you are new to asynchronous programming in Python, you should take a look at the [`asyncio documentation`](https://docs.python.org/3/library/asyncio.html) before continuing.

Additionally, the name of the heading for each method defines what type of model it is available on and whether it is a `class method` or an `instance method`.

- `Model.method()`: The `class method` is available on instances of both `NodeModel` and `RelationshipModel` classes.
- `Instance.method()`: The `instance method` is available on instances of both `NodeModel` and `RelationshipModel` classes.
- `<Type>Model.method()`: The `class method` is available on instances of the `<Type>Model` class.
- `<Type>ModelInstance.method()`: The `instance method` is available on instances of the `<Type>Model` class.

##### Instance.update() <a name="instance-update"></a>

The `update()` method can be used to sync the modified properties of a node or relationship-model with the corresponding entity inside the graph. All models also provide a property called `modified_properties` that contains a set of all properties that have been modified since the model was created, fetched or synced with the database. This property is used by the `update()` method to determine which properties to sync with the database.

```python
# In this context, the developer `john` has been created before and the `name` property has been
# not been changed since.

# Maybe we want to name him James instead?
john.name = "James"

print(john.modified_properties)  # {"name"}

# Will update the `name` property of the `john` node inside the graph
# And suddenly he is James!
await john.update()
```

##### Instance.delete() <a name="instance-delete"></a>

The `delete()` method can be used to delete the graph entity tied to the current model instance. Once deleted, the model instance will be marked as `destroyed` and any further operations on it will raise a `InstanceDestroyed` exception.

```python
# In this context, the developer `john` has been created before and is seen as `hydrated` (aka it
# has been saved to the database before).

# This will delete the `john` node inside the graph and mark your local instance as `destroyed`.
await john.delete()

await john.update()  # Raises `InstanceDestroyed` exception
```

##### Instance.refresh() <a name="instance-refresh"></a>

Syncs your local instance with the properties from the corresponding graph entity. ´This method can be useful if you want to make sure that your local instance is always up-to-date with the graph entity.

It is recommended to always call this method when importing a model instance from a dictionary (but does not have to be called necessarily, which in turn could cause a data inconsistency locally, so be careful when!).

```python
# Maybe we want to name him James instead?
john.name = "James"

# Oh no, don't take my `john` away!
await john.refresh()

print(john.name) # 'John'
```

##### Model.find_one() <a name="model-find-one"></a>

The `find_one()` method can be used to find a single node or relationship in the graph. If multiple results are matched, the first one is returned. This method returns a single instance/dictionary or `None` if no results were found.

This method takes a mandatory `filters` argument, which is used to filter the results. For more about filters, see the [`Filtering queries`](#query-filters) section.

```python
# Return the first encountered node where the name property equals `John`.
# This method always needs a filter to go with it!
john_or_nothing = await Developer.find_one({"name": "John"})

print(developer) # <Developer> or None
```

###### Projections <a name="model-find-one-projections"></a>

`Projections` can be used to only return specific parts of the model as a dictionary. This can help to reduce bandwidth or to just pre-filter the query results to a more suitable format. For more about projections, see [`Projections`](#query-projections)

```python
# Return a dictionary with the developers name at the `dev_name` key instead
# of a model instance.
developer = await Developer.find_one({"name": "John"}, {"dev_name": "name"})

print(developer) # {"dev_name": "John"}
```

###### Auto-fetching nodes <a name="model-find-one-auto-fetching-nodes"></a>

The `auto_fetch_nodes` and `auto_fetch_models` arguments can be used to automatically fetch all or selected nodes from defined relationship-properties when running the `find_one()` query. The pre-fetched nodes are available on their respective relationship-properties. For more about auto-fetching, see [`Auto-fetching relationship-properties`](#query-auto-fetching).

> **Note**: The `auto_fetch_nodes` and `auto_fetch_models` parameters are only available for classes which inherit from the `NodeModel` class.

```python
# Returns a developer instance with `instance.<property>.nodes` properties already fetched
developer = await Developer.find_one({"name": "John"}, auto_fetch_nodes=True)

print(developer.coffee.nodes) # [<Coffee>, <Coffee>, ...]
print(developer.other_property.nodes) # [<OtherModel>, <OtherModel>, ...]

# Returns a developer instance with only the `instance.coffee.nodes` property already fetched
developer = await Developer.find_one({"name": "John"}, auto_fetch_nodes=True, auto_fetch_models=[Coffee])

# Auto-fetch models can also be passed as strings
developer = await Developer.find_one({"name": "John"}, auto_fetch_nodes=True, auto_fetch_models=["Coffee"])

print(developer.coffee.nodes) # [<Coffee>, <Coffee>, ...]
print(developer.other_property.nodes) # []
```

###### Raise on empty result <a name="model-find-one-raise-on-empty-result"></a>

By default, the `find_one()` method will return `None` if no results were found. If you want to raise an exception instead, you can pass `raise_on_empty=True` to the method.

```python
# Raises a `NoResultFound` exception if no results were found
developer = await Developer.find_one({"name": "John"}, raise_on_empty=True)
```

##### Model.find_many() <a name="model-find-many"></a>

The `find_many()` method can be used to find multiple nodes or relationships in the graph. This method always returns a list of instances/dictionaries or an empty list if no results were found.

```python
# Returns ALL `Developer` nodes
developers = await Developer.find_many()

print(developers) # [<Developer>, <Developer>, <Developer>, ...]
```

###### Filters <a name="model-find-many-filters"></a>

Just like the `find_one()` method, the `find_many()` method also takes (optional) filters. For more about filters, see the [`Filtering queries`](#query-filters) section.

```python
# Returns all `Developer` nodes where the age property is greater than or
# equal to 21 and less than 45.
developers = await Developer.find_many({"age": {"$and": [{"$gte": 21}, {"$lt": 45}]}})

print(developers) # [<Developer>, <Developer>, <Developer>, ...]
```

###### Projections <a name="model-find-many-projections"></a>

`Projections` can be used to only return specific parts of the models as dictionaries. For more information about projections, see the [`Projections`](#query-projections) section.

```python
# Returns dictionaries with the developers name at the `dev_name` key instead
# of model instances
developers = await Developer.find_many({"name": "John"}, {"dev_name": "name"})

print(developers) # [{"dev_name": "John"}, {"dev_name": "John"}, ...]
```

###### Query options <a name="model-find-many-query-options"></a>

`Query options` can be used to define how results are returned from the query. They are provided via the `options` argument. For more about query options, see the [`Query options`](#query-options) section.

```python
# Skips the first 10 results and returns the next 20
developers = await Developer.find_many({"name": "John"}, options={"limit": 20, "skip": 10})

print(developers) # [<Developer>, <Developer>, ...] up to 20 results
```

###### Auto-fetching nodes <a name="model-find-many-auto-fetching-nodes"></a>

The `auto_fetch_nodes` and `auto_fetch_models` parameters can be used to automatically fetch all or selected nodes from defined relationship-properties when running the `find_many()` query. For more about auto-fetching, see [`Auto-fetching relationship-properties`](#query-auto-fetching).

> **Note**: The `auto_fetch_nodes` and `auto_fetch_models` parameters are only available for classes which inherit from the `NodeModel` class.

```python
# Returns developer instances with `instance.<property>.nodes` properties already fetched
developers = await Developer.find_many({"name": "John"}, auto_fetch_nodes=True)

print(developers[0].coffee.nodes) # [<Coffee>, <Coffee>, ...]
print(developers[0].other_property.nodes) # [<OtherModel>, <OtherModel>, ...]

# Returns developer instances with only the `instance.coffee.nodes` property already fetched
developers = await Developer.find_many({"name": "John"}, auto_fetch_nodes=True, auto_fetch_models=[Coffee])

# Auto-fetch models can also be passed as strings
developers = await Developer.find_many({"name": "John"}, auto_fetch_nodes=True, auto_fetch_models=["Coffee"])

print(developers[0].coffee.nodes) # [<Coffee>, <Coffee>, ...]
print(developers[0].other_property.nodes) # []
```

##### Model.update_one() <a name="model-update-one"></a>

The `update_one()` method finds the first matching graph entity and updates it with the provided properties. If no match was found, nothing is updated and `None` is returned. Properties provided in the update parameter, which have not been defined on the model, will be ignored.

This method takes two mandatory arguments:

- `update`: A dictionary containing the properties to update.
- `filters`: A dictionary containing the filters to use when searching for a match. For more about filters, see the [`Filtering queries`](#query-filters) section.

```python
# Updates the `age` property to `30` in the first encountered node where the name property equals `John`
# The `i_do_not_exist` property will be ignored since it has not been defined on the model
developer = await Developer.update_one({"age": 30, "i_do_not_exist": True}, {"name": "John"})

print(developer) # <Developer age=25>

# Or if no match was found
print(developer) # None
```

###### Returning the updated entity <a name="model-update-one-new"></a>

By default, the `update_one()` method returns the model instance before the update. If you want to return the updated model instance instead, you can do so by passing the `new` parameter to the method and setting it to `True`.

```python
# Updates the `age` property to `30` in the first encountered node where the name property equals `John`
# and returns the updated node
developer = await Developer.update_one({"age": 30}, {"name": "John"}, True)

print(developer) # <Developer age=30>
```

###### Raise on empty result <a name="model-update-one-raise-on-empty-result"></a>

By default, the `update_one()` method will return `None` if no results were found. If you want to raise an exception instead, you can pass `raise_on_empty=True` to the method.

```python
# Raises a `NoResultFound` exception if no results were matched
developer = await Developer.update_one({"age": 30}, {"name": "John"}, raise_on_empty=True)
```

##### Model.update_many() <a name="model-update-many"></a>

The `update_many()` method finds all matching graph entity and updates them with the provided properties. If no match was found, nothing is updated and a `empty list` is returned. Properties provided in the update parameter, which have not been defined on the model, will be ignored.

This method takes one mandatory argument `update` which defines which properties to update with which values.

```python
# Updates the `age` property of all `Developer` nodes to 40
developers = await Developer.update_many({"age": 40})

print(developers) # [<Developer age=25>, <Developer age=23>, ...]

# Or if no matches were found
print(developers) # []
```

###### Filters <a name="model-update-many-filters"></a>

Optionally, a `filters` argument can be provided, which defines which entities to update. For more about filters, see the [`Filtering queries`](#query-filters) section.

```python
# Updates all `Developer` nodes where the age property is between `22` and `30`
# to `40`
developers = await Developer.update_many({"age": 40}, {"age": {"$gte": 22, "$lte": 30}})

print(developers) # [<Developer age=25>, <Developer age=23>, ...]
```

###### Returning the updated entity <a name="model-update-many-new"></a>

By default, the `update_many()` method returns the model instances before the update. If you want to return the updated model instances instead, you can do so by passing the `new` parameter to the method and setting it to `True`.

```python
# Updates all `Developer` nodes where the age property is between `22` and `30`
# to `40` and return the updated nodes
developers = await Developer.update_many({"age": 40}, {"age": {"$gte": 22, "$lte": 30}})

print(developers) # [<Developer age=40>, <Developer age=40>, ...]
```

##### Model.delete_one() <a name="model-delete-one"></a>

The `delete_one()` method finds the first matching graph entity and deletes it. Unlike others, this method returns the number of deleted entities instead of the deleted entity itself. If no match was found, nothing is deleted and `0` is returned.

This method takes one mandatory argument `filters` which defines which entity to delete. For more about filters, see the [`Filtering queries`](#query-filters) section.

```python
# Deletes the first `Developer` node where the name property equals `John`
count = await Developer.delete_one({"name": "John"})

print(count) # 1

# Or if no match was found
print(count) # 0
```

###### Raise on empty result <a name="model-delete-one-raise-on-empty-result"></a>

By default, the `delete_one()` method will return `None` if no results were found. If you want to raise an exception instead, you can pass `raise_on_empty=True` to the method.

```python
# Raises a `NoResultFound` exception if no results were matched
count = await Developer.delete_one({"name": "John"}, raise_on_empty=True)
```

##### Model.delete_many() <a name="model-delete-many"></a>

The `delete_many()` method finds all matching graph entity and deletes them. Like the `delete_one()` method, this method returns the number of deleted entities instead of the deleted entity itself. If no match was found, nothing is deleted and `0` is returned.

```python
# Deletes all `Developer` nodes
count = await Developer.delete_many()

print(count) # However many nodes matched the filter

# Or if no match was found
print(count) # 0
```

###### Filters <a name="model-delete-many-filters"></a>

Optionally, a `filters` argument can be provided, which defines which entities to delete. For more about filters, see the [`Filtering queries`](#query-filters) section.

```python
# Deletes all `Developer` nodes where the age property is greater than `65`
count = await Developer.delete_many({"age": {"$gt": 65}})

print(count) # However many nodes matched the filter
```

##### Model.count() <a name="model-count"></a>

The `count()` method returns the total number of entities of this model in the graph.

```python
# Returns the total number of `Developer` nodes inside the database
count = await Developer.count()

print(count) # However many nodes matched the filter

# Or if no match was found
print(count) # 0
```

###### Filters <a name="model-count-filters"></a>

Optionally, a `filters` argument can be provided, which defines which entities to count. For more about filters, see the [`Filtering queries`](#query-filters) section.

```python
# Counts all `Developer` nodes where the name property contains the letters `oH`
# The `i` in `icontains` means that the filter is case insensitive
count = await Developer.count({"name": {"$icontains": "oH"}})

print(count) # However many nodes matched the filter
```

##### NodeModelInstance.create() <a name="node-model-instance-create"></a>

> **Note**: This method is only available for classes inheriting from the `NodeModel` class.

The `create()` method allows you to create a new node from a given model instance. All properties defined on the instance will be carried over to the corresponding node inside the graph. After this method has successfully finished, the instance saved to the database will be seen as `hydrated` and other methods such as `update()`, `refresh()`, etc. will be available.

```python
# Creates a node inside the graph with the properties and labels
# from the model below
developer = Developer(name="John", age=24)
await developer.create()

print(developer) # <Developer uid="..." age=24, name="John">
```

##### NodeModelInstance.find_connected_nodes() <a name="node-model-instance-find-connected-nodes"></a>

> **Note**: This method is only available for classes inheriting from the `NodeModel` class.

The `find_connected_nodes()` method can be used to find nodes over multiple hops. It returns all matched nodes with the defined labels in the given hop range or an empty list if no nodes where found. The method requires you to define the labels of the nodes you want to find inside the filters (You can only define the labels of `one model` at a time). For more about filters, see the [`Filtering queries`](#query-filters) section.

```python
# Picture a structure like this inside the graph:
# (:Producer)-[:SELLS_TO]->(:Barista)-[:PRODUCES {with_love: bool}]->(:Coffee)-[:CONSUMED_BY]->(:Developer)

# If we want to get all `Developer` nodes connected to a `Producer` node over the `Barista` and `Coffee` nodes,
# where the `Barista` created the coffee with love, we can do so like this:
producer = await Producer.find_one({"name": "Coffee Inc."})

if producer is None:
  # No producer found, do something else

developers = await producer.find_connected_nodes({
  "$node": {
    "$labels": ["Developer", "Python"],
    # You can use all available filters here as well
  },
  # You can define filters on specific relationships inside the path
  "$relationships": [
    {
      # Here we define a filter for all `PRODUCES` relationships
      # Only nodes where the with_love property is set to `True` will be returned
      "$type": "PRODUCES",
      "with_love": True
    }
  ]
})

print(developers) # [<Developer>, <Developer>, ...]

# Or if no matches were found
print(developers) # []
```

###### Projections <a name="node-model-find-connected-nodes-projections"></a>

`Projections` can be used to only return specific parts of the models as dictionaries. For more information about projections, see the [`Projections`](#query-projections) section.

```python
# Returns dictionaries with the developers name at the `dev_name` key instead
# of model instances
developers = await producer.find_connected_nodes(
  {
    "$node": {
      "$labels": ["Developer", "Python"],
    },
    "$relationships": [
      {
        "$type": "PRODUCES",
        "with_love": True
      }
    ]
  },
  {
    "dev_name": "name"
  }
)

print(developers) # [{"dev_name": "John"}, {"dev_name": "John"}, ...]
```

###### Query options <a name="node-model-find-connected-nodes-query-options"></a>

`Query options` can be used to define how results are returned from the query. They are provided via the `options` argument. For more about query options, see the [`Query options`](#query-options) section.

```python
# Skips the first 10 results and returns the next 20
developers = await producer.find_connected_nodes(
  {
    "$node": {
      "$labels": ["Developer", "Python"],
    },
    "$relationships": [
      {
        "$type": "PRODUCES",
        "with_love": True
      }
    ]
  },
  options={"limit": 20, "skip": 10}
)

print(developers) # [<Developer>, <Developer>, ...]
```

###### Auto-fetching nodes <a name="node-model-find-connected-nodes-auto-fetching-nodes"></a>

The `auto_fetch_nodes` and `auto_fetch_models` parameters can be used to automatically fetch all or selected nodes from defined relationship-properties when running the `find_connected_nodes()` query. For more about auto-fetching, see [`Auto-fetching relationship-properties`](#query-auto-fetching).

```python
# Skips the first 10 results and returns the next 20
developers = await producer.find_connected_nodes(
  {
    "$node": {
      "$labels": ["Developer", "Python"],
    },
    "$relationships": [
      {
        "$type": "PRODUCES",
        "with_love": True
      }
    ]
  },
  auto_fetch_nodes=True
)

print(developers[0].coffee.nodes) # [<Coffee>, <Coffee>, ...]
print(developers[0].other_property.nodes) # [<OtherModel>, <OtherModel>, ...]

# Returns developer instances with only the `instance.coffee.nodes` property already fetched
developers = await producer.find_connected_nodes(
  {
    "$node": {
      "$labels": ["Developer", "Python"],
    },
    "$relationships": [
      {
        "$type": "PRODUCES",
        "with_love": True
      }
    ]
  },
  auto_fetch_nodes=True,
  auto_fetch_models=[Coffee]
)

developers = await producer.find_connected_nodes(
  {
    "$node": {
      "$labels": ["Developer", "Python"],
    },
    "$relationships": [
      {
        "$type": "PRODUCES",
        "with_love": True
      }
    ]
  },
  auto_fetch_nodes=True,
  auto_fetch_models=["Coffee"]
)

print(developers[0].coffee.nodes) # [<Coffee>, <Coffee>, ...]
print(developers[0].other_property.nodes) # []
```

##### RelationshipModelInstance.start_node() <a name="relationship-model-instance-start-node"></a>

> **Note**: This method is only available for classes inheriting from the `RelationshipModel` class.

This method returns the start node of the current relationship instance. This method takes no arguments.

```python
# The `coffee_relationship` variable is a relationship instance created somewhere above
start_node = await coffee_relationship.start_node()

print(start_node) # <Coffee>
```

##### RelationshipModelInstance.end_node() <a name="relationship-model-instance-end-node"></a>

> **Note**: This method is only available for classes inheriting from the `RelationshipModel` class.

This method returns the end node of the current relationship instance. This method takes no arguments.

```python
# The `coffee_relationship` variable is a relationship instance created somewhere above
end_node = await coffee_relationship.end_node()

print(end_node) # <Developer>
```

#### Serializing models <a name="serializing-models"></a>

When serializing models to a dictionary or JSON string, the models `element_id and id` fields are `automatically added` to the corresponding dictionary/JSON string when calling Pydantic's `dict()` or `json()` methods.

#### Hooks <a name="hooks"></a>

Hooks are a convenient way to execute code before or after a method is called A pre-hook function always receives the `class it is used on` as it's first argument and `any arguments the decorated method receives`. They can be used to execute code that is not directly related to the method itself, but still needs to be executed when the method is called. This allows for all sorts of things, such as logging, caching, etc.

`pyneo4j-ogm` provides a hooks for all available methods out of the box, and will even work for custom methods. Hooks are simply registered with the method name as the key and a list of hook functions as the value. The hook functions can be synchronous or asynchronous and will receive the exact same arguments as the method they are registered for and the current model instance as the first argument.

For relationship-properties, the key under which the hook is registered has to be in the format `<relationship-property>.<method>`. For example, if you want to register a hook for the `connect()` method of a relationship-property named `coffee`, you would have to pass `coffee.connect` as the key. Additionally, instead of the `RelationshipProperty class context`, the hook function will receive the `NodeModel class context` of the model it has been called on as the first argument.

> **Note:** Custom methods to define the `hook decorator` on the method you want to register hooks for.

##### Pre-hooks <a name="pre-hooks"></a>

Pre-hooks are executed before the method they are registered for. They can be defined in the [`model's Settings`](#configuration-settings) class under the `pre_hooks` property or by calling the `register_pre_hooks()` method on the model.

```python
class Developer(NodeModel):
  ...

  class Settings:
    post_hooks = {
      "coffee.connect": lambda self, *args, **kwargs: print(f"{self.name} chugged another one!")
    }


# Or by calling the `register_pre_hooks()` method
# Here `hook_func` can be a synchronous or asynchronous function reference
Developer.register_pre_hooks("create", hook_func)

# By using the `register_pre_hooks()` method, you can also overwrite all previously registered hooks
# This will overwrite all previously registered hooks for the defined hook name
Developer.register_pre_hooks("create", hook_func, overwrite=True)
```

##### Post-hooks <a name="post-hooks"></a>

Post-hooks are executed after the method they are registered for. They can be defined in the [`model's Settings`](#configuration-settings) class under the `post_hooks` property or by calling the `register_post_hooks()` method on the model.

In addition to the same arguments a pre-hook function receives, a post-hook function also receives the result of the method it is registered for as the second argument.

> **Note:** Since post-hooks have the exact same usage/registration options as pre-hooks, they are not explained in detail here.

#### Model settings <a name="model-settings"></a>

Can be used to access the model's settings. For more about model settings, see the [`Model settings`](#model-settings) section.

```python
model_settings = Developer.model_settings()

print(model_settings) # <NodeModelSettings labels={"Developer"}, auto_fetch_nodes=False, ...>
```

### Relationship-properties <a name="relationship-properties"></a>

> **Note**: Relationship-properties are only available for classes which inherit from the `NodeModel` class.

Relationship-properties are a special type of property that can only be defined on a `NodeModel` class. They can be used to define relationships between nodes and other models. They provide a variate of options to fine-tune the relationship and how it behaves. The options are pretty self-explanatory, but let's go through them anyway:

```python
class Developer(NodeModel):

    # Here we define a relationship to one or more `Coffee` nodes, both the target
    # and relationship-model can be defined as strings (Has to be the exact name of the model)

    # Notice that the `RelationshipProperty` class takes two type arguments, the first
    # one being the target model and the second one being the relationship-model
    # Can can get away without defining these, but it is recommended to do so for
    # better type hinting
    coffee: RelationshipProperty["Coffee", "Consumed"] = RelationshipProperty(
        # The target model is the model we want to connect to
        target_model="Coffee",
        # The relationship-model is the model which defines the relationship
        # between a target model (in this case `Coffee`) and the model it is defined on
        relationship_model=Consumed,
        # The direction of the relationship inside the graph
        direction=RelationshipPropertyDirection.OUTGOING,
        # Cardinality defines how many nodes can be connected to the relationship
        # **Note**: This only softly enforces cardinality from the model it's defined on
        # and does not enforce it on the database level
        cardinality=RelationshipPropertyCardinality.ZERO_OR_MORE,
        # Whether to allow multiple connections to the same node
        allow_multiple=True,
    )
```

#### Available methods <a name="relationship-properties-available-methods"></a>

Just like regular models, relationship-properties also provide a few methods to make working with them easier. In this section we are going to take a closer look at the different methods available to you.

> **Note**: In the following, the terms `source node` and `target node` will be used. Source node refers to the `node instance the method is called on` and target node refers to the `node/s passed to the method`.

##### RelationshipProperty.relationships() <a name="relationship-property-relationship"></a>

Returns the relationships between the source node and the target node. The method expects a single argument `node` which has to be the target node of the relationship. This always returns a list of relationship instances or an empty list if no relationships were found.

```python
# The `developer` and `coffee` variables have been defined somewhere above

# Returns the relationships between the two nodes
coffee_relationships = await developer.coffee.relationships(coffee)

print(coffee_relationships) # [<Consumed>, <Consumed>, ...]

# Or if no relationships were found
print(coffee_relationships) # []
```

###### Filters <a name="relationship-property-relationships-filters"></a>

This method also allows for (optional) filters. For more about filters, see the [`Filtering queries`](#query-filters) section.

```python
# Only returns the relationships between the two nodes where
# the `developer liked the coffee`
coffee_relationships = await developer.coffee.relationships(coffee, {"likes_it": True})

print(coffee_relationships) # [<Consumed liked=True>, <Consumed liked=True>, ...]
```

###### Projections <a name="relationship-property-relationships-projections"></a>

`Projections` can be used to only return specific parts of the models as dictionaries. For more information about projections, see the [`Projections`](#query-projections) section.

```python
# Returns dictionaries with the relationships `liked` property is at the
# `loved_it` key instead of model instances
coffee_relationships = await developer.coffee.relationships(coffee, projections={"loved_it": "liked"})

print(coffee_relationships) # [{"loved_it": True}, {"loved_it": False}, ...]
```

###### Query options <a name="relationship-property-relationships-query-options"></a>

`Query options` can be used to define how results are returned from the query. They are provided via the `options` argument. For more about query options, see the [`Query options`](#query-options) section.

```python
# Skips the first 10 results and returns the next 20
coffee_relationships = await developer.coffee.relationships(coffee, options={"limit": 20, "skip": 10})

print(coffee_relationships) # [<Consumed>, <Consumed>, ...] up to 20 results
```

##### RelationshipProperty.connect() <a name="relationship-property-connect"></a>

Connects the given target node to the source node. The method expects the target node as the first argument, and optional properties as the second argument. The properties provided will be carried over to the relationship inside the graph.

Depending on the `allow_multiple` option, which is defined on the relationship-property, this method will either create a new relationship or update the existing one. If the `allow_multiple` option is set to `True`, this method will always create a new relationship. Otherwise, the query will use a `MERGE` statement to update an existing relationship.

```python
# The `developer` and `coffee` variables have been defined somewhere above

coffee_relationship = await developer.coffee.connect(coffee, {"likes_it": True})

print(coffee_relationship) # <Consumed>
```

##### RelationshipProperty.disconnect() <a name="relationship-property-disconnect"></a>

Disconnects the target node from the source node and deletes all relationships between them. The only argument to the method is the target node. If no relationships exist between the two, nothing is deleted and `0` is returned. Otherwise, the number of deleted relationships is returned.

> **Note**: If `allow_multiple` was set to `True` and multiple relationships to the target node exist, all of them will be deleted.

```python
# The `developer` and `coffee` variables have been defined somewhere above

coffee_relationship_count = await developer.coffee.disconnect(coffee)

print(coffee_relationship_count) # However many relationships were deleted
```

###### Raise on empty result <a name="relationship-property-disconnect-raise-on-empty-result"></a>

By default, the `disconnect()` method will return `None` if no results were found. If you want to raise an exception instead, you can pass `raise_on_empty=True` to the method.

```python
# Raises a `NoResultFound` exception if no results were matched
coffee_relationship_count = await developer.coffee.disconnect(coffee, raise_on_empty=True)
```

##### RelationshipProperty.disconnect_all() <a name="relationship-property-disconnect-all"></a>

Disconnects all target nodes from the source node and deletes all relationships between them. Returns the number of deleted relationships.

```python
# This will delete all relationships to `Coffee` nodes for this `Developer` node
coffee_relationship_count = await developer.coffee.disconnect_all()

print(coffee_relationship_count) # However many relationships were deleted
```

##### RelationshipProperty.replace() <a name="relationship-property-replace"></a>

Disconnects all relationships from the source node to the old target node and connects them back to the new target node, carrying over all properties defined in the relationship. Returns the replaced relationships.

> **Note**: If `multiple relationships` between the target node and the old source node exist, `all of them` will be replaced.

```python
# Currently there are two relationships defined between the `developer` and `coffee_latte`
# nodes where the `likes_it` property is set to `True` and `False` respectively

# Moves the relationships from `coffee_latte` to `coffee_americano`
replaced_coffee_relationships = await developer.coffee.replace(coffee_latte, coffee_americano)

print(replaced_coffee_relationships) # [<Consumed likes_it=True>, <Consumed likes_it=False>]
```

##### RelationshipProperty.find_connected_nodes() <a name="relationship-property-find-connected-nodes"></a>

Finds and returns all connected nodes for the given relationship-property. This method always returns a list of instances/dictionaries or an empty list if no results were found.

```python
# Returns all `Coffee` nodes
coffees = await developer.coffee.find_connected_nodes()

print(coffees) # [<Coffee>, <Coffee>, ...]

# Or if no matches were found
print(coffees) # []
```

###### Filters <a name="relationship-property-find-connected-nodes-filters"></a>

You can pass filters using the `filters` argument to filter the returned nodes. For more about filters, see the [`Filtering queries`](#query-filters) section.

```python
# Returns all `Coffee` nodes where the `sugar` property is set to `True`
coffees = await developer.coffee.find_connected_nodes({"sugar": True})

print(coffees) # [<Coffee sugar=True>, <Coffee sugar=True>, ...]
```

###### Projections <a name="relationship-property-find-connected-nodes-projections"></a>

`Projections` can be used to only return specific parts of the models as dictionaries. For more information about projections, see the [`Projections`](#query-projections) section.

```python
# Returns dictionaries with the coffee's `sugar` property at the `contains_sugar` key instead
# of model instances
coffees = await developer.coffee.find_connected_nodes({"sugar": True}, {"contains_sugar": "sugar"})

print(coffees) # [{"contains_sugar": True}, {"contains_sugar": False}, ...]
```

###### Query options <a name="relationship-property-find-connected-nodes-query-options"></a>

`Query options` can be used to define how results are returned from the query. They are provided via the `options` argument. For more about query options, see the [`Query options`](#query-options) section.

```python
# Skips the first 10 results and returns the next 20
coffees = await developer.coffee.find_connected_nodes({"sugar": True}, options={"limit": 20, "skip": 10})

# Skips the first 10 results and returns up to 20
print(coffees) # [<Coffee>, <Coffee>, ...]
```

###### Auto-fetching nodes <a name="relationship-property-find-connected-nodes-auto-fetching-nodes"></a>

The `auto_fetch_nodes` and `auto_fetch_models` parameters can be used to automatically fetch all or selected nodes from defined relationship-properties when running the `find_many()` query. For more about auto-fetching, see [`Auto-fetching relationship-properties`](#query-auto-fetching).

```python
# Returns coffee instances with `instance.<property>.nodes` properties already fetched
coffees = await developer.coffee.find_connected_nodes(auto_fetch_nodes=True)

print(coffees[0].developer.nodes) # [<Developer>, <Developer>, ...]
print(coffees[0].other_property.nodes) # [<OtherModel>, <OtherModel>, ...]

# Returns coffee instances with only the `instance.developer.nodes` property already fetched
coffees = await developer.coffee.find_connected_nodes(auto_fetch_nodes=True, auto_fetch_models=[Developer])

# Auto-fetch models can also be passed as strings
coffees = await developer.coffee.find_connected_nodes(auto_fetch_nodes=True, auto_fetch_models=["Developer"])

print(coffees[0].developer.nodes) # [<Developer>, <Developer>, ...]
print(coffees[0].other_property.nodes) # []
```

#### Hooks with relationship properties <a name="hooks-with-relationship-properties"></a>

Although slightly different, hooks can also be registered for relationship-properties. The only different lies in the arguments passed to the hook function. Since relationship-properties are defined on a `NodeModel` class, the hook function will receive the `NodeModel class context` of the model it has been called on as the first argument instead of the `RelationshipProperty class context` (like it would for regular models).

> **Note:** The rest of the arguments passed to the hook function are the same as for regular models.

```python
class Developer(NodeModel):

    # Here we define a relationship to one or more `Coffee` nodes, both the target
    # and relationship-model can be defined as strings (Has to be the exact name of the model)

    # Notice that the `RelationshipProperty` class takes two type arguments, the first
    # one being the target model and the second one being the relationship-model
    # Can can get away without defining these, but it is recommended to do so for
    # better type hinting
    coffee: RelationshipProperty["Coffee", "Consumed"] = RelationshipProperty(
        # The target model is the model we want to connect to
        target_model="Coffee",
        # The relationship-model is the model which defines the relationship
        # between a target model (in this case `Coffee`) and the model it is defined on
        relationship_model=Consumed,
        # The direction of the relationship inside the graph
        direction=RelationshipPropertyDirection.OUTGOING,
        # Cardinality defines how many nodes can be connected to the relationship
        # **Note**: This only softly enforces cardinality from the model it's defined on
        # and does not enforce it on the database level
        cardinality=RelationshipPropertyCardinality.ZERO_OR_MORE,
        # Whether to allow multiple connections to the same node
        allow_multiple=True,
    )

    class Settings:
        post_hooks = {
            "coffee.connect": lambda self, *args, **kwargs: print(type(self))
        }

# Somewhere further down the line...
# Prints `<class '__main__.Developer'>` instead of `<class '__main__.RelationshipProperty'>`
await developer.coffee.connect(coffee)
```

The reason for this change in the hooks behavior is simple, really. Since relationship-properties are only used to define relationships between nodes, it makes more sense to have the `NodeModel class context` available inside the hook function instead of the `RelationshipProperty class context`, since the hook function will most likely be used to execute code on the model the relationship-property is defined on.

### Queries <a name="queries"></a>

As you might have seen by now, `pyneo4j-ogm` provides a variate of methods to query the graph. If you followed the documentation up until this point, you might have seen that most of the methods take a `filters` argument.

If you have some `prior experience` with `Neo4j and Cypher`, you may know that it does not provide a easy way to generate queries from given inputs. This is where `pyneo4j-ogm` comes in. It provides a `variety of filters` to make querying the graph as easy as possible.

The filters are heavily inspired by [`MongoDB's query language`](https://docs.mongodb.com/manual/tutorial/query-documents/), so if you have some experience with that, you will feel right at home.

This is really nice to have, not only for normal usage, but especially if you are developing a `gRPC service` or `REST API` and want to provide a way to query the graph from the outside.

But enough of that, let's take a look at the different filters available to you.

#### Filtering queries <a name="query-filters"></a>

Since the filters are inspired by MongoDB's query language, they are also very similar. The filters are defined as dictionaries, where the keys are the properties you want to filter on and the values are the values you want to filter for.

We can roughly separate them into the `following categories`:

- Comparison operators
- String operators
- List operators
- Logical operators
- Element operators

##### Comparison operators <a name="query-filters-comparison-operators"></a>

Comparison operators are used to compare values to each other. They are the most basic type of filter.

| Operator | Description | Corresponding Cypher query |
| --- | --- | --- |
| `$eq` | Matches values that are equal to a specified value. | `WHERE node.property = value` |
| `$neq` | Matches all values that are not equal to a specified value. | `WHERE node.property <> value` |
| `$gt` | Matches values that are greater than a specified value. | `WHERE node.property > value` |
| `$gte` | Matches values that are greater than or equal to a specified value. | `WHERE node.property >= value` |
| `$lt` | Matches values that are less than a specified value. | `WHERE node.property < value` |
| `$lte` | Matches values that are less than or equal to a specified value. | `WHERE node.property <= value` |

##### String operators <a name="query-filters-string-operators"></a>

String operators are used to compare string values to each other.

| Operator | Description | Corresponding Cypher query |
| --- | --- | --- |
| `$contains` | Matches values that contain a specified value. | `WHERE node.property CONTAINS value` |
| `$icontains` | Matches values that contain a specified case insensitive value. | `WHERE toLower(node.property) CONTAINS toLower(value)` |
| `$startsWith` | Matches values that start with a specified value. | `WHERE node.property STARTS WITH value` |
| `$istartsWith` | Matches values that start with a specified case insensitive value. | `WHERE toLower(node.property) STARTS WITH toLower(value)` |
| `$endsWith` | Matches values that end with a specified value. | `WHERE node.property ENDS WITH value` |
| `$iendsWith` | Matches values that end with a specified case insensitive value. | `WHERE toLower(node.property) ENDS WITH toLower(value)` |
| `$regex` | Matches values that match a specified regular expression (Regular expressions used by Neo4j and Cypher). | `WHERE node.property =~ value` |

##### List operators <a name="query-filters-list-operators"></a>

List operators are used to compare list values to each other.

| Operator | Description | Corresponding Cypher query |
| --- | --- | --- |
| `$in` | Matches lists where at least one item is in the given list. | `WHERE ANY(i IN node.property WHERE i IN value)` |
| `$nin` | Matches lists where no items are in the given list | `WHERE NONE(i IN node.property WHERE i IN value)` |
| `$all` | Matches lists where all items are in the given list. | `WHERE ALL(i IN node.property WHERE i IN value)` |
| `$size` | Matches lists where the size of the list is equal to the given value. | `WHERE size(node.property) = value` |

> **Note**: The `$size` operator can also be combined with the comparison operators by nesting them inside the `$size` operator. For example: `{"$size": {"$gt": 5}}`.

##### Logical operators <a name="query-filters-logical-operators"></a>

Logical operators are used to combine multiple filters with each other.

| Operator | Description | Corresponding Cypher query |
| --- | --- | --- |
| `$and` | Joins query clauses with a logical AND returns all nodes that match the conditions of both clauses (Used by default if multiple filters are present). | `WHERE node.property1 = value1 AND node.property2 = value2` |
| `$or` | Joins query clauses with a logical OR returns all nodes that match the conditions of either clause. | `WHERE node.property1 = value1 OR node.property2 = value2` |
| `$xor` | Joins query clauses with a logical XOR returns all nodes that match the conditions of either clause but not both. | `WHERE WHERE node.property1 = value1 XOR node.property2 = value2` |
| `$not` | Inverts the effect of a query expression nested within and returns nodes that do not match the query expression. | `WHERE NOT (node.property = value)` |

##### Element operators <a name="query-filters-element-operators"></a>

Element operators are a special kind of operator not available for every filter type. They are used to check Neo4j-specific values.

| Operator | Description | Corresponding Cypher query |
| --- | --- | --- |
| `$exists` | Matches nodes that have the specified property. | `WHERE EXISTS(node.property)` |
| `$elementId` | Matches nodes that have the specified element id. | `WHERE elementId(node) = value` |
| `$id` | Matches nodes that have the specified id. | `WHERE id(node) = value` |
| `$labels` | Matches nodes that have the specified labels. | `WHERE ALL(i IN labels(n) WHERE i IN value)` |
| `$type` | Matches relationships that have the specified type. Can be either a list or a string. | For a string: `WHERE type(r) = value`, For a list: `WHERE type(r) IN value` |

##### Pattern matching <a name="query-filters-pattern-matching"></a>

The filters we have seen so far are great for simple queries, but what if we need to filter our nodes based on relationships to other nodes? This is where `pattern matching` comes in. Pattern matching allows us to define a `pattern` of nodes and relationships we want to match (or ignore). This is done by defining a `list of patterns` inside the `$patterns` key of the filter. Here is a short summary of the available operators inside a pattern:

- `$node`: Filters applied to the target node. Expects a dictionary containing basic filters.
- `$relationship`: Filters applied to the relationship between the source node and the target node. Expects a dictionary containing basic filters.
- `$direction`: The direction of the pattern. Can be either INCOMING,OUTGOING or BOTH.
- `$exists`: A boolean value indicating whether the pattern must exist or not.

> **Note**: The `$patterns` key can only be used inside the `root filter` and not inside nested filters. Furthermore, only patterns across a single hop are supported.

To make this as easy to understand as possible, we are going to take a look at a quick example. Let's say our `Developer` can define relationships to his `Coffee`. We want to get all `Developers` who `don't drink` their coffee `with sugar`:

```python
developers = await Developer.find_many({
  "$patterns": [
    {
      # The `$exists` operator tells the library to match/ignore the pattern
      "$exists": False,
      # The defines the direction of the relationship inside the pattern
      "$direction": RelationshipMatchDirection.OUTGOING,
      # The `$node` key is used to define the node we want to filter for. This means
      # the filters inside the `$node` key will be applied to our `Coffee` nodes
      "$node": {
        "$labels": ["Beverage", "Hot"],
        "sugar": False
      },
      # The `$relationship` key is used to filter the relationship between the two nodes
      # It can also define property filters for the relationship
      "$relationship": {
        "$type": "CHUGGED"
      }
    }
  ]
})
```

We can take this even further by defining multiple patters inside the `$patterns` key. Let's say this time our `Developer` can have some other `Developer` friends and we want to get all `Developers` who liked their coffee. At the same time, our developer must be `FRIENDS_WITH` (now the relationship is an incoming one, because why not?) a developer named `Jenny`:

```python
developers = await Developer.find_many({
  "$patterns": [
    {
      "$exists": True,
      "$direction": RelationshipMatchDirection.OUTGOING,
      "$node": {
        "$labels": ["Beverage", "Hot"],
      },
      "$relationship": {
        "$type": "CHUGGED",
        "liked": True
      }
    },
    {
      "$exists": True,
      "$direction": RelationshipMatchDirection.INCOMING,
      "$node": {
        "$labels": ["Developer"],
        "name": "Jenny"
      },
      "$relationship": {
        "$type": "FRIENDS_WITH"
      }
    }
  ]
})
```

##### Multi-hop filters <a name="query-filters-multi-hop-filters"></a>

Multi-hop filters are a special type of filter which is only available for [`NodeModelInstance.find_connected_nodes()`](#node-model-instance-find-connected-nodes). They allow you to specify filter parameters on the target node and all relationships between them over, you guessed it, multiple hops. To define this filter, you have a few operators you can define:

- `$node`: Filters applied to the target node. Expects a dictionary containing basic filters. Can not contain pattern yet.
- `$minHops`: The minimum number of hops between the source node and the target node. Must be greater than 0.
- `$maxHops`: The maximum number of hops between the source node and the target node. You can pass "\*" as a value to define no upper limit. Must be greater than 1.
- `$relationships`: A list of relationship filters. Each filter is a dictionary containing basic filters and must define a $type operator.

```python
# Picture a structure like this inside the graph:
# (:Producer)-[:SELLS_TO]->(:Barista)-[:PRODUCES {with_love: bool}]->(:Coffee)-[:CONSUMED_BY]->(:Developer)

# If we want to get all `Developer` nodes connected to a `Producer` node over the `Barista` and `Coffee` nodes,
# where the `Barista` created the coffee with love.

# Let's say, for the sake of this example, that there are connections possible
# with 10+ hops, but we don't want to include them. To solve this, we can define
# a `$maxHops` filter with a value of `10`.
producer = await Producer.find_one({"name": "Coffee Inc."})

if producer is None:
  # No producer found, do something else

developers = await producer.find_connected_nodes({
  "$maxHops": 10,
  "$node": {
    "$labels": ["Developer", "Python"],
    # You can use all available filters here as well
  },
  # You can define filters on specific relationships inside the path
  "$relationships": [
    {
      # Here we define a filter for all `PRODUCES` relationships
      # Only nodes where the with_love property is set to `True` will be returned
      "$type": "PRODUCES",
      "with_love": True
    }
  ]
})

print(developers) # [<Developer>, <Developer>, ...]

# Or if no matches were found
print(developers) # []
```

#### Projections <a name="query-projections"></a>

Projections are used to only return specific parts of the models as dictionaries. They are defined as a dictionary where the key is the name of the property in the returned dictionary and the value is the name of the property on the model instance.

Projections can help you to reduce bandwidth usage and speed up queries, since you only return the data you actually need.

> **Note:** Only top-level mapping is supported. This means that you can not map properties to a nested dictionary key.

In the following example, we will return a dictionary with a `dev_name` key, which get's mapped to the models `name` property and a `dev_age` key, which get's mapped to the models `age` property. Any defined mapping which does not exist on the model will have `None` as it's value. You can also map the result's `elementId` and `Id` using either `$elementId` or `$id` as the value for the mapped key.

```python
developer = await Developer.find_one({"name": "John"}, {"dev_name": "name", "dev_age": "age", "i_do_not_exist": "some_non_existing_property"})

print(developer) # {"dev_name": "John", "dev_age": 24, "i_do_not_exist": None}
```

#### Query options <a name="query-options"></a>

Query options are used to define how results are returned from the query. They provide some basic functionality for easily implementing pagination, sorting, etc. They are defined as a dictionary where the key is the name of the option and the value is the value of the option. The following options are available:

- `limit`: Limits the number of returned results.
- `skip`: Skips the first `n` results.
- `sort`: Sorts the results by the given property. Can be either a string or a list of strings. If a list is provided, the results will be sorted by the first property and then by the second property, etc.
- `order`: Defines the sort direction. Can be either `ASC` or `DESC`. Defaults to `ASC`.

```python
# Returns 50 results, skips the first 10 and sorts them by the `name` property in descending order
developers = await Developer.find_many({}, options={"limit": 50, "skip": 10, "sort": "name", "order": QueryOptionsOrder.DESCENDING})

print(len(developers)) # 50
print(developers) # [<Developer>, <Developer>, ...]
```

#### Auto-fetching relationship-properties <a name="query-auto-fetching"></a>

You have the option to automatically fetch all defined relationship-properties of matched nodes. This will populate the `instance.<property>.nodes` attribute with the fetched nodes. This can be useful in situations where you need to fetch a specific node and get all of it's related nodes at the same time.

> **Note**: Auto-fetching nodes with many relationships can be very expensive and slow down your queries. Use it with caution.

To enable this behavior, you can either set the `auto_fetch_nodes` parameter to `True` or set the `auto_fetch_nodes setting` in the model settings to `True`, but doing so will `always enable auto-fetching`.

You can also define which relationship-properties to fetch by providing the fetched models to the `auto_fetch_models` parameter. This can be useful if you only want to fetch specific relationship-properties.

Now, let's take a look at an example:

```python
# Fetches everything defined in the relationship-properties of the current matched node
developer = await Developer.find_one({"name": "John"}, auto_fetch_nodes=True)

# All nodes for all defined relationship-properties are now fetched
print(developer.coffee.nodes) # [<Coffee>, <Coffee>, ...]
print(developer.developer.nodes) # [<Developer>, <Developer>, ...]
print(developer.other_property.nodes) # [<OtherModel>, <OtherModel>, ...]
```

With the `auto_fetch_models` parameter, we can define which relationship-properties to fetch:

```python
# Only fetch nodes for `Coffee` and `Developer` models defined in relationship-properties
# The models can also be passed as strings, where the string is the model's name
developer = await Developer.find_one({"name": "John"}, auto_fetch_nodes=True, auto_fetch_models=[Coffee, "Developer"])

# Only the defined models have been fetched
print(developer.coffee.nodes) # [<Coffee>, <Coffee>, ...]
print(developer.developer.nodes) # [<Developer>, <Developer>, ...]
print(developer.other_property.nodes) # []
```

### Logging <a name="logging"></a>

You can control the log level and whether to log to the console or not by setting the `PYNEO4J_OGM_LOG_LEVEL` and `PYNEO4J_OGM_ENABLE_LOGGING` as environment variables. The available levels are the same as provided by the build-in `logging` module. The default log level is `WARNING` and logging to the console is enabled by default.

### Running the test suite <a name="running-the-test-suite"></a>

To run the test suite, you have to install the development dependencies and run the tests using `pytest`. The tests are located in the `tests` directory. Any tests located in the `tests/integration` directory will require you to have a Neo4j instance running on `localhost:7687` with the credentials (`neo4j:password`). This can easily be done using the provided `docker-compose.yml` file.

```bash
poetry run pytest tests --asyncio-mode=auto -W ignore::DeprecationWarning
```

> **Note:** The `-W ignore::DeprecationWarning` can be omitted but will result in a lot of deprication warnings by Neo4j itself about the usage of the now deprecated `ID`.

As for running the tests with a different pydantic version, you can just run the following command locally:

```bash
poetry add pydantic@1.10
```
