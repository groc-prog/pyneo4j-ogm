## Basic concepts

As you might have guessed by now, `pyneo4j-ogm` is a library that allows you to interact with a Neo4j database using Python. It is designed to make your life as simple as possible, while still providing the most common operations and some more advanced features.

But first, how does this even work!?! Well, the basic concept boils down to the following:

- You define your models that represent your nodes and relationships inside the graph.
- You use these models to do all sorts of things with your data.

Of course, there is a lot more to it than that, but this is the basic idea. So let's take a closer look at the different parts of `pyneo4j-ogm` and how to use them.

> **Note:** All of the examples in this documentation assume that you have already connected to a database and registered your models with the client like shown in the [`quickstart guide`](https://github.com/groc-prog/pyneo4j-ogm/blob/develop?tab=readme-ov-file#quickstart). The models used in the following examples will build upon the ones defined there. If you are new to [`Neo4j`](https://neo4j.com/docs/) or [`Cypher`](https://neo4j.com/docs/cypher-manual/current/) in general, you should get a basic understanding of how to use them before continuing.

### A note on Pydantic version support

As of version [`v0.3.0`](https://github.com/groc-prog/pyneo4j-ogm/blob/develop/CHANGELOG.md#whats-changed-in-v030-2023-11-30), pyneo4j-ogm now supports both `Pydantic 1.10+ and 2+`. All core features of pydantic should work, meaning full support for model serialization, validation and schema generation.

Should you find any issues or run into any problems, feel free to open a issue!
