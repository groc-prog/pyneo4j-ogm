# Neo4j Object Graph Mapper

A wrapper library around **Neo4j's python driver** which provides a **structured and easy** approach to working with
Neo4j databases and cypher queries.


Create a new production-ready project with **backend** (Golang),
**frontend** (JavaScript, TypeScript) and **deploy automation** (Ansible,
Docker) by running only one CLI command.

Focus on **writing your code** and **thinking of the business-logic**! The CLI
will take care of the rest.

## ⚡️ Quick start

Before we can interact with the database, we have to do 3 simple things:

- Connect our client to our database
- Define our data structures with `NodeModels and RelationshipModels`
- Register our models with the client (Can be skipped but with some drawbacks, more talked about in [`Neo4jClient`][#neo4j-client])
