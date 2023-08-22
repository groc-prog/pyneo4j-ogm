# Neo4j Object Graph Mapper
A asynchronous library for working with Neo4j and Python 3.10+. The aim of this library is to provide a **clean and structured** way to work with Neo4j in Python. It is built on top of the [`Neo4j Python Driver`](https://neo4j.com/docs/api/python-driver/current/index.html) and [`pydantic 1.10`](https://docs.pydantic.dev/1.10/).


## 📌 Todo's and features for future updates

### Todo's
- [ ] Unit tests to ensure future updates don't break anything
- [ ] Add release workflow to automatically publish new releases to PyPI
- [ ] Add projections and auto_fetch_nodes to documentation
- [ ] Add extensive examples to documentation


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
  - [📌 Todo's and features for future updates](#-todos-and-features-for-future-updates)
    - [Todo's](#todos)
  - [⚡️ Quick start ](#️-quick-start-)
  - [📚 Documentation ](#-documentation-)
    - [Table of contents ](#table-of-contents-)
    - [Basic concepts ](#basic-concepts-)
    - [Database client ](#database-client-)
      - [Connecting to a database instance ](#connecting-to-a-database-instance-)
      - [Closing an existing connection ](#closing-an-existing-connection-)
      - [Registering models ](#registering-models-)
      - [Executing Cypher queries ](#executing-cypher-queries-)
      - [Batching cypher queries ](#batching-cypher-queries-)
      - [Custom indexing and constraints ](#custom-indexing-and-constraints-)
      - [Client utilities ](#client-utilities-)
    - [Model configuration ](#model-configuration-)
      - [Defining node and relationship properties ](#defining-node-and-relationship-properties-)
      - [Defining indexes and constraints on model properties ](#defining-indexes-and-constraints-on-model-properties-)
      - [Defining settings for a model ](#defining-settings-for-a-model-)
        - [NodeModel specific settings ](#nodemodel-specific-settings-)
        - [RelationshipModel specific settings ](#relationshipmodel-specific-settings-)
      - [Model methods ](#model-methods-)
        - [Instance.update()](#instanceupdate)
        - [Instance.delete()](#instancedelete)
        - [Instance.refresh()](#instancerefresh)
        - [Model.find\_one()](#modelfind_one)
        - [Model.find\_many()](#modelfind_many)
        - [Model.update\_one()](#modelupdate_one)
        - [Model.update\_many()](#modelupdate_many)
        - [Model.delete\_one()](#modeldelete_one)
        - [Model.delete\_many()](#modeldelete_many)
        - [Model.count()](#modelcount)
    - [Relationship models ](#relationship-models-)
      - [Working with relationship models ](#working-with-relationship-models-)
        - [Instance.start\_node()](#instancestart_node)
        - [Instance.end\_node()](#instanceend_node)
    - [Node models ](#node-models-)
      - [Working with node models ](#working-with-node-models-)
        - [Instance.create()](#instancecreate)
        - [Instance.find\_connected\_nodes()](#instancefind_connected_nodes)
        - [Additional argument for Model.find\_one() and Model.find\_many()](#additional-argument-for-modelfind_one-and-modelfind_many)
    - [Relationship properties on node models ](#relationship-properties-on-node-models-)
      - [Working with relationship properties ](#working-with-relationship-properties-)
        - [Property.relationship()](#propertyrelationship)
        - [Property.connect()](#propertyconnect)
        - [Property.disconnect()](#propertydisconnect)
        - [Property.disconnect\_all()](#propertydisconnect_all)
        - [Property.replace()](#propertyreplace)
        - [Property.find\_connected\_nodes()](#propertyfind_connected_nodes)
    - [Filtering queries ](#filtering-queries-)
      - [Basic filters ](#basic-filters-)
      - [Pattern matching ](#pattern-matching-)
      - [Multi-hop filters ](#multi-hop-filters-)
      - [Query options to modify results ](#query-options-to-modify-results-)
    - [Extended functionality of models ](#extended-functionality-of-models-)
      - [Importing/Exporting models ](#importingexporting-models-)
      - [Model hooks ](#model-hooks-)


### Basic concepts <a name="basic-concepts"></a>
If you have worked with other ORM's like `sqlalchemy` or `beanie` before, you will find that this library is very similar to them. The main idea behind neo4j-ogm is to work with nodes and relationships in a **structured and easy-to-use** way instead of writing out complex cypher queries and tons of boilerplate for simple operations.

The concept of the library builds on the idea of defining nodes and relationships present in the graph database as **Python classes**. This allows for easy and structured access to the data in the database. These classes provide a robust foundation for working with a Neo4j database. On top of that, the library provides additional features like a `custom query filters` and `automatic model resolution from queries` out of the box. All of this is done in a **asynchronous** way using the asynchronous driver provided by Neo4j.

In the following sections we will take a look at all of the features of this library and how to use them.

> **Note:** All of the examples in this documentation assume that you have already connected to a database instance and registered your models with the client instance. The models used in the following examples will build upon the ones defined in the [`Quick start`](#quick-start) section.


### Database client <a name="database-client"></a>
The `Neo4jClient` class is the main class used to interact with the database. It is used to connect to a database instance, register models and execute queries. Under the hood, every class uses the client you connected to a database with to execute queries. It is also possible to use multiple client instances to connect to multiple databases at the same time.

#### Connecting to a database instance <a name="connecting-to-a-database-instance"></a>
Before you can interact with anything neo4j-ogm offers in any way, you have to connect to a database instance. You can do this by creating a new instance of the `Neo4jClient` class and calling the `connect()` method on it. The `connect()` method takes a few arguments:

- `uri`: The connection URI to the database instance.
- `auth`: A tuple containing the username and password for the database instance.
- `skip_constraints`: Whether the client should skip creating any constraints defined on models when registering them. Defaults to `False`.
- `skip_indexes`: Whether the client should skip creating any indexes defined on models when registering them. Defaults to `False`.
- `*args`: Additional arguments that are passed directly to Neo4j's `AsyncDriver.driver()` method.
- `**kwargs`: Additional keyword arguments that are passed directly to Neo4j's `AsyncDriver.driver()` method.

The `connect()` method returns the client instance itself, so you can chain it right after the instantiation of the class. Here is an example of how to connect to a database instance:

```python
from neo4j_ogm import Neo4jClient

client = Neo4jClient()
client.connect(uri="<connection-uri-to-database>", auth=("<username>", "<password>"), max_connection_pool_size=10, ...)

# Or chained right after the instantiation of the class
client = Neo4jClient().connect(uri="<connection-uri-to-database>", auth=("<username>", "<password>"), max_connection_pool_size=10, ...)
```

After connecting the client, you will be able to run queries against the database instance. Should you try to run a query without connecting to a database instance first, you will get a `NotConnectedToDatabase` exception.

#### Closing an existing connection <a name="closing-an-existing-connection"></a>
Once you are done working with a database instance, you can close the connection to it by calling the `close()` method on the client instance. This will close the connection to the database instance and free up any resources used by the client instance. Here is an example of how to close a connection to a database instance:

```python
# Do some work with the database instance ...

await client.close()
```

Once you closed the client, it will be seen as `disconnected` and if you try to run any further queries with it, you will get a `NotConnectedToDatabase` exception.

#### Registering models <a name="registering-models"></a>
As mentioned before, the basic concept behind neo4j-ogm is to work with models which reflect the nodes and relationships inside the graph database. In order to work with these models, you have to register them with the client instance. You can do this by calling the `register_models()` method on the client instance and passing in your models as arguments. Let's take a look at an example:

```python
# Create a new client instance and connect ...

client.register_models([Developer, Coffee, Drinks])
```

If you have defined any indexes or constraints on your models, they will be created automatically when registering them (if not disabled when the client got initialized). This is a crucial step, because if you don't register your models with the client instance, you won't be able to work with them in any way. Should you try to work with a model that is not registered with the client instance, you will get a `UnregisteredModel` exception. This exception also gets raised if a database model defines a relationship property with other (unregistered) models as a target or relationship model. For more information about relationship properties, see the [`Relationship properties on node models`](#relationship-properties-on-node-models) section.

If you don't register your models with the client, you will still be able to run cypher queries directly with the client, but you will `loose automatic model resolution` from queries. This means that you will have to manually resolve the models from the results of the queries.

#### Executing Cypher queries <a name="executing-cypher-queries"></a>
Node- and RelationshipModels provide many methods for commonly used cypher queries, but sometimes you might want to execute a custom cypher with more complex logic. For this purpose, the client instance provides a `cypher()` method that allows you to execute custom cypher queries. The `cypher()` method takes a three arguments:

- `query`: The cypher query to execute.
- `parameters`: A dictionary containing the parameters to pass to the query.
- `resolve_models`: Whether the client should try to resolve the models from the query results. Defaults to `True`.

This method will always return a tuple containing list of result lists and a list of variable names returned in the query. Internally, the client uses the `.values()` method of the Neo4j driver to get the results of the query.

> **Note:** If no models have been registered with the client and resolve_models is set to True, the client will not raise any exceptions but rather return the raw query results.

Here is an example of how to execute a custom cypher query:

```python
# Create a new client instance and connect ...

results, meta = await client.cypher(
  query="MATCH (d:Developer) WHERE d.name = $name RETURN d.name as developer_name, d.age",
  parameters={"name": "John Doe"},
  resolve_models=False, # Explicitly disable model resolution
)

print(results) # [["John Doe", 25]]
print(meta) # ["developer_name", "d.age"]
```

#### Batching cypher queries <a name="batching-cypher-queries"></a>
Since Neo4j is ACID compliant, it is possible to batch multiple cypher queries into a single transaction. This can be useful if you want to execute multiple queries at once and make sure that either all of them succeed or none of them. The client instance provides a `batch()` method that allows you to batch multiple cypher queries into a single transaction. The `batch()` has to be called with a context manager like in the following example:

```python
# Create a new client instance and connect ...
# Make sure to register models when using them!

async with client.batch():
  # All queries executed inside the context manager will be batched into a single transaction
  # and executed once the context manager exits. If any of the queries fail, the whole transaction
  # will be rolled back.
  await client.cypher(
      query="CREATE (d:Developer {name: $name, age: $age})",
      parameters={"name": "John Doe", "age": 25},
  )
  await client.cypher(
      query="CREATE (c:Coffee {name: $name})",
      parameters={"name": "Espresso"},
  )

  # Model queries also can be batched together
  coffee = await Coffee(name="Americano").create()
```

#### Custom indexing and constraints <a name="working-with-indexes-and-constraints"></a>
By default, the client will automatically create any indexes and constraints defined on models when registering them. If you want to disable this behavior, you can do so by passing the `skip_indexes` and `skip_constraints` arguments to the `connect()` method when connecting to a database instance. If you want to create custom indexes and constraints, or want to add additional indexes/constraints later on (which should probably be done on the models themselves), you can do so by calling the `create_index()` and `create_constraint()` methods on the client instance.

First, let's take a look at how to create a custom index in the database. The `create_index()` method takes a few arguments:

- `name`: The name of the index to create.
- `entity_type`: The entity type the index is created for. Can be either `EntityType.NODE` or `EntityType.RELATIONSHIP`.
- `index_type`: The type of index to create. Can be `IndexType.RANGE`, `IndexType.TEXT`, `IndexType.POINT` or `IndexType.TOKEN`.
- `properties`: A list of properties to create the index for.
- `labels_or_type`: The node labels or relationship type the index is created for.

The `create_constraint()` method also takes similar arguments as the `create_index()` method. The only difference is that it does not take a `constraint_type` argument since only `UNIQUENESS` constraints are currently supported.

- `name`: The name of the constraint to create.
- `entity_type`: The entity type the constraint is created for. Can be either `EntityType.NODE` or `EntityType.RELATIONSHIP`.
- `properties`: A list of properties to create the index for.
- `labels_or_type`: The node labels or relationship type the index is created for.

#### Client utilities <a name="client-utilities"></a>
The database client also provides a few utility methods and properties that can be useful when writing automated scripts or tests. These methods are:

- `is_connected()`: Returns whether the client is connected to a database instance.
- `drop_nodes()`: Drops all nodes from the database.
- `drop_constraints()`: Drops all constraints from the database.
- `drop_indexes()`: Drops all indexes from the database.

Additionally, transactions can be manually controlled by using the `begin_transaction()`, `commit_transaction()` and `rollback_transaction()` methods. These methods are also used internally by the client when using the `batch()` context manager.


### Model configuration <a name="model-configuration"></a>
Both Node- and RelationshipModels provide a few configuration options that can be used to define indexes, constraints and other settings for the model. These options can be used to easily define indexes and constraints on models and configure how nodes and relationships are created in the database.

Since neo4j-ogm uses `pydantic` under the hood, all of the configuration options available for pydantic models are also available for Node- and RelationshipModels. For more information about the configuration options available for pydantic models, see the [`pydantic docs`](https://docs.pydantic.dev/1.10/).

#### Defining node and relationship properties <a name="defining-node-and-relationship-properties"></a>
Node- and RelationshipModels are defined in the same way as pydantic models. The only difference is that you have to use the `NodeModel` and `RelationshipModel` classes instead of the `BaseModel` class. Here is an example of how to define a simple NodeModel:

```python
from neo4j_ogm import NodeModel
from pydantic import Field, validator
from uuid import UUID, uuid4

class Developer(NodeModel):
  """
  A model representing a developer node in the graph.
  """
  id: UUID = Field(default_factory=uuid4)
  name: str
  age: int
  likes_his_job: bool

  @validator("likes_his_job")
  def must_like_his_job(cls, v):
    if not v:
      raise ValueError("A developer must like his job!")
    return v
```

A node created with the above model would look like this as a cypher query:

```cypher
CREATE (d:Developer {id: "a1b2c3d4-e5f6-g7h8-i9j0-k1l2m3n4o5p6", name: "John Doe", age: 25, likes_his_job: true})
```

> **Note:** Everything mentioned above also applies to `RelationshipModels`.

#### Defining indexes and constraints on model properties <a name="defining-indexes-and-constraints-on-model-properties"></a>
neo4j-ogm provides a convenient way to define indexes and constraints on model properties. This can be done by using the `WithOptions` method instead of the datatype when defining the properties of your model. The `WithOptions` method takes a few arguments:

- `property_type`: The datatype of the property.
- `range_index`: Whether to create a range index on the property. Defaults to `False`.
- `text_index`: Whether to create a text index on the property. Defaults to `False`.
- `point_index`: Whether to create a point index on the property. Defaults to `False`.
- `unique`: Whether to create a uniqueness constraint on the property. Defaults to `False`.

If the method is called without defining any indexes or constraints, it behaves just like any other property. Here is an example of how to define indexes and constraints on model properties:

```python
from neo4j_ogm import NodeModel, WithOptions
from pydantic import Field
from uuid import UUID, uuid4

class Developer(NodeModel):
  """
  A model representing a developer node in the graph.
  """
  id: WithOptions(UUID, unique=True) = Field(default_factory=uuid4)
  name: WithOptions(str, text_index=True)
  age: int
  likes_his_job: bool
```

In the example above, we defined a `text index` on the `name` property and a `uniqueness constraint` on the `email` property. If you want to define multiple indexes or constraints on a single property, you can do so by passing multiple arguments to the `WithOptions` method. Note that you can still use the full power of pydantic like validators and default values when defining indexes and constraints on model properties.

> **Note:** Everything mentioned above also applies to `RelationshipModels`.

#### Defining settings for a model <a name="defining-settings-for-a-model"></a>
It is possible to define a number of settings for a model. These settings can be used to configure how nodes and relationships are created in the database and how you can interact with them. Settings are defined with a nested class called `Settings`. Class attributes act as the settings defined on the model. The following settings are available for Node- and RelationshipModels:

| Setting name          | Type                                           | Description                                                                                                                                                                                                                                                                                                                                                   |
| --------------------- | ---------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `exclude_from_export` | **Set[str]**                                   | Can be used to always exclude a property from being exported when using the `export_model()` method on a model.                                                                                                                                                                                                                                               |
| `pre_hooks`           | **Dict[str, Union[List[Callable], Callable]]** | A dictionary where the key is the name of the method for which to register the hook and the value is the hook function or a list of hook functions. The hook function can be sync or async. All hook functions receive the exact same arguments as the method they are registered for and the current model instance as the first argument. Defaults to `{}`. |
| `post_hooks`          | **Dict[str, Union[List[Callable], Callable]]** | Same as **pre_hooks**, but the hook functions are executed after the method they are registered for. Additionally, the result of the method is passed to the hook as the second argument. Defaults to `{}`.                                                                                                                                                   |

##### NodeModel specific settings <a name="nodemodel-specific-settings"></a>
NodeModels have two additional setting, `labels` and `auto_fetch_nodes`.

| Setting name       | Type         | Description                                                                                                                                                                                                                          |
| ------------------ | ------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `labels`           | **Set[str]** | A set of labels to use for the node. If no labels are defined, the name of the model will be used as the label. Defaults to `None`.                                                                                                  |
| `auto_fetch_nodes` | **bool**     | Whether to automatically fetch nodes of defined relationship properties when getting a model instance from the database. Auto-fetched nodes are available at `instance.<relationship-property>.nodes` property. Defaults to `False`. |

> **Note:** When no labels are defined for a NodeModel, the name of the model will be used and converted to **PascalCase** to stay in line with the style guide for cypher.

##### RelationshipModel specific settings <a name="relationshipmodel-specific-settings"></a>
For RelationshipModels, the `labels` setting is not available, since relationships don't have labels in Neo4j. Instead, the `type` setting can be used to define the type of the relationship. If no type is defined, the name of the model will be used as the type.

> **Note:** When no type is defined for a RelationshipModel, the name of the model will be used and converted to **SCREAMING_SNAKE_CASE** to stay in line with the style guide for cypher.

Now let's take a look at an example of how to define settings for a model:

```python
class Developer(NodeModel):
  ...

  class Settings:
    # Nodes of this model will have the labels "Developer" and "Python"
    labels = {"Developer", "Python"}
    # The "likes_his_job" property will always be excluded from being exported
    exclude_from_export = {"likes_his_job"}


def print_drink(self, result, *args, **kwargs):
  # Will print the result from the `find_one()` method
  print(result)


class Drinks(RelationshipModel):
  ...

  class Settings:
    # The type of the relationship will be "DRINKS"
    type = "DRINKS"
    # The "print_drink" method will be executed after the "find_one" method
    post_hooks = {"find_one": print_drink}
```

#### Model methods <a name="model-methods"></a>
Node- and RelationshipModels provide a number of methods for commonly used cypher queries. In the following sections we will take a look at all of the methods available on Node- and RelationshipModels.

> **Note:** All of the methods mentioned below are available on both Node- and RelationshipModels unless stated otherwise. If a method is defined using **Instance.method()**, the method is to be called on a instance if a model. If a method is defined using **Model.method()**, the method is to be called on the model itself.

##### Instance.update()
The `update()` method can be used to update the relationship tied to the current model instance with the current values of the instance. This method takes no arguments and returns nothing.

```python
developer = await Developer(
  name="John",
  age=24,
  likes_his_job=True
).create()

# Update instance with new values
developer.age = 27
await developer.update()  # Updates node in database and syncs local instance
```

##### Instance.delete()
The `delete()` method can be used to delete the relationship tied to the current model instance. This method takes no arguments and returns nothing. Once deleted, the model instance will be marked as `destroyed` and any further operations on it will raise a `InstanceDestroyed` exception.

```python
developer = await Developer(
  name="John",
  age=24,
  likes_his_job=True
).create()

await developer.delete()  # Deletes node in database, instance is now seen as `destroyed`
```

##### Instance.refresh()
Refreshes the current instance with the latest data from the database. Can be useful if you want to sync your local instance with the graph or to reset the instance to it's original properties. This method takes no arguments and returns nothing.

```python
developer = await Developer(
  name="John",
  age=24,
  likes_his_job=True
).create()

# Something on the local instance changes
developer.age = 27
print(developer.age)  # 27

await developer.refresh()

print(developer.age)  # 24
```

##### Model.find_one()
The `find_one()` method can be used to find a single node or relationship in the graph. If multiple results are matched, the first one is returned. This method takes a mandatory `filters` argument, which can be used to filter the results. For more about filters, see the [`Filtering queries`](#filtering-queries) section. This method returns a single instance of the model or `None` if no results were found.

```python
developer = await Developer.find_one({"name": "John"})  # Return the first encountered node where the name property equals `John`

if developer is None:
  # No developer with the name "John" was found
  ...
```

##### Model.find_many()
This method is similar to the `find_one()` method, but returns a list of all results matched by the query. This method takes a two argument:

- `filters`: The filters to use for the query. Can be omitted to match all results. Defaults to `None`.
- `options`: Options to modify the query results. Useful for pagination and sorting. Defaults to `None`. For more information about the options available, see the [`Query options to modify results`](#query-options-to-modify-results) section.

```python
# Return the first 20 encountered nodes where the name property equals `John`
developers = await Developer.find_many({"name": "John"}, {"limit": 20})
```

##### Model.update_one()
Updates the first encountered node or relationship matched by the query and updates it with the defined properties. This method takes three arguments:

- `update`: A dictionary containing the properties to update. Must be defined.
- `filters`: The filters to use for the query. Must be defined.
- `new`: Whether to return the updated instance or the old instance. Defaults to `False`.

If no match is found, `None` is returned instead.

```python
# Update the first encountered node where the name property equals `John`
developer = await Developer.update_one({"name": "Johnny"}, {"name": "John"}, new=True)

print(developer.name)  # Prints `Johnny` since new=True was defined
```

##### Model.update_many()
Updates all nodes or relationships matched by the query and updates them with the defined properties. This method takes three arguments:

- `update`: A dictionary containing the properties to update. Must be defined.
- `filters`: The filters to use for the query. If omitted, updates all nodes or relationships in the graph. Defaults to `None`.
- `new`: Whether to return the updated instances or the old instances. Defaults to `False`.

If no match is found, a empty list is returned.

```python
# Update all encountered nodes where the name property equals `John`
developers = await Developer.update_many({"name": "Johnny"}, {"name": "John"})

print(type(developers)) # Prints `list`
print(developers[0].name)  # Prints `John` since new was not defined and defaults to false
```

##### Model.delete_one()
Deletes the first encountered node or relationship matched by the query. This method takes a single argument:

- `filters`: The filters to use for the query. Must be defined.

Unlike the other methods, this one does not return a instance of the deleted node or relationship. Instead, it returns the number of nodes or relationships deleted, which will always be 1 (If a match was found) or 0 (If no match was found).

```python
# Delete the first encountered node where the name property equals `John`
developer_count = await Developer.delete_one({"name": "John"})

print(developer_count) # 1
```

##### Model.delete_many()
Deletes all nodes or relationships matched by the query. This method takes a single argument:

- `filters`: The filters to use for the query. If omitted, deletes all nodes or relationships in the graph. Defaults to `None`.

Like the `delete_one()` method, this method also returns the number of nodes or relationships deleted.

```python
# Delete all encountered nodes where the name property equals `John`
developer_count = await Developer.delete_many({"name": "John"})

print(developer_count) # However many nodes were deleted
```

##### Model.count()
Counts the number of nodes or relationships matched by the query. This method takes a single argument:

- `filters`: The filters to use for the query. If omitted, counts all nodes or relationships in the graph. Defaults to `None`.

This method returns the number of nodes or relationships matched by the query.

```python
# Counts all encountered nodes where the name property equals `John`
developer_count = await Developer.count({"name": "John"})

print(developer_count) # However many nodes were counted
```


### Relationship models <a name="relationship-models"></a>
RelationshipModels are used to define relationships between nodes in the graph. They are defined in the same way as NodeModels, but inherit from the `RelationshipModel` class instead of the `NodeModel` class. Let's take a look at an example of how to define a simple RelationshipModel:

```python
from neo4j_ogm import RelationshipModel


class Drinks(RelationshipModel):
  """
  A model representing a DRINKS relationship between a developer and a coffee node.
  """
  likes_it: bool
```

#### Working with relationship models <a name="relationship-models-specific-methods"></a>
RelationshipModels provide a few additional methods for working with relationships. Let's take a look at all of the methods available on RelationshipModels.

##### Instance.start_node()
Returns the start node of the relationship tied to the current model instance. This method takes no arguments and returns a instance of the start node, resolved to the correct model.

```python
# `drinks` represents a relationship between a `Developer` and a `Coffee`
# with the direction `OUTGOING`
developer = await drinks.start_node()

print(developer) # An hydrated instance of the `Developer` model
```

##### Instance.end_node()
Returns the end node of the relationship tied to the current model instance. This method takes no arguments and returns a instance of the end node, resolved to the correct model.

```python
# `drinks` represents a relationship between a `Developer` and a `Coffee`
# with the direction `OUTGOING`
coffee = await drinks.start_node()

print(coffee) # An hydrated instance of the `Coffee` model
```


### Node models <a name="node-models"></a>
To define a node inside the graph, we have to create a new class that inherits from the `NodeModel` class. Let's take a look at an example of how to define a simple NodeModel:

```python
from neo4j_ogm import NodeModel
from pydantic import Field
from uuid import UUID, uuid4

class Developer(NodeModel):
  """
  A model representing a developer node in the graph.
  """
  id: UUID = Field(default_factory=uuid4)
  name: str
  age: int
```

#### Working with node models <a name="node-models-specific-methods"></a>
Like RelationshipModels, NodeModels also provide a few additional methods for working with nodes. Let's take a look at all of the methods available on NodeModels.

##### Instance.create()
Creates a new node in the graph with the properties defined on the current model instance. This method takes no arguments and returns nothing. After the method is done, the instance is seen as `alive`, which enables you to call all other methods on it. If you try to call any methods on a instance which has not been hydrated, you will receive a `InstanceNotHydrated` exception.

```python
developer = Developer(
  name="John",
  age=24,
  likes_his_job=True
)

# Not yet hydrated, we get a `InstanceNotHydrated` exception if we try to call methods
# like `update()` or `delete()`
print(developer)

await developer.create()  # New node with the defined properties on `developer` is created
print(developer)  # You can keep using the instance like normal
```

##### Instance.find_connected_nodes()
This method allows you to query nodes connected to the current model over multiple hops. For this, the method takes a special `multi-hop filter` (see [`Multi-hop filters`](#multi-hop-filters)). The method takes two arguments:

- `filters`: A special multi-hop filter which allows you to define filters in the end node and the relationships between them. Defaults to `None`.
- `options`: Options to modify the query results. Useful for pagination and sorting. Defaults to `None`. For more information about the options available, see the [`Query options to modify results`](#query-options-to-modify-results) section.

This method returns a list of all nodes matched by the query.

```python
# Find all company nodes that the developer works at where all relationships of type `PAYMENT` have
# the property `pays_well` set to `True`. The query will be executed over a maximum of 7 hops.
developer.find_connected_nodes({
  "$maxHops": 7,
  "$relationships": [
    {
      "$type": "PAYMENT",
      "pays_well": True
    }
  ],
  "$node": {
    "$labels": ["Company"],
  }
})
```

##### Additional argument for Model.find_one() and Model.find_many()
Node models support an additional argument for the `find_one()` and `find_many()` methods. This argument is called `auto_fetch_nodes` and can be used to automatically fetch nodes of defined relationship properties when getting a model instance from the database. This argument defaults to `False`. If `auto_fetch_nodes` is enabled in the models settings, this argument will be ignored and the nodes will be fetched automatically.

```python
developer = await Developer.find_one({"name": "John"})

if developer is None:
  # No developer with the name "John" was found
  ...

# Coffee drank by the developer will be fetched automatically and can be
# accessed at `developer.coffee.nodes`
print(developer.coffee.nodes) # A list of hydrated `Coffee` instances
```


### Relationship properties on node models <a name="relationship-properties-on-node-models"></a>
To define relationships between node models, RelationshipProperties can be used. RelationshipProperties are defined as a special type of pydantic property. They can be used to define relationships between node models and provide a convenient way to work with them. Let's take a look at an example of how to define a RelationshipProperty:

```python
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

  # Here we define a relationship property called "coffee" which defines a relationship
  # between a developer and a coffee node.
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

RelationshipProperties take a few arguments:

- `target_model`: The target model of the relationship (The node to which the relationship connects). Can be either a string or a reference to the model itself.
- `relationship_model`: The relationship model to use for the relationship. Can be either a string or a reference to the model itself.
- `direction`: The direction of the relationship. Can be either `RelationshipPropertyDirection.OUTGOING` or `RelationshipPropertyDirection.INCOMING`. Defaults to `RelationshipPropertyDirection.OUTGOING`.
- `cardinality`: The cardinality of the relationship. Can be either `RelationshipPropertyCardinality.ONE` or `RelationshipPropertyCardinality.ZERO_OR_MORE`. Defaults to `RelationshipPropertyCardinality.ONE`. This allows you to (softly) enforce cardinality constraints on relationships.
- `allow_multiple`: Whether to allow multiple relationships between the same nodes. By default, only one relationship between the same nodes is allowed. Defaults to `False`.

> **Note:** If you define the target_model or relationship_model as a string, you can pass the class to the RelationshipProperty as a generic. This allows you to still use type hints for the RelationshipProperty.

#### Working with relationship properties <a name="working-with-relationship-properties-on-node-models"></a>
RelationshipProperties provide a few methods for working with relationships. Let's take a look at all of the methods available on RelationshipProperties.

##### Property.relationship()
Returns the relationship between the current model instance and a target model passed to the method. If no relationship is found, `None` is returned. This method takes a single argument:

- `node`: The target node to get the relationship to.

```python
# `developer` and `project` are instances of the `Developer` and `Project` models
# respectively, defined somewhere else
worked_on = await developer.projects.relationship(project)

if worked_on is not None:
  # Developer did not work on the project
  ...

# Do something with the relationship
...
```

The returned relationship is a instance of the relationship model defined on the RelationshipProperty. This means that you can use all methods available on RelationshipModels on the returned relationship.

```python
worked_on = await developer.projects.relationship(project)

if worked_on is not None:
  if worked_on.implemented_many_bugs:
    # Developer implemented many bugs in the project
    ...
  else:
    # Developer did not implemented many bugs in the project
    ...
```

##### Property.connect()
Creates a new relationship between the current model instance and a target model passed to the method. This method takes a two argument:

- `node`: The target node to connect to.
- `properties`: A dictionary containing the properties to set on the relationship. Defaults to `{}`.

```python
worked_on = await developer.projects.connect(project, {"implemented_many_bugs": True})

print(worked_on) # An hydrated instance of the `WorkedOn` model
```

> **Note:** The provided properties are validated against the relationship model. Make sure to define all required properties on the relationship model or you will get a `ValidationError`.

##### Property.disconnect()
Deletes the relationship between the current model instance and a target model passed to the method. Like the `delete_one()` and `delete_many()` methods, this method also returns the number of relationships deleted. This method takes a single argument:

- `node`: The target node to disconnect from.

```python
# The developer does no longer work on the project after the next line
worked_on_count = await developer.projects.disconnect(project)

print(worked_on_count) # 1
```

> **Note:** If multiple relationships between the same nodes exist, all of them will be deleted.

##### Property.disconnect_all()
Deletes all relationships between the current model instance and all target nodes found with a connection to the current model instance. Like the `delete_one()` and `delete_many()` methods, this method also returns the number of relationships deleted. This method takes no arguments.

```python
# The developer does no longer work on any project after the next line
worked_on_count = await developer.projects.disconnect_all()

print(worked_on_count) # However many relationships were deleted
```

##### Property.replace()
Replaces the relationship and all of it's properties between the current model instance and a target model with a identical relationship to another node. This method takes a two argument:

- `old_node`: The node the current model is connected to.
- `new_node`: The node to replace the old node with.

After the method successfully finished, the new relationship will be returned. If the `old_node is not connected` to the current model, a `NotConnectedToSourceNode` exception will be raised. If the `new_node is already connected` to the current model and allow_multiple is set to `False`, The old relationship will be deleted and replaced by the new one. If `allow_multiple` is set to `True`, the new relationship will be created in addition to the old one.

```python
# Instances defined somewhere else
developer = ...
old_project = ...
new_project = ...

worked_on_old = await developer.projects.relationship(old_project)
print(worked_on_old.implemented_many_bugs) # True

worked_on_new = await developer.projects.replace(old_project, new_project)

# Relationship holds the same properties as the old relationship
print(worked_on_new.implemented_many_bugs) # True
```

##### Property.find_connected_nodes()
Finds all nodes connected to the current model instance over the relationship property. This method takes a two argument:

- `filters`: A special relationship-property filter which allows you to define filters in the end node and the relationship between them. Defaults to `None`.
- `options`: Options to modify the query results. Useful for pagination and sorting. Defaults to `None`. For more information about the options available, see the [`Query options to modify results`](#query-options-to-modify-results) section.


### Filtering queries <a name="filtering-queries"></a>
As you have seen in the previous examples, many methods accept filters and options as arguments. Filters are used to filter the results of the query, while options are used to modify the query results. Both filters and options are defined as dictionaries. The following sections will explain how to use filters and options.

#### Basic filters <a name="basic-filters"></a>
Basic filters are the building blocks of more complex filters. They are used to filter nodes and relationships based on their properties. There is a number of basic filters that can be used to filter nodes and relationships. If you used **MongoDB's query language** before, you will find these filters very familiar. The following table lists all basic filters and their usage:

| Comparison operators | Description                                                                                                                                | Example                                    |
| -------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------ |
| `$eq`                | Matches any property where the value is equal to a specified value. If a filter specifies no operator, neo4j-ogm will assume a this filter | `{ "name": { "$eq": "John" } }`            |
| `$neq`               | Matches any property where the value is not equal to a specified value                                                                     | `{ "name": { "$neq": "John" } }`           |
| `$gt`                | Matches any property where the value is greater than a specified value                                                                     | `{ "age": { "$gt": 18 } }`                 |
| `$gte`               | Matches any property where the value is greater than or equal to a specified value                                                         | `{ "age": { "$gte": 18 } }`                |
| `$lt`                | Matches any property where the value is less than a specified value                                                                        | `{ "age": { "$lt": 18 } }`                 |
| `$lte`               | Matches any property where the value is less than or equal to a specified value                                                            | `{ "age": { "$lte": 18 } }`                |
| `$in`                | Matches any property where the value is in the list of given values                                                                        | `{ "name": { "$in": ["John", "Jane"] } }`  |
| `$nin`               | Matches any property where the value is not in the list of given values                                                                    | `{ "name": { "$nin": ["John", "Jane"] } }` |

<br />

| String operators | Description                                                                                                            | Example                               |
| ---------------- | ---------------------------------------------------------------------------------------------------------------------- | ------------------------------------- |
| `$contains`      | Matches any property where the value contains the given substring                                                      | `{ "name": { "$contains": "ohn" } }`  |
| `$icontains`     | Matches any property where the value contains the given substring (case-insensitive)                                   | `{ "name": { "$icontains": "oHn" } }` |
| `$startsWith`    | Matches any property where the value starts with the given substring                                                   | `{ "name": { "$startsWith": "J" } }`  |
| `$istartsWith`   | Matches any property where the value starts with the given substring (case-insensitive)                                | `{ "name": { "$istartsWith": "j" } }` |
| `$endsWith`      | Matches any property where the value ends with the given substring                                                     | `{ "name": { "$endsWith": "n" } }`    |
| `$iendsWith`     | Matches any property where the value ends with the given substring (case-insensitive)                                  | `{ "name": { "$iendsWith": "N" } }`   |
| `$regex`         | Matches any property where the value matches the given regular expression (Uses the same regular expressions as Neo4j) | `{ "name": { "$regex": "Jo.*" } }`    |

<br />

| List operators | Description                                                                                                                                              | Example                                                                              |
| -------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------ |
| `$all`         | Matches any property where the value contains all of the given values                                                                                    | `{ "projects": { "$all": ["neo4j-ogm", "buy-me-coffee"] } }`                         |
| `$size`        | Matches any property where the value is an array of a given size. This operator can be combined with other numeric operators for more specific filtering | `{ "projects": { "$size": 2 } }` <br /> `{ "projects": { "$size": { "$gte": 2 } } }` |

<br />

| Logical operators | Description                                                                                                                   | Example                                                                                              |
| ----------------- | ----------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| `$not`            | Add a logical **NOT** to the operator it wraps, can be used with all basic operators                                          | `{ "age": { "$not": { "$gt": 12 } }`                                                                 |
| `$and`            | Combines multiple operators with a logical **AND**. Falls back to this if multiple operators are defined on a single property | `{ "age": { "$and": [{ "$gt": 12 }, { "$lte": 32 }] }` <br /> `{ "age": { "$gt": 12, "$lte": 32 } }` |
| `$or`             | Combines multiple operators with a logical **OR**                                                                             | `{ "age": { "$or": [{ "$gt": 12 }, { "$lte": 32 }] }`                                                |
| `$xor`            | Combines multiple operators with a logical **XOR**                                                                            | `{ "age": { "$xor": [{ "$gt": 12 }, { "$lte": 32 }] }`                                               |

<br />

| Element operators | Description                                                                                         | Example                                                                     |
| ----------------- | --------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------- |
| `$exists`         | Matches all nodes or relationships where the property exists. Useful for models with dynamic fields | `{ "name": { "$exists": True } }`                                           |
| `$elementId`      | Matches the node or relationship with the provided element-id                                       | `{ "$elementId": "4:704eea2c-3c2c-42a7-a774-8fb962a93f38:0" }`              |
| `$id`             | Matches the node or relationship with the provided id                                               | `{ "$id": 1 }`                                                              |
| `$labels`         | Matches all nodes with the given label(s). Only available for node filters                          | `{ "$labels": "Developer" }`<br /> `{ "$labels": ["Developer", "Senior"] }` |
| `$type`           | Matches all relationships with the given type. Only available for relationship filters              | `{ "$type": "IMPLEMENTED" }`                                                |

<br />

| Node and relationship operators | Description                                                                                                  | Example                                                  |
| ------------------------------- | ------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------- |
| `$relationship`                 | Specific to **RelationshipProperty.find_connected_nodes()**, allows filtering on a relationship's properties | `{ "$relationship": { "implemented_many_bugs": True } }` | ` |


#### Pattern matching <a name="pattern-matching"></a>
Sometimes just filtering nodes based on their properties is not enough, or sometimes we might want to exclude nodes with connections to specific nodes with a specific relationship. In this case you can use the `$patterns` operator. Pattern filters allow you to specify a pattern of nodes and relationships that must be met in order for the node to be matched. This is useful for filtering on nodes based on their relationships to other nodes.

Pattern filters are specified as a list of dictionaries, where each dictionary represents a pattern. Each pattern can specify the following keys:

- `$node`: Filters applied to the target node. Expects a dictionary containing basic filters.
- `$relationship`: Filters applied to the relationship between the source node and the target node. Expects a dictionary containing basic filters.
- `$direction`: The direction of the pattern. Can be either **INCOMING**,**OUTGOING** or **BOTH**.
- `$not`: A boolean value indicating whether the pattern should be negated. Defaults to **False**.

To make the power of this feature clear, let's look at an example. Let's say we want to find all developers who have worked on the neo4j-ogm project and have not implemented many bugs. Additionally, we want to exclude developers who drink coffee. We can do this by specifying the following pattern:

```python
developer = await Developer.find_one({
  "$patterns": [
    {
      "$node": {
        "$labels": ["Project"],
        "$properties": {
          "name": "neo4j-ogm"
        }
      },
      "$relationship": {
        "$type": "WORKED_ON",
        "implemented_many_bugs": False
      },
      "$direction": "OUTGOING"
    },
    {
      "$node": {
        "$labels": ["Coffee"]
      },
      "$relationship": {
        "$type": "DRINKS"
      },
      "$direction": "INCOMING",
      "$not": True
    }
  ]
})
```

> ❗️ **Note:** Patterns are not available when filtering relationships

#### Multi-hop filters <a name="multi-hop-filters"></a>
Multi-hop filters are a special type of filter only available for `Instance.find_connected_nodes()`. It allows you to specify filter parameters on the target node and **all** relationships between them. To define this filter, you have a few operators you can define:

- `$node`: Filters applied to the target node. Expects a dictionary containing basic filters. Can not contain pattern **yet**.
- `$minHops`: The minimum number of hops between the source node and the target node. Must be greater than **0**.
- `$maxHops`: The maximum number of hops between the source node and the target node. You can pass `"*"` as a value to define no upper limit. Must be greater than **1**.
- `$relationships`: A list of relationship filters. Each filter is a dictionary containing basic filters and **must** define a `$type` operator.

You guessed it, we shall do an example once more! Let's say we want to find all projects for a given coffee type where the developers who drank the coffee liked it and have not implement many bugs on the project. We can do this by specifying the following filter:

```python
# Assume coffee instance has been defined above
projects = await coffee.find_connected_nodes({
  "$node": {
    "$labels": ["Project"]
  },
  "$maxHops": "*",
  "$relationships": [
    {
      "$type": "WORKED_ON",
      "implemented_many_bugs": False
    },
    {
      "$type": "IS_CRITICIZED_BY",
      "liked": True
    }
  ]
})
```

#### Query options to modify results <a name="query-options-to-modify-results"></a>
As you may have seen by now, some methods allow you to define options which change the way results are returned. Methods who implement these options are usually ones that return multiple results, such as `NodeModel.find_many()`, `RelationshipModel.find_many()` and so on. The following options are available:

- `limit`: Limits the number of results returned. Must be greater than **0**.
- `skip`: Skips the first `n` results. Must be greater than or equal to **0**.
- `sort`: Sorts the results based on the given properties in combination with the defined `order`. Can be a single property name or a list of property names.
- `order`: How the results are ordered. Can be either **ASCENDING** or **DESCENDING**. Defaults to **ASCENDING**.

With these options, you can do things like pagination, sorting and so on.


### Extended functionality of models <a name="extended-functionality-of-models"></a>
Models provide a few additional features that can be used to extend their functionality. Let's take a look at all of the extended functionality available on models.

#### Importing/Exporting models <a name="importing-exporting-models"></a>
If you are working with something like `gRPC`, a `RestAPI` or anything else which needs to serialize our data in some way, we might run into the problem of having to manually handle the serialization for custom data types or data types like UUID, which are often not supported in the named use cases. To solve this problem, we can use the `import_model()` and `export_model()` methods on models. These methods allow us to import and export models to and from dictionaries. Let's take a look at an example:

```python
# Assume developer instance has been defined above. Our developer instance has a
# UUID as a property, which is not supported by gRPC. We can easily export the
# developer instance to a dictionary and then serialize it with gRPC.
developer_dict = developer.export_model(exclude={"meta"}) # Takes the same arguments as `pydantic.BaseModel.dict()`

# Parse your dict to a gRPC message
developer_message = ParseDict(developer_dict, DeveloperMessage())
```

This allows us to easily serialize our models to dictionaries and then parse them to gRPC messages or JSON objects. We can also import models from dictionaries. This is useful if we want to deserialize a gRPC message or JSON object to a model. Let's take a look at an example:

```python
# Assume developer_message has been received as a gRPC message. We can easily parse
# it to a dictionary and then import it as a model.
developer_dict = MessageToDict(developer_message)
developer = Developer.import_model(developer_dict) # `developer` is now a hydrated instance of the `Developer` model
```

By default, a `element_id` field is exported with every model. This way, once you import the model again, it will be seen as hydrated and you can directly work with it. Although this may seem convenient, it can still be a problem if the node is deleted in the graph in the meantime. To prevent this, you can just try to call `.refresh()` to sync the instance with the graph. If the node was deleted, a `NoResultsFound` exception will be raised.

If you are not using something like gRPC, which supports casing transformations, you can also convert your model's properties to and from snake_case and camelCase. This can be useful if you are working with a RestAPI and want to keep the casing for your JSON as it should be per definition. Let's take a look at an example:

```python
# Assume developer instance has been defined above. We can easily export the
# developer instance to a dictionary and then convert it to snake_case.
developer_dict = developer.export_model(convert_to_camel_case=True)

print(developer_dict) # {"name": "John", "age": 24, "likesHisJob": True, "elementId": "4:704eea2c-3c2c-42a7-a774-8fb962a93f38:0"}

# We can also import the dictionary as a model and convert it to snake_case
developer = Developer.import_model(developer_dict, convert_to_snake_case=True)

print(dict(developer)) # {"name": "John", "age": 24, "likes_his_job": True}
```

#### Model hooks <a name="model-hooks"></a>
Model hooks allow you to define functions that are called at specific points in the models lifecycle. This can be useful if you want to do something before or after a model is created, updated or deleted. Let's take a look at an example:

```python
def on_create(model, *args, **kwargs):
  print(f"Model {model._element_id} was created")

class Developer():
  ...

  class Settings:
    post_hooks = {"create": on_create}
```

The above code will print `Model <element-id-of-node> was created` every time a developer is created.

If a hooks is defined like above, it will be called whenever a new model is created, regardless if it was used in completely different applications. But there are some use-cases, for ea
