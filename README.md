# Neo4j Object Graph Mapper

A asynchronous wrapper library around **Neo4j's python driver** which provides a **structured and easy** approach to working with
Neo4j databases and cypher queries. This library makes heavy use of `pydantic's models` and validation capabilities.



## ⚡️ Quick start

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
`Nodes and Relationships`. With neo4j-ogm, you mimic this approach by defining you nodes, relationships and the connections
between them as `database models`.

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
the client will automatically create the necessary constraints and indexes for the models. We can now start to query our database,
create new nodes and relationships and much more.

```python
# Registering the models with the client
async def main() -> None:
  await my_client.register_models([Developer, Bug, Implemented])

  # Create a new `Developer` instance and save it to the database
  developer = await Developer(name="John", age=21).create()
```
<br />



## 📚 Documentation

### Node models <a name="node-models"></a>

### Relationship models <a name="relationship-models"></a>

### Relationship properties <a name="relationship-properties"></a>

### Filtering <a name="filtering"></a>

### Hooks <a name="hooks"></a>

### Importing and exporting models <a name="importing-and-exporting-models"></a>

### Indexes and constraints <a name="indexes-and-constraints"></a>

### Database client <a name="database-client"></a>
