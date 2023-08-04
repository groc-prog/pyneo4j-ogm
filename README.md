# Neo4j Object Graph Mapper

A asynchronous wrapper library around **Neo4j's python driver** which provides a **structured and easy** approach to working with
Neo4j databases and cypher queries. This library makes heavy use of `pydantic's models` and validation capabilities.



## ⚡️ Quick start <a name="quick-start"></a>

Before we can interact with the database, we have to do 3 simple things:

- Connect our client to our database
- Define our data structures with `NodeModels and RelationshipModels`
- Register our models with the client (Can be skipped, which brings some drawbacks, more talked about in
  [`Database client`](#database-client))

<br />


Before you can interact with the database in any way, you have to open a connection. This can be achieved by initializing
the `Neo4jClient` class and calling the `Neo4jClient.connect()` method.

```python
from neo4j_ogm import Neo4jClient

my_client = Neo4jClient()
my_client.connect(uri="uri-to-your-database", auth=("your-username", "your-password"))

# It is also possible to chain the connect method when creating the client instance
my_client = Neo4jClient().connect(uri="uri-to-your-database", auth=("your-username", "your-password"))
```
<br />


After we have established a connection to our database, we can start to model our data. Neo4j stores data in the form of
`nodes and relationships`. With neo4j-ogm, you mimic this approach by defining you nodes, relationships and the connections
between them as `database models`. The attributes of the models reflect the properties of the nodes and relationships in
the database. Additionally, you can define `Settings` for your models, more about that in the [`Defining node settings`](#node-settings)
and [`Defining relationship settings`](#relationship-settings) sections.

```python
from neo4j_ogm import NodeModel, RelationshipModel, RelationshipDirection, RelationshipProperty
from datetime import datetime
from uuid import UUID


# A class representing a relationship in the database
class Implemented(RelationshipModel):
  id: UUID
  production_down: bool

  class Settings:
    type = "JUST_IMPLEMENTED"


# Classes representing nodes in the database
class Bug(NodeModel):
  created_at: datetime

  class Settings:
    labels = "Bug"


class Developer(NodeModel):
  name: str
  age: int

  caused_bugs = RelationshipProperty(
    target_model=Bug,
    relationship_model=Implemented,
    direction=RelationshipPropertyDirection.OUTGOING
    allow_multiple=True
  )

  class Settings:
    labels = {"Person", "Developer"}
```
<br />


Now all we have to do is register the models we defined with our client and we are ready to go. After registering the models,
the client will automatically create the necessary constraints and indexes for the models, if any are defined
(more about that in the [`Indexes and constraints`](#indexes-and-constraints) section). We can now start to query our database,
create new nodes or relationships and much more.

```python
# Registering the models with the client
async def main() -> None:
  await my_client.register_models([Developer, Bug, Implemented])

  # Create a new `Developer` instance and save it to the database
  developer = await Developer(name="John", age=21).create()

  # More fun stuff down here
  ...
```
<br />



## 📚 Documentation
The following documentation will cover all the features of neo4j-ogm and how to use them in greater detail. If you are
looking for a quick start, please refer to the [`Quick start`](#quick-start) section.


### Node models <a name="node-models"></a>
Node models are used to represent nodes in the database. They are defined by inheriting from the `NodeModel` class and
defining the properties of the node as class attributes.

#### Defining node properties <a name="node-properties"></a>
If you want to define a property for a node, you have to define it as a class attribute. The name of the attribute will
be used as the name of the property in the database. The type of the attribute will be used to validate the property
value. If the validation fails, a `ValidationError` will be raised. The following example shows how to define a node.
If this sounds familiar to you, it is because this library makes heavy use of `pydantic's BaseModel` and validation
under the hood. If you want to learn more about pydantic, please refer to the [pydantic documentation](https://docs.pydantic.dev/1.10/).

> **Note:** Since Neo4j does not support nested properties, all dictionaries and nested models will be flattened when defining them
> as properties. This means that all dictionaries and nested models will be converted to a string and stored as a string property.
> This also means that you can not define indexes or constraints on nested properties. When inflating the model, the string will be
> converted back to a dictionary or model.

```python
from neo4j_ogm import NodeModel
from pydantic import Field, validator
from uuid import uuid4, UUID


# This class represents a node in the database with the label "Developer"
# It has two properties, "name" and "age"
class Developer(NodeModel):
  id: UUID = Field(default_factory=uuid4)  # All data types supported by pydantic are supported by neo4j-ogm
  name: str
  age: int = Field(gt=0)  # You can use pydantic's Field class to define additional validation rules
  likes_his_job: bool

  # You can also define custom validators for your properties
  @validator("likes_his_job")
  def validate_likes_his_job(cls, v: bool) -> bool:
    if v is False:
      raise ValueError("Welcome to the club!")
    return v
```
<br />


> You can define whatever properties you want, but you can not use the following property names, as they are reserved for
> internal use and to prevent conflicts when exporting models:
> - `element_id`
> - `modified_properties`

<br />

#### Defining node settings <a name="node-settings"></a>
Node settings are used to define additional settings for a node model. They are defined by creating a class named
`Settings` inside the node model class and defining the settings as class attributes. The following example shows how
to define node settings. For

```python
from neo4j_ogm import NodeModel

class Developer(NodeModel):
  # Properties would go here

  class Settings:
    exclude_from_export = {"id"}
    pre_hooks = {"create": ["set_default_values"]}
    labels = {"Person", "Developer"}
```
<br />

Available node settings:

| Setting name          | Type                                         | Description                                                                                                                                |
| --------------------- | -------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| `exclude_from_export` | `Set[str]`                                   | A set of property names that should be excluded model exports (see [`Importing and exporting models`](#importing-and-exporting-models))    |
| `pre_hooks`           | `Dict[str, Union[List[Callable], Callable]]` | A dictionary of pre hooks that should be executed before a certain action (see [`Pre hooks`](#pre-hooks))                                  |
| `post_hooks`          | `Dict[str, Union[List[Callable], Callable]]` | A dictionary of post hooks that should be executed after a certain action (see [`Post hooks`](#post-hooks))                                |
| `labels`              | `Union[str, Set[str]]`                       | The labels that should be used for the node. If no labels are defined before the model is registered, the class name will be used instead. |
<br />

#### Working with model methods <a name="working-with-node-models-methods"></a>
Node models offer a variety of methods to interact with the database. In this section we will cover all of them.
> All of the following examples will use the `Developer` model defined in the [`Defining node properties`](#defining-node-properties)

#### **`Instance.create()`**
Creates a new node in the database with the values of the model instance. Here is an example
of how to use it:

```python
async def main() -> None:
  developer = Developer(
    name="John",
    age=24,
    likes_his_job=True
  )

  print(developer)  # Not yet hydrated

  await developer.create()  # New node with the defined properties on `developer` is created
  print(developer)  # You can keep using the instance like normal
```
<br />

After creating the node in the database, the instance will be marked as `alive` (This can be seen by running the above code). This means you
can now call other methods on the instance like `.delete()` or `.update()`. If you were to try the same on a instance which has not been saved to
the database, neo4j-ogm kindly reminds you of your mistake with a `InstanceNotHydrated` exception.

#### **`Instance.update()`**
Updates an existing node in the database which corresponds to your local instance. The updated values defined in the instance will overwrite any
properties in the database.

```python
async def main() -> None:
  developer = await Developer(
    name="John",
    age=24,
    likes_his_job=True
  ).create()

  # Update instance with new values
  developer.age = 27
  await developer.update()  # Updates node in database and syncs local instance
```

#### **`Instance.delete()`**
Deletes the node linked to your local instance.

```python
async def main() -> None:
  developer = await Developer(
    name="John",
    age=24,
    likes_his_job=True
  ).create()

  await developer.delete()  # Deletes node in database
```
<br />

After deleting the node in the database, the instance will be marked as `destroyed`. This means you can no longer call any methods on the instance
except for `.create()`, which will create a new node with the same properties as the instance. Still, if you were to try and call any other method
on the instance, you will get a `InstanceDestroyed` exception.

#### **`Instance.refresh()`**
Updates the local instance with the values from the database. This is useful if you want to make sure that the instance is up to date with the
database.

```python
async def main() -> None:
  developer = await Developer(
    name="John",
    age=24,
    likes_his_job=True
  ).create()

  # Something on the local instance changes (Maybe for no apparent reason)
  developer.age = 27
  await developer.refresh()

  print(developer.age)  # 24
```

#### **`Instance.find_connected_nodes()`**
Returns all nodes connected to the instance over multiple hops. The method takes a single argument, `filters`, which is a special multi-hop
filter (see [`Filters on relationships with multiple hops`](#filters-on-relationships-with-multiple-hops)). This method gives you the ability to
use the same filters as you would with other methods, but with the added benefit of being able to filter on the relationships between the nodes.

```python
async def main() -> None:
  developer = await Developer(
    name="John",
    age=24,
    likes_his_job=True
  ).create()

  # Find all company nodes that the developer works at where all relationships of type `PAYMENT` have
  # the property `pays_well` set to `True`
  developer.find_connected_nodes({
    "$minHops": 2,
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
<br />

The above example will return all company nodes that the developer works at where all relationships of type `PAYMENT` have the property `pays_well`
set to `True`. The returned value will be a list of instances of the model `Company`. For more complex examples, multiple filters for multiple relationships
can be defined.

#### **`Model.find_one()`**
Finds and returns a single node from the database. If no node is found, `None` is returned. The method takes a single argument, `filters`, which
are filters which determine which node should be returned. For more information on filters, see [`Filters`](#filters). The following example shows how to use it:

```python
async def main() -> None:
  developer = await Developer.find_one({"name": "John"})  # Return the first encountered node where the name property equals `John`

  if developer is None:
    # No developer with the name "John" was found
    ...
```

#### **`Model.find_many()`**
A similar method to `Model.find_one()`, but instead of returning a single node, it returns a list of nodes. If no nodes are found, an empty list is returned. The method takes two arguments:

- `filters`: Filters which determine which nodes should be returned. For more information on filters, see [`Filters and options`](#filters-and-options). Can be
  omitted to return all nodes.
- `options`: Options which determine how the nodes should be returned. For more information on options, see [`Filter options`](#filter-options).

```python
async def main() -> None:
  # Return the first 20 encountered nodes where the name property equals `John`
  developers = await Developer.find_many({"name": "John"}, {"limit": 20})
```

#### **`Model.update_one()`**
Updates a single node in the database. The method takes three arguments:

- `update`: The properties which should be updated on the node. Properties which are not defined in the model will be ignored.
- `filters`: Filters which determine which node should be updated. For more information on filters, see [`Filters and options`](#filters-and-options).
- `new`: Whether or not the updated node should be returned. Defaults to `False`.

```python
async def main() -> None:
  # Update the first encountered node where the name property equals `John`
  developer = await Developer.update_one({"name": "Johnny"}, {"name": "John"}, new=True)

  print(developer.name)  # Prints `Johnny` since new=True was defined
```

#### **`Model.update_many()`**
Updates multiple nodes in the database. The method takes three arguments:

- `update`: The properties which should be updated on the nodes. Properties which are not defined in the model will be ignored.
- `filters`: Filters which determine which nodes should be updated. For more information on filters, see [`Filters and options`](#filters-and-options).
- `new`: Whether or not the updated nodes should be returned. Defaults to `False`.

```python
async def main() -> None:
  # Update all encountered nodes where the name property equals `John`
  developers = await Developer.update_many({"name": "Johnny"}, {"name": "John"})

  print(type(developers)) # Prints `list`
  print(developers[0].name)  # Prints `John` since new was not defined and defaults to false
```

#### **`Model.delete_one()`**
Deletes a single node in the database. The method takes one argument:

- `filters`: Filters which determine which nodes should be deleted. For more information on filters, see [`Filters and options`](#filters-and-options).

Unlike the other methods, this method does not return a instance of the model. Instead, it returns the amount of nodes which were deleted.

```python
async def main() -> None:
  # Delete the first encountered node where the name property equals `John`
  developer_count = await Developer.delete_one({"name": "John"})

  print(developer_count) # 1
```

#### **`Model.delete_many()`**
Deletes multiple nodes in the database. The method one argument:

- `filters`: Filters which determine which nodes should be deleted. For more information on filters, see [`Filters and options`](#filters-and-options).

When deleting multiple nodes, the method returns the amount of nodes which were deleted.

```python
async def main() -> None:
  # Delete all encountered nodes where the name property equals `John`
  developer_count = await Developer.delete_many({"name": "John"})

  print(developer_count) # However many nodes were deleted
```

#### **`Model.count()`**
Returns the count of nodes matched by the filters. The method takes one argument:

- `filters`: Filters which determine which nodes are matched. For more information on filters, see [`Filters and options`](#filters-and-options).


```python
async def main() -> None:
  # Counts all encountered nodes where the name property equals `John`
  developer_count = await Developer.count({"name": "John"})

  print(developer_count) # However many nodes were deleted
```

### Relationship models <a name="relationship-models"></a>

#### Defining relationship properties <a name="relationship-properties"></a>
#### Defining relationship settings <a name="relationship-settings"></a>
#### Working with model methods <a name="working-with-relationship-models-methods"></a>


### Relationship properties <a name="relationship-properties"></a>

#### Defining connections between node models <a name="defining-connections-between-node-models"></a>
#### Relationship property settings <a name="relationship-property-settings"></a>
#### Working with connections between node models <a name="working-with-connections-between-node-models"></a>


### Filters and options <a name="filters-and-options"></a>
#### Basic filters <a name="available-filters"></a>
#### Pattern matching <a name="pattern-matching"></a>
#### Filters on relationships with multiple hops <a name="filters-on-relationships-with-multiple-hops"></a>
#### Filter options <a name="filter-options"></a>


### Hooks <a name="hooks"></a>
#### Pre hooks <a name="pre-hooks"></a>
#### Post hooks <a name="post-hooks"></a>
#### Global vs local hooks <a name="global-vs-local-hooks"></a>


### Importing and exporting models <a name="importing-and-exporting-models"></a>
#### Importing models <a name="importing-models"></a>
#### Exporting models <a name="exporting-models"></a>


### Indexes and constraints <a name="indexes-and-constraints"></a>
#### Indexes <a name="indexes"></a>
#### Constraints <a name="constraints"></a>


### Database client <a name="database-client"></a>
#### Connecting to the database <a name="connecting-to-the-database"></a>
#### Closing the connection <a name="closing-the-connection"></a>
#### Registering models <a name="registering-models"></a>
#### Running cypher queries <a name="running-cypher-queries"></a>
#### Batched queries together <a name="batched-queries-together"></a>
#### Manually creating indexes and constraints <a name="manually-creating-indexes-and-constraints"></a>
#### Drop all indexes, constraints and nodes <a name="drop-all-indexes-constraints-and-nodes"></a>
