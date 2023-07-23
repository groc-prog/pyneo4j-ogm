## NodeModel

- [ ] `NodeModel.create()` - Saves instance to the DB
- [ ] `NodeModel.update()` - Updates current instance in DB
- [ ] `NodeModel.delete()` - Deletes the current instance in DB and flags it as destroyed
- [ ] `NodeModel.refresh()` - Refreshes current model instance from DB
- [ ] `NodeModel.find_one()` - Find first node of current model
- [ ] `NodeModel.find_many()` - Finds all nodes of current model
- [ ] `NodeModel.update_one()` - Update first node of current model
- [ ] `NodeModel.update_many()` - Updates all nodes of current model
- [ ] `NodeModel.delete_one()` - Delete first node of current model
- [ ] `NodeModel.delete_many()` - Deletes all nodes of current model
- [ ] `NodeModel.count()` - Returns the count of nodes found
- [ ] `NodeModel.find_connected_nodes()` - Finds connected nodes for one or more hops

- [ ] Add automatic refs for defined relationship properties in node models


## RelationshipModel

- [ ] `RelationshipModel.update()` - Update current instance in DB
- [ ] `RelationshipModel.delete()` - Update current instance in DB
- [ ] `RelationshipModel.refresh()` - Deletes current model instance from DB and flags it as destroyed
- [ ] `RelationshipModel.start_node()` - Returns the start node
- [ ] `RelationshipModel.end_node()` - Returns the end node
- [ ] `RelationshipModel.find_one()` - Find first relationship of current model
- [ ] `RelationshipModel.find_many()` - Finds all relationships of current model
- [ ] `RelationshipModel.update_one()` - Update first relationship of current model
- [ ] `RelationshipModel.update_many()` - Updates all relationships of current model
- [ ] `RelationshipModel.delete_one()` - Delete first relationship of current model
- [ ] `RelationshipModel.delete_many()` - Deletes all relationships of current model
- [ ] `RelationshipModel.count()` - Returns the count of relationships found


## RelationshipProperty

- [ ] `RelationshipProperty.relationship()` - Returns the relationship between source and target node
- [ ] `RelationshipProperty.connect()` - Connects source and target node
- [ ] `RelationshipProperty.disconnect()` - Disconnects source and target node
- [ ] `RelationshipProperty.disconnect_all()` - Disconnects source and all target node
- [ ] `RelationshipProperty.replace()` - Replaces one target node with another
- [ ] `RelationshipProperty.find_connected_nodes()` - Finds connected nodes with one hop


## Neo4jClient

- [ ] `Neo4jClient.register_models()` - Registers used models with client
- [ ] `Neo4jClient.connect()` - Connects to the DB
- [ ] `Neo4jClient.close()` - Closes connection to DB
- [ ] `Neo4jClient.cypher()` - Executes a given cypher query with parameters
- [ ] `Neo4jClient.create_constraint()` - Create a new constraint
- [ ] `Neo4jClient.create_index()` - Create a new index
- [ ] `Neo4jClient.drop_nodes()` - Delete all nodes
- [ ] `Neo4jClient.drop_constraints()` - Delete all constraints
- [ ] `Neo4jClient.drop_indexes()` - Delete all indexes
- [ ] `Neo4jClient.batch()` - Batches transactions inside the context manager together
