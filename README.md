# pyneo4j-ogm

[![PyPI](https://img.shields.io/pypi/v/pyneo4j-ogm?style=flat-square)](https://pypi.org/project/pyneo4j-ogm/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/pyneo4j-ogm?style=flat-square)](https://pypi.org/project/pyneo4j-ogm/)
[![PyPI - License](https://img.shields.io/pypi/l/pyneo4j-ogm?style=flat-square)](https://pypi.org/project/pyneo4j-ogm/)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/pyneo4j-ogm?style=flat-square)](https://pypi.org/project/pyneo4j-ogm/)

[`pyneo4j-ogm`](https://github.com/groc-prog/pyneo4j-ogm/blob/develop) is a asynchronous `Object-Graph-Mapper` for [`Neo4j 5+`](https://neo4j.com/docs/) and [`Python 3.10+`](https://www.python.org/). It is inspired by [`beanie`](https://github.com/roman-right/beanie) and build on top of proven technologies like [`Pydantic 1.10+ and 2+`](https://docs.pydantic.dev/latest/) and the [`Neo4j Python Driver`](https://neo4j.com/docs/api/python-driver/current/index.html). It saves you from writing ever-repeating boilerplate queries and allows you to focus on the `stuff that actually matters`. It is designed to be simple and easy to use, but also flexible and powerful.

## 🎯 Features

[`pyneo4j-ogm`](https://github.com/groc-prog/pyneo4j-ogm/blob/develop) has a lot to offer, including:

- [x] **Fully typed**: pyneo4j-ogm is `fully typed` out of the box.
- [x] **Powerful validation**: Since we use Pydantic under the hood, you can use it's powerful validation and serialization features without any issues.
- [x] **Focus on developer experience**: Designed to be simple to use, pyneo4j-ogm provides features for both simple queries and more `advanced use-cases` while keeping it's API as simple as possible.
- [x] **Build-in migration tooling**: Shipped with simple, yet flexible migration tooling.
- [x] **Fully asynchronous**: Completely asynchronous code, thanks to the `Neo4j Python Driver`.
- [x] **Supports Neo4j 5+**: pyneo4j-ogm supports `Neo4j 5+` and is tested against the latest version of Neo4j.
- [x] **Multi-version Pydantic support**: Both `Pydantic 1.10+` and `2+` fully supported.

## 📣 Announcements

Things to come in the future. Truly exiting stuff! If you have feature requests which you think might improve `pyneo4j-ogm`, feel free to open up a feature request.

- [ ] [MemGraph](https://memgraph.com/) support.

## 📦 Installation

Using [`pip`](https://pip.pypa.io/en/stable/):

```bash
pip install pyneo4j-ogm
```

or when using [`Poetry`](https://python-poetry.org/):

```bash
poetry add pyneo4j-ogm
```

## 🚀 Quickstart

Before we can get going, we have to take care of some things:

- We need to define our models, which will represent the nodes and relationships inside our database.
- We need a database client, which will do the actual work for us.

### Defining our data structures

Since every developer has a coffee addiction one way or another, we are going to use `Coffee` and `Developers` for this guide. So let's start by defining what our data should look like:

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
  This class represents a `Developer` node inside the graph. All interactions
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
  define some configuration for this relationship.

  Note that the relationship itself does not define it's start- and end-nodes,
  making it reusable for other models as well.
  """
  liked: bool

  class Settings:
    type = "CHUGGED"
```

Until now everything seems pretty standard if you have worked with other ORM's before. But if you haven't, we are going to go over what happened above:

- We defined 2 node models `Developer` and `Coffee`, and a relationship `Consumed`.
- Some models define a special inner `Settings` class. This is used to customize the behavior of our models inside the graph. More on these settings can be found [`here`](https://github.com/groc-prog/pyneo4j-ogm/blob/develop/docs/Models.md#configuration-settings).
- The `WithOptions` function has been used to define `constraints and indexes` (more about them [`here`](https://github.com/groc-prog/pyneo4j-ogm/blob/develop/docs/DatabaseClient.md#manual-indexing-and-constraints)) on model properties.

### Creating a database client

In pyneo4j-ogm, the real work is done by a database client. One of these bad-boys can be created by initializing a `Pyneo4jClient` instance. But for models to work as expected, we have to let our client know that we want to use them like so:

```python
from pyneo4j_ogm import Pyneo4jClient

async def main():
  # We initialize a new `Pyneo4jClient` instance and connect to the database.
  client = Pyneo4jClient()

  # Replace `<connection-uri-to-database>`, `<username>` and `<password>` with the
  # actual values.
  await client.connect(uri="<connection-uri-to-database>", auth=("<username>", "<password>"))

  # To use our models for running queries later on, we have to register
  # them with the client.
  # **Note**: You only have to register the models that you want to use
  # for queries and you can even skip this step if you want to use the
  # `Pyneo4jClient` instance for running raw queries.
  await client.register_models([Developer, Coffee, Consumed])
```

### Interacting with the database

Now the fun stuff begins! We are ready to interact with our database. For the sake of this [`quickstart guide`](https://github.com/groc-prog/pyneo4j-ogm/blob/develop?tab=readme-ov-file#-quickstart) we are going to keep it nice and simple, but this is just the surface of what pyneo4j-ogm has to offer.

We are going to create a new `Developer` and some `Coffee` and give him something to drink:

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

### Full example

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

And that's it! You should now see a `Developer` and a `Hot/Beverage` node, connected by a `CONSUMED` relationship. If you want to learn more about the library, you can check out the full [`Documentation`](https://github.com/groc-prog/pyneo4j-ogm/blob/develop/docs).

## 📚 Documentation

In the following we are going to take a closer look at the different parts of `pyneo4j-ogm` and how to use them. We will cover everything pyneo4j-ogm has to offer, from the `Pyneo4jClient` to the `NodeModel` and `RelationshipModel` classes all the way to the `Query filters` and `Auto-fetching relationship-properties`.

### Table of contents

- [pyneo4j-ogm](https://github.com/groc-prog/pyneo4j-ogm/blob/develop?tab=readme-ov-file#pyneo4j-ogm)
  - [🎯 Features](https://github.com/groc-prog/pyneo4j-ogm/blob/develop?tab=readme-ov-file#features)
  - [📣 Announcements](https://github.com/groc-prog/pyneo4j-ogm/blob/develop?tab=readme-ov-file#-announcements)
  - [📦 Installation](https://github.com/groc-prog/pyneo4j-ogm/blob/develop?tab=readme-ov-file#-installation)
  - [🚀 Quickstart](https://github.com/groc-prog/pyneo4j-ogm/blob/develop?tab=readme-ov-file#-quickstart)
    - [Defining our data structures](https://github.com/groc-prog/pyneo4j-ogm/blob/develop?tab=readme-ov-file#-defining-our-data-structures)
    - [Creating a database client](https://github.com/groc-prog/pyneo4j-ogm/blob/develop?tab=readme-ov-file#-creating-a-database-client)
    - [Interacting with the database](https://github.com/groc-prog/pyneo4j-ogm/blob/develop?tab=readme-ov-file#-interacting-with-the-database)
    - [Full example](https://github.com/groc-prog/pyneo4j-ogm/blob/develop?tab=readme-ov-file#-full-example)
  - [Running the test suite](https://github.com/groc-prog/pyneo4j-ogm/blob/develop?tab=readme-ov-file#-running-the-test-suite)
  - [📚 Documentation](https://github.com/groc-prog/pyneo4j-ogm/blob/develop/docs)
    - [Basic concepts](https://github.com/groc-prog/pyneo4j-ogm/blob/develop/docs/Concept.md)
      - [A note on Pydantic version support](https://github.com/groc-prog/pyneo4j-ogm/blob/develop/docs/Concept.md#a-note-on-pydantic-version-support)
    - [Database client](https://github.com/groc-prog/pyneo4j-ogm/blob/develop/docs/DatabaseClient.md)
      - [Connecting to the database](https://github.com/groc-prog/pyneo4j-ogm/blob/develop/docs/DatabaseClient.md#connecting-to-the-database)
      - [Closing an existing connection](https://github.com/groc-prog/pyneo4j-ogm/blob/develop/docs/DatabaseClient.md#closing-an-existing-connection)
      - [Registering models](https://github.com/groc-prog/pyneo4j-ogm/blob/develop/docs/DatabaseClient.md#registering-models)
      - [Executing Cypher queries](https://github.com/groc-prog/pyneo4j-ogm/blob/develop/docs/DatabaseClient.md#executing-cypher-queries)
      - [Batching cypher queries](https://github.com/groc-prog/pyneo4j-ogm/blob/develop/docs/DatabaseClient.md#batching-cypher-queries)
      - [Using bookmarks (Enterprise Edition only)](https://github.com/groc-prog/pyneo4j-ogm/blob/develop/docs/DatabaseClient.md#using-bookmarks-enterprise-edition-only)
      - [Manual indexing and constraints](https://github.com/groc-prog/pyneo4j-ogm/blob/develop/docs/DatabaseClient.md#manual-indexing-and-constraints)
      - [Client utilities](https://github.com/groc-prog/pyneo4j-ogm/blob/develop/docs/DatabaseClient.md#client-utilities)
    - [Models](https://github.com/groc-prog/pyneo4j-ogm/blob/develop/docs/Models.md)
      - [Indexes, constraints and properties](https://github.com/groc-prog/pyneo4j-ogm/blob/develop/docs/Models.md#indexes-constraints-and-properties)
      - [Reserved properties](https://github.com/groc-prog/pyneo4j-ogm/blob/develop/docs/Models.md#reserved-properties)
      - [Configuration settings](https://github.com/groc-prog/pyneo4j-ogm/blob/develop/docs/Models.md#configuration-settings)
        - [NodeModel configuration](https://github.com/groc-prog/pyneo4j-ogm/blob/develop/docs/Models.md#nodemodel-configuration)
        - [RelationshipModel configuration](https://github.com/groc-prog/pyneo4j-ogm/blob/develop/docs/Models.md#relationshipmodel-configuration)
      - [Available methods](https://github.com/groc-prog/pyneo4j-ogm/blob/develop/docs/Models.md#available-methods)
        - [Instance.update()](https://github.com/groc-prog/pyneo4j-ogm/blob/develop/docs/Models.md#instanceupdate)
        - [Instance.delete()](https://github.com/groc-prog/pyneo4j-ogm/blob/develop/docs/Models.md#instancedelete)
        - [Instance.refresh()](https://github.com/groc-prog/pyneo4j-ogm/blob/develop/docs/Models.md#instancerefresh)
        - [Model.find_one()](https://github.com/groc-prog/pyneo4j-ogm/blob/develop/docs/Models.md#modelfind_one)
        - [Model.find_many()](https://github.com/groc-prog/pyneo4j-ogm/blob/develop/docs/Models.md#modelfind_many)
        - [Model.update_one()](https://github.com/groc-prog/pyneo4j-ogm/blob/develop/docs/Models.md#modelupdate_one)
        - [Model.update_many()](https://github.com/groc-prog/pyneo4j-ogm/blob/develop/docs/Models.md#modelupdate_many)
        - [Model.delete_one()](https://github.com/groc-prog/pyneo4j-ogm/blob/develop/docs/Models.md#modeldelete_one)
        - [Model.delete_many()](https://github.com/groc-prog/pyneo4j-ogm/blob/develop/docs/Models.md#modeldelete_many)
        - [Model.count()](https://github.com/groc-prog/pyneo4j-ogm/blob/develop/docs/Models.md#modelcount)
        - [NodeModelInstance.create()](https://github.com/groc-prog/pyneo4j-ogm/blob/develop/docs/Models.md#nodemodelinstancecreate)
        - [NodeModelInstance.find_connected_nodes()](https://github.com/groc-prog/pyneo4j-ogm/blob/develop/docs/Models.md#nodemodelinstancefind_connected_nodes)
        - [RelationshipModelInstance.start_node()](https://github.com/groc-prog/pyneo4j-ogm/blob/develop/docs/Models.md#relationshipmodelinstancestart_node)
        - [RelationshipModelInstance.end_node()](https://github.com/groc-prog/pyneo4j-ogm/blob/develop/docs/Models.md#relationshipmodelinstanceend_node)
      - [Serializing models](https://github.com/groc-prog/pyneo4j-ogm/blob/develop/docs/Models.md#serializing-models)
      - [Hooks](https://github.com/groc-prog/pyneo4j-ogm/blob/develop/docs/Models.md#hooks)
        - [Pre-hooks](https://github.com/groc-prog/pyneo4j-ogm/blob/develop/docs/Models.md#pre-hooks)
        - [Post-hooks](https://github.com/groc-prog/pyneo4j-ogm/blob/develop/docs/Models.md#post-hooks)
      - [Model settings](https://github.com/groc-prog/pyneo4j-ogm/blob/develop/docs/Models.md#model-settings)
    - [Relationship-properties](https://github.com/groc-prog/pyneo4j-ogm/blob/develop/docs/RelationshipProperty.md)
      - [Available methods](https://github.com/groc-prog/pyneo4j-ogm/blob/develop/docs/RelationshipProperty.md#available-methods)
        - [RelationshipProperty.relationships()](https://github.com/groc-prog/pyneo4j-ogm/blob/develop/docs/RelationshipProperty.md#relationshippropertyrelationships)
        - [RelationshipProperty.connect()](https://github.com/groc-prog/pyneo4j-ogm/blob/develop/docs/RelationshipProperty.md#relationshippropertyconnect)
        - [RelationshipProperty.disconnect()](https://github.com/groc-prog/pyneo4j-ogm/blob/develop/docs/RelationshipProperty.md#relationshippropertydisconnect)
        - [RelationshipProperty.disconnect\_all()](https://github.com/groc-prog/pyneo4j-ogm/blob/develop/docs/RelationshipProperty.md#relationshippropertydisconnect_all)
        - [RelationshipProperty.replace()](https://github.com/groc-prog/pyneo4j-ogm/blob/develop/docs/RelationshipProperty.md#relationshippropertyreplace)
        - [RelationshipProperty.find\_connected\_nodes()](https://github.com/groc-prog/pyneo4j-ogm/blob/develop/docs/RelationshipProperty.md#relationshippropertyfind_connected_nodes)
      - [Hooks with relationship properties](https://github.com/groc-prog/pyneo4j-ogm/blob/develop/docs/RelationshipProperty.md#hooks-with-relationship-properties)
    - [Queries](https://github.com/groc-prog/pyneo4j-ogm/blob/develop/docs/Query.md)
      - [Filtering queries](https://github.com/groc-prog/pyneo4j-ogm/blob/develop/docs/Query.md#filtering-queries)
        - [Comparison operators](https://github.com/groc-prog/pyneo4j-ogm/blob/develop/docs/Query.md#comparison-operators)
        - [String operators](https://github.com/groc-prog/pyneo4j-ogm/blob/develop/docs/Query.md#string-operators)
        - [List operators](https://github.com/groc-prog/pyneo4j-ogm/blob/develop/docs/Query.md#list-operators)
        - [Logical operators](https://github.com/groc-prog/pyneo4j-ogm/blob/develop/docs/Query.md#logical-operators)
        - [Element operators](https://github.com/groc-prog/pyneo4j-ogm/blob/develop/docs/Query.md#element-operators)
        - [Pattern matching](https://github.com/groc-prog/pyneo4j-ogm/blob/develop/docs/Query.md#pattern-matching)
        - [Multi-hop filters](https://github.com/groc-prog/pyneo4j-ogm/blob/develop/docs/Query.md#multi-hop-filters)
      - [Projections](https://github.com/groc-prog/pyneo4j-ogm/blob/develop/docs/Query.md#projections)
      - [Query options](https://github.com/groc-prog/pyneo4j-ogm/blob/develop/docs/Query.md#query-options)
      - [Auto-fetching relationship-properties](https://github.com/groc-prog/pyneo4j-ogm/blob/develop/docs/Query.md#auto-fetching-relationship-properties)
    - [Migrations](https://github.com/groc-prog/pyneo4j-ogm/blob/develop/docs/Migrations.md)
      - [Initializing migrations for your project](https://github.com/groc-prog/pyneo4j-ogm/blob/develop/docs/Migrations.md#initializing-migrations-for-your-project)
      - [Creating a new migration](https://github.com/groc-prog/pyneo4j-ogm/blob/develop/docs/Migrations.md#creating-a-new-migration)
      - [Running migrations](https://github.com/groc-prog/pyneo4j-ogm/blob/develop/docs/Migrations.md#running-migrations)
      - [Listing migrations](https://github.com/groc-prog/pyneo4j-ogm/blob/develop/docs/Migrations.md#listing-migrations)
      - [Programmatic usage](https://github.com/groc-prog/pyneo4j-ogm/blob/develop/docs/Migrations.md#programmatic-usage)
    - [Logging](https://github.com/groc-prog/pyneo4j-ogm/blob/develop/docs/Logging.md)

### Running the test suite

To run the test suite, you have to install the development dependencies and run the tests using `pytest`. The tests are located in the `tests` directory. Some tests will require you to have a Neo4j instance running on `localhost:7687` with the credentials (`neo4j:password`). This can easily be done using the provided `docker-compose.yml` file.

```bash
poetry run pytest tests --asyncio-mode=auto -W ignore::DeprecationWarning
```

> **Note:** The `-W ignore::DeprecationWarning` can be omitted but will result in a lot of deprication warnings by Neo4j itself about the usage of the now deprecated `ID`.

As for running the tests with a different pydantic version, you can just install a different pydantic version with the following command:

```bash
poetry add pydantic@<version>
```
