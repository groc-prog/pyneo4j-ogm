## Migrations

As of version [`v0.5.0`](https://github.com/groc-prog/pyneo4j-ogm/blob/develop/CHANGELOG.md#whats-changed-in-v050-2024-02-06), pyneo4j-ogm supports migrations using a built-in migration tool. The migration tool is basic but flexibly, which should cover most use-cases.

### Initializing migrations for your project

To initialize migrations for your project, you can use the `poetry run pyneo4j_ogm init` command. This will create a `migrations` directory at the given path (which defaults to `./migrations`), which will contain all your migration files.

```bash
poetry run pyneo4j_ogm init --migration-dir ./my/custom/migration/path
```

### Creating a new migration

To create a new migration, you can use the `poetry run pyneo4j_ogm create` command. This will create a new migration file inside the `migrations` directory. The migration file will contain a `up` and `down` function, which you can use to define your migration.

```bash
poetry run pyneo4j_ogm create my_first_migration
```

Both the `up` and `down` functions will receive the client used during the migration as their only arguments. This makes the migrations pretty flexible, since you can not only use the client to execute queries, but also register models on it and use them to execute methods.

> **Note**: When using models inside the migration, you have to make sure that the model used implements the same data structure as the data inside the graph. Otherwise you might run into validation issues.

```python
"""
Auto-generated migration file {name}. Do not
rename this file or the `up` and `down` functions.
"""
from pyneo4j_ogm import Pyneo4jClient


async def up(client: Pyneo4jClient) -> None:
    """
    Write your `UP migration` here.
    """
    await client.cypher("CREATE (n:Node {name: 'John'})")


async def down(client: Pyneo4jClient) -> None:
    """
    Write your `DOWN migration` here.
    """
    await client.cypher("MATCH (n:Node {name: 'John'}) DELETE n")
```

### Running migrations

To run the migrations, you can use the `up` or `down` commands. The `up` command will run all migrations that have not been run yet, while the `down` command will run all migrations in reverse order.

Both commands support a `--up-count` or `--down-count` argument, which can be used to limit the number of migrations to run. By default, the `up` command will run `all pending migration` and the `down` command will roll back the `last migration`.

```bash
poetry run pyneo4j_ogm up --up-count 3
poetry run pyneo4j_ogm down --down-count 2
```

### Listing migrations

The current state of all migrations can be viewed anytime using the `status` command. This will show you all migrations that have been run and all migrations that are pending.

```bash
poetry run pyneo4j_ogm status

## Output
┌─────────────────────────────────────────┬─────────────────────┐
│ Migration                               │ Applied At          │
├─────────────────────────────────────────┼─────────────────────┤
│ 20160608155948-my_awesome_migration     │ 2022-03-04 15:40:22 │
│ 20160608155948-my_fixed_migration       │ 2022-03-04 15:41:13 │
│ 20160608155948-final_fix_i_swear        │ PENDING             │
└─────────────────────────────────────────┴─────────────────────┘
```

### Programmatic usage

The migration tool can also be used programmatically. This can be useful if you want to run migrations inside your application or if you want to integrate the migration tool into your own CLI.

```python
import asyncio
from pyneo4j_ogm.migrations import create, down, init, status, up

## Call with same arguments as you would with cli
init(migration_dir="./my/custom/migration/path")

create("my_first_migration")
asyncio.run(up())
```
