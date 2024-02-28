## Models

As shown in the [`quickstart guide`](https://github.com/groc-prog/pyneo4j-ogm/blob/develop?tab=readme-ov-file#quickstart), models are the main building blocks of `pyneo4j-ogm`. They represent the nodes and relationships inside the graph and provide a lot of useful methods for interacting with them.

A core mechanic of `pyneo4j-ogm` is serialization and deserialization of models. Every model method uses this mechanic under the hood to convert the models to and from the format used by the Neo4j driver.

This is necessary because the Neo4j driver can only handle certain data types, which means models with custom or complex data types have to be serialized before they can be saved to the database. Additionally, Neo4j itself does not support nested data structures. To combat this, nested dictionaries and Pydantic models are serialized to a JSON string before being saved to the database.

Filters for nested properties are also not supported, since they are stored as strings inside the database. This means that you can't use filters on nested properties when running queries with models. If you want to use filters on nested properties, you will to run a complex regular expression query.

### Indexes, constraints and properties

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
  ## Using the `WithOptions` method on the type, we can still use all of the features provided by
  ## `Pydantic` while also defining indexes and constraints on the property.
  uid: WithOptions(UUID, unique=True) = Field(default_factory=uuid4)
  name: WithOptions(str, text_index=True)
  ## Has no effect, since no index or constraint options are passed
  age: WithOptions(int)
```

There also is a special type of property called `RelationshipProperty`. This property can be used to define relationships between models. For more information about this property, see the [`Relationship-properties`](https://github.com/groc-prog/pyneo4j-ogm/blob/develop/docs/RelationshipProperty.md) section.

### Reserved properties

Node- and RelationshipModels have a few pre-defined properties which reflect the entity inside the graph and are used internally in queries. These properties are:

- `element_id`: The element id of the entity inside the graph. This property is used internally to identify the entity inside the graph.
- `id`: The id of the entity inside the graph.
- `modified_properties`: A set of properties which have been modified on the

The `RelationshipModel` class has some additional properties:

- `start_node_element_id`: The element id of the start node of the relationship.
- `start_node_id`: The ID of the start node of the relationship.
- `end_node_element_id`: The element id of the end node of the relationship.
- `end_node_id`: The ID of the end node of the relationship.

These properties are implemented as class properties and allow you to access the graph properties of you models.

### Configuration settings

Both `NodeModel` and `RelationshipModel` provide a few properties that can be configured. In this section we are going to take a closer look at how to configure your models and what options are available to you.

Model configuration is done by defining a inner `Settings` class inside the model itself. The properties of this class control how the model is handled by `pyneo4j-ogm`:

```python
class Coffee(NodeModel):
  flavour: str
  sugar: bool
  milk: bool

  class Settings:
    ## This is the place where the magic happens!
```

#### NodeModel configuration

The `Settings` class of a `NodeModel` provides the following properties:

| Setting name          | Type                          | Description                                                                                                                                                                                                                                                                                                                              |
| --------------------- | ----------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `pre_hooks`           | **Dict[str, List[Callable]]** | A dictionary where the key is the name of the method for which to register the hook and the value is a list of hook functions. The hook function can be synchronous or asynchronous. All hook functions receive the exact same arguments as the method they are registered for and the current model instance as the first argument. Defaults to `{}`. |
| `post_hooks`          | **Dict[str, List[Callable]]** | Same as **pre_hooks**, but the hook functions are executed after the method they are registered for. Additionally, the result of the method is passed to the hook as the second argument. Defaults to `{}`.                                                                                                                              |
| `labels`           | **Set[str]** | A set of labels to use for the node. If no labels are defined, the name of the model will be used as the label. Defaults to the `model name split by it's words`.                                                                                                                                                                                                                            |
| `auto_fetch_nodes` | **bool**     | Whether to automatically fetch nodes of defined relationship-properties when getting a model instance from the database. Auto-fetched nodes are available at the `instance.<relationship-property>.nodes` property. If no specific models are passed to a method when this setting is set to `True`, nodes from all defined relationship-properties are fetched. Defaults to `False`. |

#### RelationshipModel configuration

For RelationshipModels, the `labels` setting is not available, since relationships don't have labels in Neo4j. Instead, the `type` setting can be used to define the type of the relationship. If no type is defined, the name of the model name will be used as the type.

| Setting name          | Type                          | Description                                                                                                                                                                                                                                                                                                                              |
| --------------------- | ----------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `pre_hooks`           | **Dict[str, List[Callable]]** | A dictionary where the key is the name of the method for which to register the hook and the value is a list of hook functions. The hook function can be synchronous or asynchronous. All hook functions receive the exact same arguments as the method they are registered for and the current model instance as the first argument. Defaults to `{}`. |
| `post_hooks`          | **Dict[str, List[Callable]]** | Same as **pre_hooks**, but the hook functions are executed after the method they are registered for. Additionally, the result of the method is passed to the hook as the second argument. Defaults to `{}`.                                                                                                                              |
| `type`       | **str** | The type of the relationship to use. If no type is defined, the model name will be used as the type. Defaults to the `model name in all uppercase`. |

> **Note:** Hooks can be defined for all native methods that interact with the database. When defining a hook for a method on a relationship-property, you have to pass a string in the format `<relationship-property>.<method>` as the key. For example, if you want to define a hook for the `connect()` method of a relationship-property named `coffee`, you would have to pass `coffee.connect` as the key. This is true for both Node- and Relationship-models.

### Available methods

Running cypher queries manually is nice and all, but something else running them for you is even better. That's exactly what the model methods are for. They allow you to do all sorts of things with your models and the nodes and relationships they represent. In this section we are going to take a closer look at the different methods available to you.

But before we jump in, let's get one thing out of the way: All of the methods described in this section are `asynchronous` methods. This means that they have to be awaited when called. If you are new to asynchronous programming in Python, you should take a look at the [`asyncio documentation`](https://docs.python.org/3/library/asyncio.html) before continuing.

> **Note**: The name of the heading for each method defines what type of model it is available on and whether it is a `class method` or an `instance method`.
>
> - `Model.method()`: The `class method` is available on instances of both `NodeModel` and `RelationshipModel` classes.
> - `Instance.method()`: The `instance method` is available on instances of both `NodeModel` and `RelationshipModel` classes.
> - `<Type>Model.method()`: The `class method` is available on instances of the `<Type>Model` class.
> - `<Type>ModelInstance.method()`: The `instance method` is available on instances of the `<Type>Model` class.

#### Instance.update()

The `update()` method can be used to sync the modified properties of a node or relationship-model with the corresponding entity inside the graph. All models also provide a property called `modified_properties` that contains a set of all properties that have been modified since the model was created, fetched or synced with the database. This property is used by the `update()` method to determine which properties to sync with the database.

```python
## In this context, the developer `john` has been created before and the `name` property has been
## not been changed since.

## Maybe we want to name him James instead?
john.name = "James"

print(john.modified_properties)  ## {"name"}

## Will update the `name` property of the `john` node inside the graph
## And suddenly he is James!
await john.update()
```

#### Instance.delete()

The `delete()` method can be used to delete the graph entity tied to the current model instance. Once deleted, the model instance will be marked as `destroyed` and any further operations on it will raise a `InstanceDestroyed` exception.

```python
## In this context, the developer `john` has been created before and is seen as `hydrated` (aka it
## has been saved to the database before).

## This will delete the `john` node inside the graph and mark your local instance as `destroyed`.
await john.delete()

await john.update()  ## Raises `InstanceDestroyed` exception
```

#### Instance.refresh()

Syncs your local instance with the properties from the corresponding graph entity. ´This method can be useful if you want to make sure that your local instance is always up-to-date with the graph entity.

It is recommended to always call this method when importing a model instance from a dictionary (but does not have to be called necessarily, which in turn could cause a data inconsistency locally, so be careful when!).

```python
## Maybe we want to name him James instead?
john.name = "James"

## Oh no, don't take my `john` away!
await john.refresh()

print(john.name) ## 'John'
```

#### Model.find_one()

The `find_one()` method can be used to find a single node or relationship in the graph. If multiple results are matched, the first one is returned. This method returns a single instance/dictionary or `None` if no results were found.

This method takes a mandatory `filters` argument, which is used to filter the results. For more about filters, see the [`Filtering queries`](https://github.com/groc-prog/pyneo4j-ogm/blob/develop/docs/Query.md#filtering-queries) section.

```python
## Return the first encountered node where the name property equals `John`.
## This method always needs a filter to go with it!
john_or_nothing = await Developer.find_one({"name": "John"})

print(developer) ## <Developer> or None
```

##### Projections

`Projections` can be used to only return specific parts of the model as a dictionary. This can help to reduce bandwidth or to just pre-filter the query results to a more suitable format. For more about projections, see [`Projections`](https://github.com/groc-prog/pyneo4j-ogm/blob/develop/docs/Query.md#projections)

```python
## Return a dictionary with the developers name at the `dev_name` key instead
## of a model instance.
developer = await Developer.find_one({"name": "John"}, {"dev_name": "name"})

print(developer) ## {"dev_name": "John"}
```

##### Auto-fetching nodes

The `auto_fetch_nodes` and `auto_fetch_models` arguments can be used to automatically fetch all or selected nodes from defined relationship-properties when running the `find_one()` query. The pre-fetched nodes are available on their respective relationship-properties. For more about auto-fetching, see [`Auto-fetching relationship-properties`](https://github.com/groc-prog/pyneo4j-ogm/blob/develop/docs/Query.md#auto-fetching-relationship-properties).

> **Note**: The `auto_fetch_nodes` and `auto_fetch_models` parameters are only available for classes which inherit from the `NodeModel` class.

```python
## Returns a developer instance with `instance.<property>.nodes` properties already fetched
developer = await Developer.find_one({"name": "John"}, auto_fetch_nodes=True)

print(developer.coffee.nodes) ## [<Coffee>, <Coffee>, ...]
print(developer.other_property.nodes) ## [<OtherModel>, <OtherModel>, ...]

## Returns a developer instance with only the `instance.coffee.nodes` property already fetched
developer = await Developer.find_one({"name": "John"}, auto_fetch_nodes=True, auto_fetch_models=[Coffee])

## Auto-fetch models can also be passed as strings
developer = await Developer.find_one({"name": "John"}, auto_fetch_nodes=True, auto_fetch_models=["Coffee"])

print(developer.coffee.nodes) ## [<Coffee>, <Coffee>, ...]
print(developer.other_property.nodes) ## []
```

##### Raise on empty result

By default, the `find_one()` method will return `None` if no results were found. If you want to raise an exception instead, you can pass `raise_on_empty=True` to the method.

```python
## Raises a `NoResultFound` exception if no results were found
developer = await Developer.find_one({"name": "John"}, raise_on_empty=True)
```

#### Model.find_many()

The `find_many()` method can be used to find multiple nodes or relationships in the graph. This method always returns a list of instances/dictionaries or an empty list if no results were found.

```python
## Returns ALL `Developer` nodes
developers = await Developer.find_many()

print(developers) ## [<Developer>, <Developer>, <Developer>, ...]
```

##### Filters

Just like the `find_one()` method, the `find_many()` method also takes (optional) filters. For more about filters, see the [`Filtering queries`](https://github.com/groc-prog/pyneo4j-ogm/blob/develop/docs/Query.md#filtering-queries) section.

```python
## Returns all `Developer` nodes where the age property is greater than or
## equal to 21 and less than 45.
developers = await Developer.find_many({"age": {"$and": [{"$gte": 21}, {"$lt": 45}]}})

print(developers) ## [<Developer>, <Developer>, <Developer>, ...]
```

##### Projections

`Projections` can be used to only return specific parts of the models as dictionaries. For more information about projections, see the [`Projections`](https://github.com/groc-prog/pyneo4j-ogm/blob/develop/docs/Query.md#projections) section.

```python
## Returns dictionaries with the developers name at the `dev_name` key instead
## of model instances
developers = await Developer.find_many({"name": "John"}, {"dev_name": "name"})

print(developers) ## [{"dev_name": "John"}, {"dev_name": "John"}, ...]
```

##### Query options

`Query options` can be used to define how results are returned from the query. They are provided via the `options` argument. For more about query options, see the [`Query options`](https://github.com/groc-prog/pyneo4j-ogm/blob/develop/docs/Query.md#query-options) section.

```python
## Skips the first 10 results and returns the next 20
developers = await Developer.find_many({"name": "John"}, options={"limit": 20, "skip": 10})

print(developers) ## [<Developer>, <Developer>, ...] up to 20 results
```

##### Auto-fetching nodes

The `auto_fetch_nodes` and `auto_fetch_models` parameters can be used to automatically fetch all or selected nodes from defined relationship-properties when running the `find_many()` query. For more about auto-fetching, see [`Auto-fetching relationship-properties`](https://github.com/groc-prog/pyneo4j-ogm/blob/develop/docs/Query.md#auto-fetching-relationship-properties).

> **Note**: The `auto_fetch_nodes` and `auto_fetch_models` parameters are only available for classes which inherit from the `NodeModel` class.

```python
## Returns developer instances with `instance.<property>.nodes` properties already fetched
developers = await Developer.find_many({"name": "John"}, auto_fetch_nodes=True)

print(developers[0].coffee.nodes) ## [<Coffee>, <Coffee>, ...]
print(developers[0].other_property.nodes) ## [<OtherModel>, <OtherModel>, ...]

## Returns developer instances with only the `instance.coffee.nodes` property already fetched
developers = await Developer.find_many({"name": "John"}, auto_fetch_nodes=True, auto_fetch_models=[Coffee])

## Auto-fetch models can also be passed as strings
developers = await Developer.find_many({"name": "John"}, auto_fetch_nodes=True, auto_fetch_models=["Coffee"])

print(developers[0].coffee.nodes) ## [<Coffee>, <Coffee>, ...]
print(developers[0].other_property.nodes) ## []
```

#### Model.update_one()

The `update_one()` method finds the first matching graph entity and updates it with the provided properties. If no match was found, nothing is updated and `None` is returned. Properties provided in the update parameter, which have not been defined on the model, will be ignored.

This method takes two mandatory arguments:

- `update`: A dictionary containing the properties to update.
- `filters`: A dictionary containing the filters to use when searching for a match. For more about filters, see the [`Filtering queries`](https://github.com/groc-prog/pyneo4j-ogm/blob/develop/docs/Query.md#query-filters) section.

```python
## Updates the `age` property to `30` in the first encountered node where the name property equals `John`
## The `i_do_not_exist` property will be ignored since it has not been defined on the model
developer = await Developer.update_one({"age": 30, "i_do_not_exist": True}, {"name": "John"})

print(developer) ## <Developer age=25>

## Or if no match was found
print(developer) ## None
```

##### Returning the updated entity

By default, the `update_one()` method returns the model instance before the update. If you want to return the updated model instance instead, you can do so by passing the `new` parameter to the method and setting it to `True`.

```python
## Updates the `age` property to `30` in the first encountered node where the name property equals `John`
## and returns the updated node
developer = await Developer.update_one({"age": 30}, {"name": "John"}, True)

print(developer) ## <Developer age=30>
```

##### Raise on empty result

By default, the `update_one()` method will return `None` if no results were found. If you want to raise an exception instead, you can pass `raise_on_empty=True` to the method.

```python
## Raises a `NoResultFound` exception if no results were matched
developer = await Developer.update_one({"age": 30}, {"name": "John"}, raise_on_empty=True)
```

#### Model.update_many()

The `update_many()` method finds all matching graph entity and updates them with the provided properties. If no match was found, nothing is updated and a `empty list` is returned. Properties provided in the update parameter, which have not been defined on the model, will be ignored.

This method takes one mandatory argument `update` which defines which properties to update with which values.

```python
## Updates the `age` property of all `Developer` nodes to 40
developers = await Developer.update_many({"age": 40})

print(developers) ## [<Developer age=25>, <Developer age=23>, ...]

## Or if no matches were found
print(developers) ## []
```

##### Filters

Optionally, a `filters` argument can be provided, which defines which entities to update. For more about filters, see the [`Filtering queries`](https://github.com/groc-prog/pyneo4j-ogm/blob/develop/docs/Query.md#query-filters) section.

```python
## Updates all `Developer` nodes where the age property is between `22` and `30`
## to `40`
developers = await Developer.update_many({"age": 40}, {"age": {"$gte": 22, "$lte": 30}})

print(developers) ## [<Developer age=25>, <Developer age=23>, ...]
```

##### Returning the updated entity

By default, the `update_many()` method returns the model instances before the update. If you want to return the updated model instances instead, you can do so by passing the `new` parameter to the method and setting it to `True`.

```python
## Updates all `Developer` nodes where the age property is between `22` and `30`
## to `40` and return the updated nodes
developers = await Developer.update_many({"age": 40}, {"age": {"$gte": 22, "$lte": 30}})

print(developers) ## [<Developer age=40>, <Developer age=40>, ...]
```

#### Model.delete_one()

The `delete_one()` method finds the first matching graph entity and deletes it. Unlike others, this method returns the number of deleted entities instead of the deleted entity itself. If no match was found, nothing is deleted and `0` is returned.

This method takes one mandatory argument `filters` which defines which entity to delete. For more about filters, see the [`Filtering queries`](https://github.com/groc-prog/pyneo4j-ogm/blob/develop/docs/Query.md#query-filters) section.

```python
## Deletes the first `Developer` node where the name property equals `John`
count = await Developer.delete_one({"name": "John"})

print(count) ## 1

## Or if no match was found
print(count) ## 0
```

##### Raise on empty result

By default, the `delete_one()` method will return `None` if no results were found. If you want to raise an exception instead, you can pass `raise_on_empty=True` to the method.

```python
## Raises a `NoResultFound` exception if no results were matched
count = await Developer.delete_one({"name": "John"}, raise_on_empty=True)
```

#### Model.delete_many()

The `delete_many()` method finds all matching graph entity and deletes them. Like the `delete_one()` method, this method returns the number of deleted entities instead of the deleted entity itself. If no match was found, nothing is deleted and `0` is returned.

```python
## Deletes all `Developer` nodes
count = await Developer.delete_many()

print(count) ## However many nodes matched the filter

## Or if no match was found
print(count) ## 0
```

##### Filters

Optionally, a `filters` argument can be provided, which defines which entities to delete. For more about filters, see the [`Filtering queries`](https://github.com/groc-prog/pyneo4j-ogm/blob/develop/docs/Query.md#query-filters) section.

```python
## Deletes all `Developer` nodes where the age property is greater than `65`
count = await Developer.delete_many({"age": {"$gt": 65}})

print(count) ## However many nodes matched the filter
```

#### Model.count()

The `count()` method returns the total number of entities of this model in the graph.

```python
## Returns the total number of `Developer` nodes inside the database
count = await Developer.count()

print(count) ## However many nodes matched the filter

## Or if no match was found
print(count) ## 0
```

##### Filters

Optionally, a `filters` argument can be provided, which defines which entities to count. For more about filters, see the [`Filtering queries`](https://github.com/groc-prog/pyneo4j-ogm/blob/develop/docs/Query.md#query-filters) section.

```python
## Counts all `Developer` nodes where the name property contains the letters `oH`
## The `i` in `icontains` means that the filter is case insensitive
count = await Developer.count({"name": {"$icontains": "oH"}})

print(count) ## However many nodes matched the filter
```

#### NodeModelInstance.create()

> **Note**: This method is only available for classes inheriting from the `NodeModel` class.

The `create()` method allows you to create a new node from a given model instance. All properties defined on the instance will be carried over to the corresponding node inside the graph. After this method has successfully finished, the instance saved to the database will be seen as `hydrated` and other methods such as `update()`, `refresh()`, etc. will be available.

```python
## Creates a node inside the graph with the properties and labels
## from the model below
developer = Developer(name="John", age=24)
await developer.create()

print(developer) ## <Developer uid="..." age=24, name="John">
```

#### NodeModelInstance.find_connected_nodes()

> **Note**: This method is only available for classes inheriting from the `NodeModel` class.

The `find_connected_nodes()` method can be used to find nodes over multiple hops. It returns all matched nodes with the defined labels in the given hop range or an empty list if no nodes where found. The method requires you to define the labels of the nodes you want to find inside the filters (You can only define the labels of `one model` at a time). For more about filters, see the [`Filtering queries`](https://github.com/groc-prog/pyneo4j-ogm/blob/develop/docs/Query.md#query-filters) section.

```python
## Picture a structure like this inside the graph:
## (:Producer)-[:SELLS_TO]->(:Barista)-[:PRODUCES {with_love: bool}]->(:Coffee)-[:CONSUMED_BY]->(:Developer)

## If we want to get all `Developer` nodes connected to a `Producer` node over the `Barista` and `Coffee` nodes,
## where the `Barista` created the coffee with love, we can do so like this:
producer = await Producer.find_one({"name": "Coffee Inc."})

if producer is None:
  ## No producer found, do something else

developers = await producer.find_connected_nodes({
  "$node": {
    "$labels": ["Developer", "Python"],
    ## You can use all available filters here as well
  },
  ## You can define filters on specific relationships inside the path
  "$relationships": [
    {
      ## Here we define a filter for all `PRODUCES` relationships
      ## Only nodes where the with_love property is set to `True` will be returned
      "$type": "PRODUCES",
      "with_love": True
    }
  ]
})

print(developers) ## [<Developer>, <Developer>, ...]

## Or if no matches were found
print(developers) ## []
```

##### Projections

`Projections` can be used to only return specific parts of the models as dictionaries. For more information about projections, see the [`Projections`](https://github.com/groc-prog/pyneo4j-ogm/blob/develop/docs/Query.md#projections) section.

```python
## Returns dictionaries with the developers name at the `dev_name` key instead
## of model instances
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

print(developers) ## [{"dev_name": "John"}, {"dev_name": "John"}, ...]
```

##### Query options

`Query options` can be used to define how results are returned from the query. They are provided via the `options` argument. For more about query options, see the [`Query options`](https://github.com/groc-prog/pyneo4j-ogm/blob/develop/docs/Query.md#query-options) section.

```python
## Skips the first 10 results and returns the next 20
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

print(developers) ## [<Developer>, <Developer>, ...]
```

##### Auto-fetching nodes

The `auto_fetch_nodes` and `auto_fetch_models` parameters can be used to automatically fetch all or selected nodes from defined relationship-properties when running the `find_connected_nodes()` query. For more about auto-fetching, see [`Auto-fetching relationship-properties`](https://github.com/groc-prog/pyneo4j-ogm/blob/develop/docs/Query.md#auto-fetching-relationship-properties).

```python
## Skips the first 10 results and returns the next 20
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

print(developers[0].coffee.nodes) ## [<Coffee>, <Coffee>, ...]
print(developers[0].other_property.nodes) ## [<OtherModel>, <OtherModel>, ...]

## Returns developer instances with only the `instance.coffee.nodes` property already fetched
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

print(developers[0].coffee.nodes) ## [<Coffee>, <Coffee>, ...]
print(developers[0].other_property.nodes) ## []
```

#### RelationshipModelInstance.start_node()

> **Note**: This method is only available for classes inheriting from the `RelationshipModel` class.

This method returns the start node of the current relationship instance. This method takes no arguments.

```python
## The `coffee_relationship` variable is a relationship instance created somewhere above
start_node = await coffee_relationship.start_node()

print(start_node) ## <Coffee>
```

#### RelationshipModelInstance.end_node()

> **Note**: This method is only available for classes inheriting from the `RelationshipModel` class.

This method returns the end node of the current relationship instance. This method takes no arguments.

```python
## The `coffee_relationship` variable is a relationship instance created somewhere above
end_node = await coffee_relationship.end_node()

print(end_node) ## <Developer>
```

### Serializing models

When serializing models to a dictionary or JSON string, the models `element_id and id` fields are `automatically added` to the corresponding dictionary/JSON string when calling Pydantic's `dict()` or `json()` methods.

If you want to exclude them from serialization, you can easily do so by passing them to the `exclude` parameter of the according method.

On node-models:

- `id`
- `element_id`

Additional properties for relationship-models:

- `start_node_id`
- `start_node_element_id`
- `end_node_id`
- `end_node_element_id`

### Hooks

Hooks are a convenient way to execute code before or after a method is called A pre-hook function always receives the `class it is used on` as it's first argument and `any arguments the decorated method receives`. They can be used to execute code that is not directly related to the method itself, but still needs to be executed when the method is called. This allows for all sorts of things, such as logging, caching, etc.

`pyneo4j-ogm` provides a hooks for all available methods out of the box, and will even work for custom methods. Hooks are simply registered with the method name as the key and a list of hook functions as the value. The hook functions can be synchronous or asynchronous and will receive the exact same arguments as the method they are registered for and the current model instance as the first argument.

For relationship-properties, the key under which the hook is registered has to be in the format `<relationship-property>.<method>`. For example, if you want to register a hook for the `connect()` method of a relationship-property named `coffee`, you would have to pass `coffee.connect` as the key. Additionally, instead of the `RelationshipProperty class context`, the hook function will receive the `NodeModel class context` of the model it has been called on as the first argument.

> **Note:** If you implement custom methods and want to use hooks for them, you can simply define the `hook decorator` on them and then register hooks under the `name of your method`.

#### Pre-hooks

Pre-hooks are executed before the method they are registered for. They can be defined in the [`model settings`](https://github.com/groc-prog/pyneo4j-ogm/blob/develop/docs/Models.md#configuration-settings) class under the `pre_hooks` property or by calling the `register_pre_hooks()` method on the model.

```python
class Developer(NodeModel):
  ...

  class Settings:
    post_hooks = {
      "coffee.connect": lambda self, *args, **kwargs: print(f"{self.name} chugged another one!")
    }


## Or by calling the `register_pre_hooks()` method
## Here `hook_func` can be a synchronous or asynchronous function reference
Developer.register_pre_hooks("create", hook_func)

## By using the `register_pre_hooks()` method, you can also overwrite all previously registered hooks
## This will overwrite all previously registered hooks for the defined hook name
Developer.register_pre_hooks("create", hook_func, overwrite=True)
```

#### Post-hooks

Post-hooks are executed after the method they are registered for. They can be defined in the [`model settings`](https://github.com/groc-prog/pyneo4j-ogm/blob/develop/docs/Models.md#configuration-settings) class under the `post_hooks` property or by calling the `register_post_hooks()` method on the model.

In addition to the same arguments a pre-hook function receives, a post-hook function also receives the result of the method it is registered for as the second argument.

> **Note:** Since post-hooks have the exact same usage/registration options as pre-hooks, they are not explained in detail here.

### Model settings

Can be used to access the model's settings. For more about model settings, see the [`model settings`]([#model-settings](https://github.com/groc-prog/pyneo4j-ogm/blob/develop/docs/Models.md#configuration-settings)) section.

```python
model_settings = Developer.model_settings()

print(model_settings) ## <NodeModelSettings labels={"Developer"}, auto_fetch_nodes=False, ...>
```
