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


You can define whatever properties you want, but you can not use the following property names, as they are reserved for
internal use and to prevent conflicts when exporting models:
- `element_id`
- `modified_properties`

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
<br />

`NodeModel.create()` - Creates a new node in the database with the values of the model instance. If the model instance

### Relationship models <a name="relationship-models"></a>

#### Defining relationship properties <a name="relationship-properties"></a>
#### Defining relationship settings <a name="relationship-settings"></a>
#### Working with model methods <a name="working-with-relationship-models-methods"></a>


### Relationship properties <a name="relationship-properties"></a>

#### Defining connections between node models <a name="defining-connections-between-node-models"></a>
#### Relationship property settings <a name="relationship-property-settings"></a>
#### Working with connections between node models <a name="working-with-connections-between-node-models"></a>


### Filtering <a name="filtering"></a>
#### Basic filters <a name="available-filters"></a>
#### Pattern matching <a name="pattern-matching"></a>
#### Filters on relationships with multiple hops <a name="filters-on-relationships-with-multiple-hops"></a>


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
