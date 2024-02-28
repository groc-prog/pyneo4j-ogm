
## Queries

As you might have seen by now, `pyneo4j-ogm` provides a variate of methods to query the graph. If you followed the documentation up until this point, you might have seen that most of the methods take a `filters` argument.

If you have some `prior experience` with `Neo4j and Cypher`, you may know that it does not provide a easy way to generate queries from given inputs. This is where `pyneo4j-ogm` comes in. It provides a `variety of filters` to make querying the graph as easy as possible.

The filters are heavily inspired by [`MongoDB's query language`](https://docs.mongodb.com/manual/tutorial/query-documents/), so if you have some experience with that, you will feel right at home.

This is really nice to have, not only for normal usage, but especially if you are developing a `gRPC service` or `REST API` and want to provide a way to query the graph from the outside.

But enough of that, let's take a look at the different filters available to you.

### Filtering queries

Since the filters are inspired by MongoDB's query language, they are also very similar. The filters are defined as dictionaries, where the keys are the properties you want to filter on and the values are the values you want to filter for.

We can roughly separate them into the `following categories`:

- Comparison operators
- String operators
- List operators
- Logical operators
- Element operators

#### Comparison operators

Comparison operators are used to compare values to each other. They are the most basic type of filter.

| Operator | Description | Corresponding Cypher query |
| --- | --- | --- |
| `$eq` | Matches values that are equal to a specified value. | `WHERE node.property = value` |
| `$neq` | Matches all values that are not equal to a specified value. | `WHERE node.property <> value` |
| `$gt` | Matches values that are greater than a specified value. | `WHERE node.property > value` |
| `$gte` | Matches values that are greater than or equal to a specified value. | `WHERE node.property >= value` |
| `$lt` | Matches values that are less than a specified value. | `WHERE node.property < value` |
| `$lte` | Matches values that are less than or equal to a specified value. | `WHERE node.property <= value` |

#### String operators

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

#### List operators

List operators are used to compare list values to each other.

| Operator | Description | Corresponding Cypher query |
| --- | --- | --- |
| `$in` | Matches lists where at least one item is in the given list. | `WHERE ANY(i IN node.property WHERE i IN value)` |
| `$nin` | Matches lists where no items are in the given list | `WHERE NONE(i IN node.property WHERE i IN value)` |
| `$all` | Matches lists where all items are in the given list. | `WHERE ALL(i IN node.property WHERE i IN value)` |
| `$size` | Matches lists where the size of the list is equal to the given value. | `WHERE size(node.property) = value` |

> **Note**: The `$size` operator can also be combined with the comparison operators by nesting them inside the `$size` operator. For example: `{"$size": {"$gt": 5}}`.

#### Logical operators

Logical operators are used to combine multiple filters with each other.

| Operator | Description | Corresponding Cypher query |
| --- | --- | --- |
| `$and` | Joins query clauses with a logical AND returns all nodes that match the conditions of both clauses (Used by default if multiple filters are present). | `WHERE node.property1 = value1 AND node.property2 = value2` |
| `$or` | Joins query clauses with a logical OR returns all nodes that match the conditions of either clause. | `WHERE node.property1 = value1 OR node.property2 = value2` |
| `$xor` | Joins query clauses with a logical XOR returns all nodes that match the conditions of either clause but not both. | `WHERE WHERE node.property1 = value1 XOR node.property2 = value2` |
| `$not` | Inverts the effect of a query expression nested within and returns nodes that do not match the query expression. | `WHERE NOT (node.property = value)` |

#### Element operators

Element operators are a special kind of operator not available for every filter type. They are used to check Neo4j-specific values.

| Operator | Description | Corresponding Cypher query |
| --- | --- | --- |
| `$exists` | Matches nodes that have the specified property. | `WHERE EXISTS(node.property)` |
| `$elementId` | Matches nodes that have the specified element id. | `WHERE elementId(node) = value` |
| `$id` | Matches nodes that have the specified id. | `WHERE id(node) = value` |
| `$labels` | Matches nodes that have the specified labels. | `WHERE ALL(i IN labels(n) WHERE i IN value)` |
| `$type` | Matches relationships that have the specified type. Can be either a list or a string. | For a string: `WHERE type(r) = value`, For a list: `WHERE type(r) IN value` |

#### Pattern matching

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
      ## The `$exists` operator tells the library to match/ignore the pattern
      "$exists": False,
      ## The defines the direction of the relationship inside the pattern
      "$direction": RelationshipMatchDirection.OUTGOING,
      ## The `$node` key is used to define the node we want to filter for. This means
      ## the filters inside the `$node` key will be applied to our `Coffee` nodes
      "$node": {
        "$labels": ["Beverage", "Hot"],
        "sugar": False
      },
      ## The `$relationship` key is used to filter the relationship between the two nodes
      ## It can also define property filters for the relationship
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

#### Multi-hop filters

Multi-hop filters are a special type of filter which is only available for [`NodeModelInstance.find_connected_nodes()`](https://github.com/groc-prog/pyneo4j-ogm/blob/main/docs/Models.md#nodemodelsettingsfind_connected_nodes()). They allow you to specify filter parameters on the target node and all relationships between them over, you guessed it, multiple hops. To define this filter, you have a few operators you can define:

- `$node`: Filters applied to the target node. Expects a dictionary containing basic filters. Can not contain pattern yet.
- `$minHops`: The minimum number of hops between the source node and the target node. Must be greater than 0.
- `$maxHops`: The maximum number of hops between the source node and the target node. You can pass "\*" as a value to define no upper limit. Must be greater than 1.
- `$relationships`: A list of relationship filters. Each filter is a dictionary containing basic filters and must define a $type operator.

```python
## Picture a structure like this inside the graph:
## (:Producer)-[:SELLS_TO]->(:Barista)-[:PRODUCES {with_love: bool}]->(:Coffee)-[:CONSUMED_BY]->(:Developer)

## If we want to get all `Developer` nodes connected to a `Producer` node over the `Barista` and `Coffee` nodes,
## where the `Barista` created the coffee with love.

## Let's say, for the sake of this example, that there are connections possible
## with 10+ hops, but we don't want to include them. To solve this, we can define
## a `$maxHops` filter with a value of `10`.
producer = await Producer.find_one({"name": "Coffee Inc."})

if producer is None:
  ## No producer found, do something else

developers = await producer.find_connected_nodes({
  "$maxHops": 10,
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

### Projections

Projections are used to only return specific parts of the models as dictionaries. They are defined as a dictionary where the key is the name of the property in the returned dictionary and the value is the name of the property on the model instance.

Projections can help you to reduce bandwidth usage and speed up queries, since you only return the data you actually need.

> **Note:** Only top-level mapping is supported. This means that you can not map properties to a nested dictionary key.

In the following example, we will return a dictionary with a `dev_name` key, which get's mapped to the models `name` property and a `dev_age` key, which get's mapped to the models `age` property. Any defined mapping which does not exist on the model will have `None` as it's value. You can also map the result's `elementId` and `Id` using either `$elementId` or `$id` as the value for the mapped key.

```python
developer = await Developer.find_one({"name": "John"}, {"dev_name": "name", "dev_age": "age", "i_do_not_exist": "some_non_existing_property"})

print(developer) ## {"dev_name": "John", "dev_age": 24, "i_do_not_exist": None}
```

### Query options

Query options are used to define how results are returned from the query. They provide some basic functionality for easily implementing pagination, sorting, etc. They are defined as a dictionary where the key is the name of the option and the value is the value of the option. The following options are available:

- `limit`: Limits the number of returned results.
- `skip`: Skips the first `n` results.
- `sort`: Sorts the results by the given property. Can be either a string or a list of strings. If a list is provided, the results will be sorted by the first property and then by the second property, etc.
- `order`: Defines the sort direction. Can be either `ASC` or `DESC`. Defaults to `ASC`.

```python
## Returns 50 results, skips the first 10 and sorts them by the `name` property in descending order
developers = await Developer.find_many({}, options={"limit": 50, "skip": 10, "sort": "name", "order": QueryOptionsOrder.DESCENDING})

print(len(developers)) ## 50
print(developers) ## [<Developer>, <Developer>, ...]
```

### Auto-fetching relationship-properties

You have the option to automatically fetch all defined relationship-properties of matched nodes. This will populate the `instance.<property>.nodes` attribute with the fetched nodes. This can be useful in situations where you need to fetch a specific node and get all of it's related nodes at the same time.

> **Note**: Auto-fetching nodes with many relationships can be very expensive and slow down your queries. Use it with caution.

To enable this behavior, you can either set the `auto_fetch_nodes` parameter to `True` or set the `auto_fetch_nodes setting` in the model settings to `True`, but doing so will `always enable auto-fetching`.

You can also define which relationship-properties to fetch by providing the fetched models to the `auto_fetch_models` parameter. This can be useful if you only want to fetch specific relationship-properties.

Now, let's take a look at an example:

```python
## Fetches everything defined in the relationship-properties of the current matched node
developer = await Developer.find_one({"name": "John"}, auto_fetch_nodes=True)

## All nodes for all defined relationship-properties are now fetched
print(developer.coffee.nodes) ## [<Coffee>, <Coffee>, ...]
print(developer.developer.nodes) ## [<Developer>, <Developer>, ...]
print(developer.other_property.nodes) ## [<OtherModel>, <OtherModel>, ...]
```

With the `auto_fetch_models` parameter, we can define which relationship-properties to fetch:

```python
## Only fetch nodes for `Coffee` and `Developer` models defined in relationship-properties
## The models can also be passed as strings, where the string is the model's name
developer = await Developer.find_one({"name": "John"}, auto_fetch_nodes=True, auto_fetch_models=[Coffee, "Developer"])

## Only the defined models have been fetched
print(developer.coffee.nodes) ## [<Coffee>, <Coffee>, ...]
print(developer.developer.nodes) ## [<Developer>, <Developer>, ...]
print(developer.other_property.nodes) ## []
```
