## Relationship-properties

> **Note**: Relationship-properties are only available for classes which inherit from the `NodeModel` class.

Relationship-properties are a special type of property that can only be defined on a `NodeModel` class. They can be used to define relationships between nodes and other models. They provide a variate of options to fine-tune the relationship and how it behaves. The options are pretty self-explanatory, but let's go through them anyway:

```python
class Developer(NodeModel):

    ## Here we define a relationship to one or more `Coffee` nodes, both the target
    ## and relationship-model can be defined as strings (Has to be the exact name of the model)

    ## Notice that the `RelationshipProperty` class takes two type arguments, the first
    ## one being the target model and the second one being the relationship-model
    ## Can can get away without defining these, but it is recommended to do so for
    ## better type hinting
    coffee: RelationshipProperty["Coffee", "Consumed"] = RelationshipProperty(
        ## The target model is the model we want to connect to
        target_model="Coffee",
        ## The relationship-model is the model which defines the relationship
        ## between a target model (in this case `Coffee`) and the model it is defined on
        relationship_model=Consumed,
        ## The direction of the relationship inside the graph
        direction=RelationshipPropertyDirection.OUTGOING,
        ## Cardinality defines how many nodes can be connected to the relationship
        ## **Note**: This only softly enforces cardinality from the model it's defined on
        ## and does not enforce it on the database level
        cardinality=RelationshipPropertyCardinality.ZERO_OR_MORE,
        ## Whether to allow multiple connections to the same node
        allow_multiple=True,
    )
```

### Available methods

Just like regular models, relationship-properties also provide a few methods to make working with them easier. In this section we are going to take a closer look at the different methods available to you.

> **Note**: In the following, the terms `source node` and `target node` will be used. Source node refers to the `node instance the method is called on` and target node refers to the `node/s passed to the method`.

#### RelationshipProperty.relationships()

Returns the relationships between the source node and the target node. The method expects a single argument `node` which has to be the target node of the relationship. This always returns a list of relationship instances or an empty list if no relationships were found.

```python
## The `developer` and `coffee` variables have been defined somewhere above

## Returns the relationships between the two nodes
coffee_relationships = await developer.coffee.relationships(coffee)

print(coffee_relationships) ## [<Consumed>, <Consumed>, ...]

## Or if no relationships were found
print(coffee_relationships) ## []
```

##### Filters

This method also allows for (optional) filters. For more about filters, see the [`Filtering queries`](https://github.com/groc-prog/pyneo4j-ogm/blob/main/docs/Query.md#filtering-queries) section.

```python
## Only returns the relationships between the two nodes where
## the `developer liked the coffee`
coffee_relationships = await developer.coffee.relationships(coffee, {"likes_it": True})

print(coffee_relationships) ## [<Consumed liked=True>, <Consumed liked=True>, ...]
```

##### Projections

`Projections` can be used to only return specific parts of the models as dictionaries. For more information about projections, see the [`Projections`](https://github.com/groc-prog/pyneo4j-ogm/blob/main/docs/Query.md#projections) section.

```python
## Returns dictionaries with the relationships `liked` property is at the
## `loved_it` key instead of model instances
coffee_relationships = await developer.coffee.relationships(coffee, projections={"loved_it": "liked"})

print(coffee_relationships) ## [{"loved_it": True}, {"loved_it": False}, ...]
```

##### Query options

`Query options` can be used to define how results are returned from the query. They are provided via the `options` argument. For more about query options, see the [`Query options`](https://github.com/groc-prog/pyneo4j-ogm/blob/main/docs/Query.md#query-options) section.

```python
## Skips the first 10 results and returns the next 20
coffee_relationships = await developer.coffee.relationships(coffee, options={"limit": 20, "skip": 10})

print(coffee_relationships) ## [<Consumed>, <Consumed>, ...] up to 20 results
```

#### RelationshipProperty.connect()

Connects the given target node to the source node. The method expects the target node as the first argument, and optional properties as the second argument. The properties provided will be carried over to the relationship inside the graph.

Depending on the `allow_multiple` option, which is defined on the relationship-property, this method will either create a new relationship or update the existing one. If the `allow_multiple` option is set to `True`, this method will always create a new relationship. Otherwise, the query will use a `MERGE` statement to update an existing relationship.

```python
## The `developer` and `coffee` variables have been defined somewhere above

coffee_relationship = await developer.coffee.connect(coffee, {"likes_it": True})

print(coffee_relationship) ## <Consumed>
```

#### RelationshipProperty.disconnect()

Disconnects the target node from the source node and deletes all relationships between them. The only argument to the method is the target node. If no relationships exist between the two, nothing is deleted and `0` is returned. Otherwise, the number of deleted relationships is returned.

> **Note**: If `allow_multiple` was set to `True` and multiple relationships to the target node exist, all of them will be deleted.

```python
## The `developer` and `coffee` variables have been defined somewhere above

coffee_relationship_count = await developer.coffee.disconnect(coffee)

print(coffee_relationship_count) ## However many relationships were deleted
```

##### Raise on empty result

By default, the `disconnect()` method will return `None` if no results were found. If you want to raise an exception instead, you can pass `raise_on_empty=True` to the method.

```python
## Raises a `NoResultFound` exception if no results were matched
coffee_relationship_count = await developer.coffee.disconnect(coffee, raise_on_empty=True)
```

#### RelationshipProperty.disconnect_all()

Disconnects all target nodes from the source node and deletes all relationships between them. Returns the number of deleted relationships.

```python
## This will delete all relationships to `Coffee` nodes for this `Developer` node
coffee_relationship_count = await developer.coffee.disconnect_all()

print(coffee_relationship_count) ## However many relationships were deleted
```

#### RelationshipProperty.replace()

Disconnects all relationships from the source node to the old target node and connects them back to the new target node, carrying over all properties defined in the relationship. Returns the replaced relationships.

> **Note**: If `multiple relationships` between the target node and the old source node exist, `all of them` will be replaced.

```python
## Currently there are two relationships defined between the `developer` and `coffee_latte`
## nodes where the `likes_it` property is set to `True` and `False` respectively

## Moves the relationships from `coffee_latte` to `coffee_americano`
replaced_coffee_relationships = await developer.coffee.replace(coffee_latte, coffee_americano)

print(replaced_coffee_relationships) ## [<Consumed likes_it=True>, <Consumed likes_it=False>]
```

#### RelationshipProperty.find_connected_nodes()

Finds and returns all connected nodes for the given relationship-property. This method always returns a list of instances/dictionaries or an empty list if no results were found.

```python
## Returns all `Coffee` nodes
coffees = await developer.coffee.find_connected_nodes()

print(coffees) ## [<Coffee>, <Coffee>, ...]

## Or if no matches were found
print(coffees) ## []
```

##### Filters

You can pass filters using the `filters` argument to filter the returned nodes. For more about filters, see the [`Filtering queries`](https://github.com/groc-prog/pyneo4j-ogm/blob/main/docs/Query.md#filtering-queries) section.

```python
## Returns all `Coffee` nodes where the `sugar` property is set to `True`
coffees = await developer.coffee.find_connected_nodes({"sugar": True})

print(coffees) ## [<Coffee sugar=True>, <Coffee sugar=True>, ...]
```

##### Projections

`Projections` can be used to only return specific parts of the models as dictionaries. For more information about projections, see the [`Projections`](https://github.com/groc-prog/pyneo4j-ogm/blob/main/docs/Query.mdprojections) section.

```python
## Returns dictionaries with the coffee's `sugar` property at the `contains_sugar` key instead
## of model instances
coffees = await developer.coffee.find_connected_nodes({"sugar": True}, {"contains_sugar": "sugar"})

print(coffees) ## [{"contains_sugar": True}, {"contains_sugar": False}, ...]
```

##### Query options

`Query options` can be used to define how results are returned from the query. They are provided via the `options` argument. For more about query options, see the [`Query options`](https://github.com/groc-prog/pyneo4j-ogm/blob/main/docs/Query.mdquery-options) section.

```python
## Skips the first 10 results and returns the next 20
coffees = await developer.coffee.find_connected_nodes({"sugar": True}, options={"limit": 20, "skip": 10})

## Skips the first 10 results and returns up to 20
print(coffees) ## [<Coffee>, <Coffee>, ...]
```

##### Auto-fetching nodes

The `auto_fetch_nodes` and `auto_fetch_models` parameters can be used to automatically fetch all or selected nodes from defined relationship-properties when running the `find_many()` query. For more about auto-fetching, see [`Auto-fetching relationship-properties`](https://github.com/groc-prog/pyneo4j-ogm/blob/main/docs/Query.md#auto-fetching-relationship-properties).

```python
## Returns coffee instances with `instance.<property>.nodes` properties already fetched
coffees = await developer.coffee.find_connected_nodes(auto_fetch_nodes=True)

print(coffees[0].developer.nodes) ## [<Developer>, <Developer>, ...]
print(coffees[0].other_property.nodes) ## [<OtherModel>, <OtherModel>, ...]

## Returns coffee instances with only the `instance.developer.nodes` property already fetched
coffees = await developer.coffee.find_connected_nodes(auto_fetch_nodes=True, auto_fetch_models=[Developer])

## Auto-fetch models can also be passed as strings
coffees = await developer.coffee.find_connected_nodes(auto_fetch_nodes=True, auto_fetch_models=["Developer"])

print(coffees[0].developer.nodes) ## [<Developer>, <Developer>, ...]
print(coffees[0].other_property.nodes) ## []
```

### Hooks with relationship properties

Although slightly different, hooks can also be registered for relationship-properties. The only different lies in the arguments passed to the hook function. Since relationship-properties are defined on a `NodeModel` class, the hook function will receive the `NodeModel class context` of the model it has been called on as the first argument instead of the `RelationshipProperty class context` (like it would for regular models).

> **Note:** The rest of the arguments passed to the hook function are the same as for regular models.

```python
class Developer(NodeModel):

    ## Here we define a relationship to one or more `Coffee` nodes, both the target
    ## and relationship-model can be defined as strings (Has to be the exact name of the model)

    ## Notice that the `RelationshipProperty` class takes two type arguments, the first
    ## one being the target model and the second one being the relationship-model
    ## Can can get away without defining these, but it is recommended to do so for
    ## better type hinting
    coffee: RelationshipProperty["Coffee", "Consumed"] = RelationshipProperty(
        ## The target model is the model we want to connect to
        target_model="Coffee",
        ## The relationship-model is the model which defines the relationship
        ## between a target model (in this case `Coffee`) and the model it is defined on
        relationship_model=Consumed,
        ## The direction of the relationship inside the graph
        direction=RelationshipPropertyDirection.OUTGOING,
        ## Cardinality defines how many nodes can be connected to the relationship
        ## **Note**: This only softly enforces cardinality from the model it's defined on
        ## and does not enforce it on the database level
        cardinality=RelationshipPropertyCardinality.ZERO_OR_MORE,
        ## Whether to allow multiple connections to the same node
        allow_multiple=True,
    )

    class Settings:
        post_hooks = {
            "coffee.connect": lambda self, *args, **kwargs: print(type(self))
        }

## Somewhere further down the line...
## Prints `<class '__main__.Developer'>` instead of `<class '__main__.RelationshipProperty'>`
await developer.coffee.connect(coffee)
```

The reason for this change in the hooks behavior is simple, really. Since relationship-properties are only used to define relationships between nodes, it makes more sense to have the `NodeModel class context` available inside the hook function instead of the `RelationshipProperty class context`, since the hook function will most likely be used to execute code on the model the relationship-property is defined on.
