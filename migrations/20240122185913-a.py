"""
Auto-generated migration file 20240115234453_something_awesome.py. Do not
rename this file or the `up` and `down` functions.
"""
from pyneo4j_ogm import Pyneo4jClient


async def up(client: Pyneo4jClient) -> None:
    """
    Write your `UP migration` here.
    """
    await client.cypher("CREATE (:A {foo: 'foo'})")


async def down(client: Pyneo4jClient) -> None:
    """
    Write your `DOWN migration` here.
    """
    await client.cypher("MATCH (n:A) WHERE n.foo = 'foo' DETACH DELETE n")
