# Neo4j Object Graph Mapper
A asynchronous library for working with Neo4j and Python 3.10+. The aim of this library is to provide a **clean and structured** way to work with Neo4j in Python. It is built on top of the [`Neo4j Python Driver`](https://neo4j.com/docs/api/python-driver/current/index.html) and [`pydantic 1.10`](https://docs.pydantic.dev/1.10/).


## ⚡️ Quick start <a name="quick-start"></a>
Before we can start to interact with the our database in any way, we have to do `three simple things`:
- Connect to our database instance
- Define our node and relationship models as Python classes
- Register our models with the client instance

First, let's connect to our database instance. We can do this by creating a new instance of the `Neo4jClient` class. This class is primarily used to interact with the database. We can create a new instance of the class and connect to a database like this:
```python
from neo4j_ogm import Neo4jClient

client = Neo4jClient()
client.connect(uri="<connection-uri-to-database>", auth=("<username>", "<password>"))

# The `.connect()` allows to be chained right after the instantiation of the class
# for more convenience.
client = Neo4jClient().connect(uri="<connection-uri-to-database>", auth=("<username>", "<password>"))
```

Next, we have to define our node and relationship models. We can do this by creating a new class that inherits from the `NodeModel` or `RelationshipModel` class. Let's create some simple models we can use to represent a `Developer` who `DRINKS` some `Coffee`:
```python
from neo4j_ogm import (
  NodeModel,
  RelationshipModel,
  RelationshipProperty,
  RelationshipPropertyDirection,
  RelationshipPropertyCardinality
)


class Developer(NodeModel):
  """
  A model representing a developer node in the graph.
  """
  name: str
  age: int

  coffee: RelationshipProperty["Coffee", "Drinks"] = RelationshipProperty(
    target_model="Coffee",
    relationship_model="Drinks",
    direction=RelationshipPropertyDirection.OUTGOING,
    cardinality=RelationshipPropertyCardinality.ZERO_OR_MORE,
    allow_multiple=True,
  )


class Coffee(NodeModel):
  """
  A model representing a coffee node in the graph.
  """
  name: str


class Drinks(RelationshipModel):
  """
  A model representing a DRINKS relationship between a developer and a coffee node.
  """
  likes_it: bool
```

Finally, we have to register our models with the client instance and put everything together. We can do this by calling the `register_models()` method on the client instance and passing in our models as arguments:
```python
import asyncio
from neo4j_ogm import (
  Neo4jClient,
  NodeModel,
  RelationshipModel,
  RelationshipProperty,
  RelationshipPropertyDirection,
  RelationshipPropertyCardinality
)


class Developer(NodeModel):
  """
  A model representing a developer node in the graph.
  """
  name: str
  age: int

  coffee: RelationshipProperty["Coffee", "Drinks"] = RelationshipProperty(
    target_model="Coffee",
    relationship_model="Drinks",
    direction=RelationshipPropertyDirection.OUTGOING,
    cardinality=RelationshipPropertyCardinality.ZERO_OR_MORE,
    allow_multiple=True,
  )


class Coffee(NodeModel):
  """
  A model representing a coffee node in the graph.
  """
  name: str


class Drinks(RelationshipModel):
  """
  A model representing a DRINKS relationship between a developer and a coffee node.
  """
  likes_it: bool


async def main():
  client = Neo4jClient().connect(uri="<connection-uri-to-database>", auth=("<username>", "<password>"))
  await client.register_models([Developer, Coffee, Drinks])

  # The following code will create a new `Developer` and `Coffee` node in the graph
  # and create a new `DRINKS` relationship between them.
  developer = await Developer(name="John Doe", age=25).create()
  coffee = await Coffee(name="Espresso").create()

  await developer.coffee.connect(coffee, {"likes_it": True})

# Run the main function
asyncio.run(main())
```

> This script should run `as is` if you have to change the `uri` and `auth` parameters in the `connect()` method call to match the ones needed for your own database.


And just like that you have created a new `Developer` and `Coffee` node in the graph and created a new `DRINKS` relationship between them. This is just a simple example of what you can do with this library. For more information about the basic concepts of this library, see the [`Basic concepts`](#basic-concepts) section.


## 📚 Documentation <a name="documentation"></a>


### Table of contents <a name="table-of-contents"></a>
- [Neo4j Object Graph Mapper](#neo4j-object-graph-mapper)
  - [⚡️ Quick start ](#️-quick-start-)
  - [📚 Documentation ](#-documentation-)
    - [Table of contents ](#table-of-contents-)
    - [Basic concepts ](#basic-concepts-)
    - [Node models ](#node-models-)
      - [Defining a node model ](#defining-a-node-model-)
      - [Working with node models ](#working-with-node-models-)
    - [Relationship models ](#relationship-models-)
      - [Defining a relationship model ](#defining-a-relationship-model-)
      - [Working with relationship models ](#working-with-relationship-models-)
    - [Relationship properties on node models ](#relationship-properties-on-node-models-)
      - [Defining connections between node models ](#defining-connections-between-node-models-)
      - [Working with relationship properties on node models ](#working-with-relationship-properties-on-node-models-)
    - [Database client ](#database-client-)
      - [Connecting to a database instance ](#connecting-to-a-database-instance-)
      - [Closing an existing connection ](#closing-an-existing-connection-)
      - [Registering node and relationship models ](#registering-node-and-relationship-models-)
      - [Executing Cypher queries ](#executing-cypher-queries-)
      - [Batching cypher queries ](#batching-cypher-queries-)
      - [Working with indexes and constraints ](#working-with-indexes-and-constraints-)
    - [Filter API ](#filter-api-)
      - [Basic filters ](#basic-filters-)
      - [Pattern matching ](#pattern-matching-)
      - [Multi-hop filters ](#multi-hop-filters-)
    - [Extended functionality of models ](#extended-functionality-of-models-)
      - [Importing/Exporting models from/to dictionaries ](#importingexporting-models-fromto-dictionaries-)
      - [Model hooks ](#model-hooks-)


### Basic concepts <a name="basic-concepts"></a>
If you have worked with other ORM's like `sqlalchemy` or `beanie` before, you will find that this library is very similar to them. The main idea behind neo4j-ogm is to work with nodes and relationships in a **structured and easy-to-use** way instead of writing out complex cypher queries and tons of boilerplate for simple operations.

The concept of the library builds on the idea of defining nodes and relationships present in the graph database as **Python classes**. This allows for easy and structured access to the data in the database. These classes provide a robust foundation for working with a Neo4j database. On top of that, the library provides additional features like a `custom filter system` and `automatic resolving of models from queries` out of the box. All of this is done in a **asynchronous** way using the asynchronous driver provided by Neo4j.

In the following sections we will take a look at all of the features of this library and how to use them.

> **Note:** All of the examples in this documentation assume that you have already connected to a database instance and registered your models with the client instance. The models used in the following examples will build upon the ones defined in the [`Quick start`](#quick-start) section.

### Node models <a name="node-models"></a>
Node models are used to represent different nodes inside a graph, but at the same time they provide a structured way of handling them. They are defined as Python classes that inherit from the `NodeModel` class.

If you have worked with `pydantic` before, you will find that the syntax for defining node models is very similar to defining `pydantic` models. This is because under the hood neo4j-ogm makes **heavy use of pydantic** to provide a robust foundation for data validation, serialization and many other features.


#### Defining a node model <a name="defining-a-node-model"></a>
Node models are defined by creating a new class that inherits from the `NodeModel` class. The newly created class can then be used to define properties on nodes in the graph and settings for the model itself. neo4j-ogm also provides a simple way of defining fields with indexes or constraints with the use of the `WithOptions` function. Let's take a look at an example of a node model:
```python
from pydantic import Field, validator
from uuid import UUID, uuid4
from neo4j_ogm import NodeModel, WithOptions


class Developer(NodeModel):
  """
  A model representing a developer node in the graph.
  """
  # Here we define a field with a unique constraint and a default value.
  id: WithOptions(UUID, unique=True) = Field(default_factory=uuid4)
  # Here we set a text_index on the name field.
  name: WithOptions(str, text_index=True)
  age: int

  # Here we define a custom validator for the age field.
  # This validator will make sure that the age is always greater than 0.
  @validator("age")
  def age_must_be_greater_than_zero(cls, v):
    if v <= 0:
      raise ValueError("age must be greater than 0")
    return v
```

Since the `NodeModel` class internally builds upon the `pydantic.BaseModel` class, all of the features provided by `pydantic` are also available for node models. This includes things like `field validation`, `serialization`, `custom validators` and many more. For more information about the features provided by `pydantic`, see the [`pydantic documentation`](https://pydantic-docs.helpmanual.io/).

In the example we defined two important things:
- The `id` field is defined with the `unique` constraint. This means that every node created with this model must have a unique `id` field. This can be compared to a unique index in SQL databases.
- The `name` field is defined with the `text_index` option. This means that the database will create a new text index for this field when the model is registered. This can be compared to a full-text index in SQL databases.

With the `WithOptions` function we can define additional options for fields on node models. This function takes the following arguments:
- `property_type`: The actual data type of the field.
- `range_index`: Whether or not to create a range index for the field.
- `text_index`: Whether or not to create a text index for the field.
- `point_index`: Whether or not to create a point index for the field.
- `unique`: Whether or not to create a unique constraint for the field.


Node models also support a number of settings, which can be defined by creating a nested class called `Settings` inside the node model. The following settings are available:


#### Working with node models <a name="working-with-node-models"></a>


### Relationship models <a name="relationship-models"></a>

#### Defining a relationship model <a name="defining-a-relationship-model"></a>

#### Working with relationship models <a name="working-with-relationship-models"></a>


### Relationship properties on node models <a name="relationship-properties-on-node-models"></a>

#### Defining connections between node models <a name="defining-connections-between-node-models"></a>

#### Working with relationship properties on node models <a name="working-with-relationship-properties-on-node-models"></a>


### Database client <a name="database-client"></a>

#### Connecting to a database instance <a name="connecting-to-a-database-instance"></a>

#### Closing an existing connection <a name="closing-an-existing-connection"></a>

#### Registering node and relationship models <a name="registering-node-and-relationship-models"></a>

#### Executing Cypher queries <a name="executing-cypher-queries"></a>

#### Batching cypher queries <a name="batching-cypher-queries"></a>

#### Working with indexes and constraints <a name="working-with-indexes-and-constraints"></a>


### Filter API <a name="filter-api"></a>

#### Basic filters <a name="basic-filters"></a>

#### Pattern matching <a name="pattern-matching"></a>

#### Multi-hop filters <a name="multi-hop-filters"></a>


### Extended functionality of models <a name="extended-functionality-of-models"></a>

#### Importing/Exporting models from/to dictionaries <a name="importing-exporting-models-from-to-dictionaries"></a>

#### Model hooks <a name="model-hooks"></a>
