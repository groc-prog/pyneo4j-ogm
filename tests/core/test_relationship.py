# pylint: disable=unused-argument, unused-import, redefined-outer-name, protected-access, missing-module-docstring, missing-class-docstring
# pyright: reportGeneralTypeIssues=false

from typing import Any, Dict, List, cast
from unittest.mock import MagicMock, patch

import pytest
from neo4j import AsyncSession
from neo4j.graph import Graph, Node, Relationship
from pydantic import BaseModel
from typing_extensions import LiteralString

from pyneo4j_ogm.core.client import Pyneo4jClient
from pyneo4j_ogm.core.relationship import RelationshipModel, ensure_alive
from pyneo4j_ogm.exceptions import (
    InstanceDestroyed,
    InstanceNotHydrated,
    InvalidFilters,
    NoResultFound,
    UnexpectedEmptyResult,
    UnregisteredModel,
)
from pyneo4j_ogm.fields.relationship_property import check_models_registered
from tests.fixtures.db_setup import (
    Developer,
    Sells,
    WorkedWith,
    client,
    session,
    setup_test_data,
)


async def test_update(client: Pyneo4jClient, session: AsyncSession, setup_test_data):
    relationship: Relationship = [
        result
        for result in setup_test_data[0][1]
        if result.type == "WAS_WORK_BUDDY_WITH" and result["language"] == "Go"
    ][0]

    relationship_model = WorkedWith(**relationship)
    relationship_model._element_id = relationship.element_id
    relationship_model._id = relationship.id
    relationship_model._start_node_element_id = cast(Node, relationship.start_node).element_id
    relationship_model._start_node_id = cast(Node, relationship.start_node).id
    relationship_model._end_node_element_id = cast(Node, relationship.end_node).element_id
    relationship_model._end_node_id = cast(Node, relationship.end_node).id

    relationship_model.language = "TypeScript"
    await relationship_model.update()
    assert relationship_model.language == "TypeScript"
    assert relationship_model._db_properties == {"language": "TypeScript"}

    results = await session.run(
        cast(
            LiteralString,
            f"""
            MATCH ()-[r:{WorkedWith.model_settings().type}]->()
            WHERE elementId(r) = $element_id
            RETURN r
            """,
        ),
        {"element_id": relationship_model._element_id},
    )
    query_result: List[List[Relationship]] = await results.values()
    await results.consume()

    assert len(query_result) == 1
    assert len(query_result[0]) == 1

    relationship_result = query_result[0][0]
    assert relationship_result["language"] == "TypeScript"


async def test_update_no_result(client: Pyneo4jClient, setup_test_data):
    relationship: Relationship = [
        result
        for result in setup_test_data[0][1]
        if result.type == "WAS_WORK_BUDDY_WITH" and result["language"] == "Go"
    ][0]

    relationship_model = WorkedWith(**relationship)
    relationship_model._element_id = relationship.element_id
    relationship_model._id = relationship.id
    relationship_model._start_node_element_id = cast(Node, relationship.start_node).element_id
    relationship_model._start_node_id = cast(Node, relationship.start_node).id
    relationship_model._end_node_element_id = cast(Node, relationship.end_node).element_id
    relationship_model._end_node_id = cast(Node, relationship.end_node).id

    with patch.object(client, "cypher") as mock_cypher:
        mock_cypher.return_value = ([], [])

        with pytest.raises(UnexpectedEmptyResult):
            relationship_model.language = "TypeScript"
            await relationship_model.update()


async def test_update_one(client: Pyneo4jClient, session: AsyncSession, setup_test_data):
    result = await WorkedWith.update_one({"language": "Rust"}, {"language": "Python"})
    assert result is not None
    assert isinstance(result, WorkedWith)
    assert result.language == "Python"

    results = await session.run(
        """
        MATCH ()-[r:WAS_WORK_BUDDY_WITH]->()
        WHERE r.language = $language
        RETURN r
        """,
        {"language": "Python"},
    )

    query_result = await results.values()
    await results.consume()

    assert len(query_result) == 1


async def test_update_one_return_new(client: Pyneo4jClient, setup_test_data):
    result = await WorkedWith.update_one({"language": "Rust"}, {"language": "Python"}, new=True)
    assert result is not None
    assert isinstance(result, WorkedWith)
    assert result.language == "Rust"


async def test_update_one_no_match(client: Pyneo4jClient, setup_test_data):
    result = await WorkedWith.update_one({"language": "non-existent"}, {"language": "non-existent"})
    assert result is None

    with pytest.raises(NoResultFound):
        await WorkedWith.update_one({"language": "non-existent"}, {"language": "non-existent"}, raise_on_empty=True)


async def test_update_one_missing_filter(client: Pyneo4jClient, setup_test_data):
    with pytest.raises(InvalidFilters):
        await WorkedWith.update_one({}, {})


async def test_update_one_raw_result(client: Pyneo4jClient):
    await client.register_models([WorkedWith])

    with patch.object(client, "cypher") as mock_cypher:
        mock_start_node = Node(
            graph=Graph(),
            element_id="start-element-id",
            id_=2,
            properties={},
        )
        mock_end_node = Node(
            graph=Graph(),
            element_id="end-element-id",
            id_=3,
            properties={},
        )

        mock_relationship = Relationship(
            graph=Graph(),
            element_id="element-id",
            id_=1,
            properties={"language": "Go"},
        )
        setattr(mock_relationship, "_start_node", mock_start_node)
        setattr(mock_relationship, "_end_node", mock_end_node)

        mock_cypher.return_value = (
            [[mock_relationship]],
            [],
        )

        result = await WorkedWith.update_one({"language": "Rust"}, {"language": "Go"})
        assert result is not None
        assert isinstance(result, WorkedWith)
        assert result.language == "Go"
        assert result._start_node_element_id == mock_start_node.element_id
        assert result._start_node_id == mock_start_node.id
        assert result._end_node_element_id == mock_end_node.element_id
        assert result._end_node_id == mock_end_node.id


async def test_update_many(client: Pyneo4jClient, session: AsyncSession, setup_test_data):
    results = await WorkedWith.update_many({"language": "Rust"}, {"language": "Python"})
    assert len(results) == 2
    assert all(isinstance(result, WorkedWith) for result in results)
    assert all(result.language == "Python" for result in results)

    results = await session.run(
        """
        MATCH ()-[r:WAS_WORK_BUDDY_WITH]->()
        WHERE r.language = $language
        RETURN r
        """,
        {"language": "Python"},
    )

    query_result = await results.values()
    await results.consume()

    assert len(query_result) == 0


async def test_update_many_return_new(client: Pyneo4jClient, setup_test_data):
    results = await WorkedWith.update_many({"language": "Rust"}, {"language": "Python"}, new=True)
    assert len(results) == 2
    assert all(isinstance(result, WorkedWith) for result in results)
    assert all(result.language == "Rust" for result in results)


async def test_update_many_no_match(client: Pyneo4jClient, setup_test_data):
    results = await WorkedWith.update_many({"language": "non-existent"}, {"language": "non-existent"})
    assert len(results) == 0


async def test_update_many_raw_result(client: Pyneo4jClient):
    await client.register_models([WorkedWith])

    with patch.object(client, "cypher") as mock_cypher:
        mock_start_node = Node(
            graph=Graph(),
            element_id="start-element-id",
            id_=2,
            properties={},
        )
        mock_end_node = Node(
            graph=Graph(),
            element_id="end-element-id",
            id_=3,
            properties={},
        )

        mock_relationship = Relationship(
            graph=Graph(),
            element_id="element-id",
            id_=1,
            properties={"language": "Go"},
        )
        setattr(mock_relationship, "_start_node", mock_start_node)
        setattr(mock_relationship, "_end_node", mock_end_node)

        mock_cypher.return_value = (
            [[mock_relationship, None]],
            [],
        )

        results = await WorkedWith.update_many({"language": "Rust"}, {"language": "Go"})
        assert len(results) == 1
        assert isinstance(results[0], WorkedWith)
        assert results[0].language == "Go"
        assert results[0]._start_node_element_id == mock_start_node.element_id
        assert results[0]._start_node_id == mock_start_node.id
        assert results[0]._end_node_element_id == mock_end_node.element_id
        assert results[0]._end_node_id == mock_end_node.id


async def test_start_node(client: Pyneo4jClient, setup_test_data):
    relationship: Relationship = [
        result
        for result in setup_test_data[0][1]
        if result.type == "WAS_WORK_BUDDY_WITH" and result["language"] == "Go"
    ][0]
    node = cast(Node, relationship.start_node)

    relationship_model = WorkedWith(**relationship)
    relationship_model._element_id = relationship.element_id
    relationship_model._id = relationship.id
    relationship_model._start_node_element_id = cast(Node, relationship.start_node).element_id
    relationship_model._start_node_id = cast(Node, relationship.start_node).id
    relationship_model._end_node_element_id = cast(Node, relationship.end_node).element_id
    relationship_model._end_node_id = cast(Node, relationship.end_node).id

    relationship_model.language = "TypeScript"
    start_node = cast(Developer, await relationship_model.start_node())
    assert isinstance(start_node, Developer)
    assert start_node._element_id == node.element_id
    assert start_node._id == node.id


async def test_start_node_no_result(client: Pyneo4jClient, setup_test_data):
    relationship: Relationship = [
        result
        for result in setup_test_data[0][1]
        if result.type == "WAS_WORK_BUDDY_WITH" and result["language"] == "Go"
    ][0]

    relationship_model = WorkedWith(**relationship)
    relationship_model._element_id = relationship.element_id
    relationship_model._id = relationship.id
    relationship_model._start_node_element_id = cast(Node, relationship.start_node).element_id
    relationship_model._start_node_id = cast(Node, relationship.start_node).id
    relationship_model._end_node_element_id = cast(Node, relationship.end_node).element_id
    relationship_model._end_node_id = cast(Node, relationship.end_node).id

    with patch.object(client, "cypher") as mock_cypher:
        mock_cypher.return_value = ([], [])

        with pytest.raises(UnexpectedEmptyResult):
            await relationship_model.start_node()


async def test_refresh(client: Pyneo4jClient, setup_test_data):
    relationship: Relationship = [
        result
        for result in setup_test_data[0][1]
        if result.type == "WAS_WORK_BUDDY_WITH" and result["language"] == "Go"
    ][0]

    relationship_model = WorkedWith(**relationship)
    relationship_model._element_id = relationship.element_id
    relationship_model._id = relationship.id
    relationship_model._start_node_element_id = cast(Node, relationship.start_node).element_id
    relationship_model._start_node_id = cast(Node, relationship.start_node).id
    relationship_model._end_node_element_id = cast(Node, relationship.end_node).element_id
    relationship_model._end_node_id = cast(Node, relationship.end_node).id

    relationship_model.language = "TypeScript"
    await relationship_model.refresh()
    assert relationship_model.language == "Go"


async def test_refresh_no_result(client: Pyneo4jClient, setup_test_data):
    relationship: Relationship = [
        result
        for result in setup_test_data[0][1]
        if result.type == "WAS_WORK_BUDDY_WITH" and result["language"] == "Go"
    ][0]

    relationship_model = WorkedWith(**relationship)
    relationship_model._element_id = relationship.element_id
    relationship_model._id = relationship.id
    relationship_model._start_node_element_id = cast(Node, relationship.start_node).element_id
    relationship_model._start_node_id = cast(Node, relationship.start_node).id
    relationship_model._end_node_element_id = cast(Node, relationship.end_node).element_id
    relationship_model._end_node_id = cast(Node, relationship.end_node).id

    with patch.object(client, "cypher") as mock_cypher:
        mock_cypher.return_value = ([], [])

        with pytest.raises(UnexpectedEmptyResult):
            relationship_model.language = "TypeScript"
            await relationship_model.refresh()


@pytest.fixture()
def mock_relationship_property():
    mock_source_node = MagicMock()

    return MagicMock(
        _client=MagicMock(models={mock_source_node.__class__}),
        _source_node=mock_source_node,
        _target_model_name=MagicMock(),
        _relationship_model=MagicMock(),
    )


async def test_unregistered_source_model(mock_relationship_property):
    mock_relationship_property._client.models = {}

    with pytest.raises(UnregisteredModel):

        @check_models_registered
        async def test_function(self):
            pass

        await test_function(mock_relationship_property)


async def test_unregistered_target_model(mock_relationship_property):
    mock_relationship_property._target_model = None

    with pytest.raises(UnregisteredModel):

        @check_models_registered
        async def test_function(self):
            pass

        await test_function(mock_relationship_property)


async def test_unregistered_relationship_model(mock_relationship_property):
    mock_relationship_property._relationship_model = None

    with pytest.raises(UnregisteredModel):

        @check_models_registered
        async def test_function(self):
            pass

        await test_function(mock_relationship_property)


@pytest.fixture()
def use_deflate_inflate_model():
    class NestedModel(BaseModel):
        name: str = "test"

    class DeflateInflateModel(RelationshipModel):
        normal_field: bool = True
        nested_model: NestedModel = NestedModel()
        dict_field: Dict[str, Any] = {"test_str": "test", "test_int": 12}
        list_field: list = ["test", 12, {"test": "test"}]

    setattr(DeflateInflateModel, "_client", None)

    return DeflateInflateModel


@pytest.fixture()
def use_test_relationship():
    setattr(WorkedWith, "_client", None)
    relationship_model = WorkedWith(language="Go")
    relationship_model._element_id = "4:08f8a347-1856-487c-8705-26d2b4a69bb7:6"
    relationship_model._id = 6
    relationship_model._start_node_element_id = "4:08f8a347-1856-487c-8705-26d2b4a69bb7:7"
    relationship_model._start_node_id = 7
    relationship_model._end_node_element_id = "4:08f8a347-1856-487c-8705-26d2b4a69bb7:8"
    relationship_model._end_node_id = 8

    return relationship_model


def test_type_fallback():
    assert Sells._settings.type == "SELLS"


def test_ensure_alive_decorator():
    class EnsureAliveTest:
        _destroyed = False
        _element_id = None
        _id = None
        _start_node_element_id = None
        _end_node_element_id = None
        _start_node_id = None
        _end_node_id = None

        @classmethod
        @ensure_alive
        def test_func(cls):
            return True

    with pytest.raises(InstanceNotHydrated):
        EnsureAliveTest.test_func()

    setattr(EnsureAliveTest, "_element_id", "4:08f8a347-1856-487c-8705-26d2b4a69bb7:18")
    setattr(EnsureAliveTest, "_id", 1)
    with pytest.raises(InstanceNotHydrated):
        EnsureAliveTest.test_func()

    setattr(EnsureAliveTest, "_start_node_element_id", "4:08f8a347-1856-487c-8705-26d2b4a69bb7:17")
    setattr(EnsureAliveTest, "_start_node_id", 3)
    setattr(EnsureAliveTest, "_end_node_element_id", "4:08f8a347-1856-487c-8705-26d2b4a69bb7:19")
    setattr(EnsureAliveTest, "_end_node_id", 2)
    setattr(EnsureAliveTest, "_destroyed", True)
    with pytest.raises(InstanceDestroyed):
        EnsureAliveTest.test_func()

    setattr(EnsureAliveTest, "_destroyed", False)
    assert EnsureAliveTest.test_func()


def test_start_node_element_id(use_test_relationship):
    assert use_test_relationship.start_node_element_id == "4:08f8a347-1856-487c-8705-26d2b4a69bb7:7"


def test_end_node_element_id(use_test_relationship):
    assert use_test_relationship.end_node_element_id == "4:08f8a347-1856-487c-8705-26d2b4a69bb7:8"


def test_start_node_id(use_test_relationship):
    assert use_test_relationship.start_node_id == 7


def test_end_node_id(use_test_relationship):
    assert use_test_relationship.end_node_id == 8


def test_deflate(use_deflate_inflate_model):
    model = use_deflate_inflate_model()
    deflated = model._deflate()

    assert deflated["normal_field"]
    assert deflated["nested_model"] == '{"name": "test"}'
    assert deflated["dict_field"] == '{"test_str": "test", "test_int": 12}'


def test_inflate(use_deflate_inflate_model):
    mock_start_node = Node(
        graph=Graph(),
        element_id="start-element-id",
        id_=2,
        properties={},
    )
    mock_end_node = Node(
        graph=Graph(),
        element_id="end-element-id",
        id_=3,
        properties={},
    )
    mock_relationship = Relationship(
        element_id="4:08f8a347-1856-487c-8705-26d2b4a69bb7:6",
        id_=6,
        graph=Graph(),
        properties={
            "normal_field": True,
            "nested_model": '{"name": "test"}',
            "dict_field": '{"test_str": "test", "test_int": 12}',
            "list_field": ["test", 12, '{"test": "test"}'],
        },
    )
    setattr(mock_relationship, "_start_node", mock_start_node)
    setattr(mock_relationship, "_end_node", mock_end_node)

    inflated = use_deflate_inflate_model._inflate(mock_relationship)

    assert inflated.normal_field
    assert inflated.nested_model.name == "test"
    assert inflated.dict_field["test_str"] == "test"
    assert inflated.dict_field["test_int"] == 12
    assert inflated.list_field[0] == "test"
    assert inflated.list_field[1] == 12
    assert inflated.list_field[2] == {"test": "test"}


def test_iter():
    class Rel(RelationshipModel):
        foo_prop: str = "foo"
        bar_prop: int = 1

    setattr(Rel, "_client", None)

    model = Rel()
    setattr(model, "_element_id", "4:08f8a347-1856-487c-8705-26d2b4a69bb7:18")
    setattr(model, "_id", 18)
    setattr(model, "_start_node_element_id", "4:08f8a347-1856-487c-8705-26d2b4a69bb7:17")
    setattr(model, "_start_node_id", 17)
    setattr(model, "_end_node_element_id", "4:08f8a347-1856-487c-8705-26d2b4a69bb7:19")
    setattr(model, "_end_node_id", 19)

    for attr_name, attr_value in model:
        assert attr_name in [
            "foo_prop",
            "bar_prop",
            "element_id",
            "id",
            "start_node_element_id",
            "start_node_id",
            "end_node_element_id",
            "end_node_id",
        ]
        assert attr_value in [
            "foo",
            1,
            "4:08f8a347-1856-487c-8705-26d2b4a69bb7:18",
            18,
            "4:08f8a347-1856-487c-8705-26d2b4a69bb7:17",
            17,
            "4:08f8a347-1856-487c-8705-26d2b4a69bb7:19",
            19,
        ]


async def test_find_one(client: Pyneo4jClient, setup_test_data):
    result = await WorkedWith.find_one({"language": "Go"})
    assert result is not None
    assert isinstance(result, WorkedWith)
    assert result.language == "Go"


async def test_find_one_no_match(client: Pyneo4jClient, setup_test_data):
    result = await WorkedWith.find_one({"language": "non-existent"})
    assert result is None

    with pytest.raises(NoResultFound):
        await WorkedWith.find_one({"language": "non-existent"}, raise_on_empty=True)


async def test_find_one_missing_filter(client: Pyneo4jClient, setup_test_data):
    with pytest.raises(InvalidFilters):
        await WorkedWith.find_one({})


async def test_find_one_raw_result(client: Pyneo4jClient):
    await client.register_models([WorkedWith])

    with patch.object(client, "cypher") as mock_cypher:
        mock_start_node = Node(
            graph=Graph(),
            element_id="start-element-id",
            id_=2,
            properties={},
        )
        mock_end_node = Node(
            graph=Graph(),
            element_id="end-element-id",
            id_=3,
            properties={},
        )

        mock_relationship = Relationship(
            graph=Graph(),
            element_id="element-id",
            id_=1,
            properties={"language": "Go"},
        )
        setattr(mock_relationship, "_start_node", mock_start_node)
        setattr(mock_relationship, "_end_node", mock_end_node)

        mock_cypher.return_value = (
            [[mock_relationship]],
            [],
        )

        result = await WorkedWith.find_one({"language": "Go"})
        assert result is not None
        assert isinstance(result, WorkedWith)
        assert result.language == "Go"
        assert result._start_node_element_id == mock_start_node.element_id
        assert result._start_node_id == mock_start_node.id
        assert result._end_node_element_id == mock_end_node.element_id
        assert result._end_node_id == mock_end_node.id


async def test_find_one_projections(client: Pyneo4jClient, setup_test_data):
    result = await WorkedWith.find_one({"language": "Go"}, {"lang": "language"})
    assert result is not None
    assert isinstance(result, dict)
    assert "lang" in result
    assert result["lang"] == "Go"


async def test_end_node(client: Pyneo4jClient, setup_test_data):
    relationship: Relationship = [
        result
        for result in setup_test_data[0][1]
        if result.type == "WAS_WORK_BUDDY_WITH" and result["language"] == "Go"
    ][0]
    node = cast(Node, relationship.end_node)

    relationship_model = WorkedWith(**relationship)
    relationship_model._element_id = relationship.element_id
    relationship_model._id = relationship.id
    relationship_model._start_node_element_id = cast(Node, relationship.start_node).element_id
    relationship_model._start_node_id = cast(Node, relationship.start_node).id
    relationship_model._end_node_element_id = cast(Node, relationship.end_node).element_id
    relationship_model._end_node_id = cast(Node, relationship.end_node).id

    relationship_model.language = "TypeScript"
    end_node = cast(Developer, await relationship_model.end_node())
    assert isinstance(end_node, Developer)
    assert end_node._element_id == node.element_id
    assert end_node._id == node.id


async def test_end_node_no_result(client: Pyneo4jClient, setup_test_data):
    relationship: Relationship = [
        result
        for result in setup_test_data[0][1]
        if result.type == "WAS_WORK_BUDDY_WITH" and result["language"] == "Go"
    ][0]

    relationship_model = WorkedWith(**relationship)
    relationship_model._element_id = relationship.element_id
    relationship_model._id = relationship.id
    relationship_model._start_node_element_id = cast(Node, relationship.start_node).element_id
    relationship_model._start_node_id = cast(Node, relationship.start_node).id
    relationship_model._end_node_element_id = cast(Node, relationship.end_node).element_id
    relationship_model._end_node_id = cast(Node, relationship.end_node).id

    with patch.object(client, "cypher") as mock_cypher:
        mock_cypher.return_value = ([], [])

        with pytest.raises(UnexpectedEmptyResult):
            await relationship_model.end_node()


async def test_delete(client: Pyneo4jClient, session: AsyncSession, setup_test_data):
    relationship: Relationship = [
        result
        for result in setup_test_data[0][1]
        if result.type == "WAS_WORK_BUDDY_WITH" and result["language"] == "Go"
    ][0]

    relationship_model = WorkedWith(**relationship)
    relationship_model._element_id = relationship.element_id
    relationship_model._id = relationship.id
    relationship_model._start_node_element_id = cast(Node, relationship.start_node).element_id
    relationship_model._start_node_id = cast(Node, relationship.start_node).id
    relationship_model._end_node_element_id = cast(Node, relationship.end_node).element_id
    relationship_model._end_node_id = cast(Node, relationship.end_node).id

    await relationship_model.delete()
    assert relationship_model._destroyed

    results = await session.run(
        cast(
            LiteralString,
            f"""
            MATCH ()-[r:{WorkedWith.model_settings().type}]->()
            WHERE elementId(r) = $element_id
            RETURN r
            """,
        ),
        {"element_id": relationship_model._element_id},
    )
    query_result: List[List[Relationship]] = await results.values()
    await results.consume()

    assert len(query_result) == 0


async def test_delete_one(client: Pyneo4jClient, session: AsyncSession, setup_test_data):
    result = await WorkedWith.delete_one({"language": "Javascript"})
    assert result == 1

    results = await session.run(
        """
        MATCH ()-[r:WAS_WORK_BUDDY_WITH]->()
        WHERE r.language = $language
        RETURN r
        """,
        {"language": "Javascript"},
    )

    query_result = await results.values()
    await results.consume()

    assert len(query_result) == 1


async def test_delete_one_no_match(client: Pyneo4jClient, session: AsyncSession, setup_test_data):
    result = await WorkedWith.delete_one({"language": "I dont exist"})
    assert result == 0

    with pytest.raises(NoResultFound):
        await WorkedWith.delete_one({"language": "I dont exist"}, raise_on_empty=True)

    results = await session.run(
        """
        MATCH ()-[r:WAS_WORK_BUDDY_WITH]->()
        RETURN DISTINCT r
        """,
    )

    query_result = await results.values()
    await results.consume()

    assert len(query_result) == 7


async def test_delete_one_no_result(client: Pyneo4jClient, session: AsyncSession, setup_test_data):
    with patch.object(client, "cypher") as mock_cypher:
        mock_cypher.return_value = [[], []]

        with pytest.raises(UnexpectedEmptyResult):
            await WorkedWith.delete_one({"language": "non-existent"})

    results = await session.run(
        """
        MATCH ()-[r:WAS_WORK_BUDDY_WITH]->()
        WHERE r.language = $language
        RETURN r
        """,
        {"language": "Javascript"},
    )

    query_result = await results.values()
    await results.consume()

    assert len(query_result) == 2


async def test_delete_one_missing_filter(client: Pyneo4jClient, setup_test_data):
    with pytest.raises(InvalidFilters):
        await WorkedWith.delete_one({})


async def test_delete_many(client: Pyneo4jClient, session: AsyncSession, setup_test_data):
    result = await WorkedWith.delete_many({"language": "Javascript"})
    assert result == 2

    results = await session.run(
        """
        MATCH ()-[r:WAS_WORK_BUDDY_WITH]->()
        WHERE r.language = $language
        RETURN r
        """,
        {"language": "Javascript"},
    )

    query_result = await results.values()
    await results.consume()

    assert len(query_result) == 0


async def test_delete_many_no_match(client: Pyneo4jClient, session: AsyncSession, setup_test_data):
    result = await WorkedWith.delete_many({"language": "non-existent"})
    assert result == 0

    results = await session.run(
        """
        MATCH ()-[r:WAS_WORK_BUDDY_WITH]->()
        WHERE r.language = $language
        RETURN r
        """,
        {"language": "Javascript"},
    )

    query_result = await results.values()
    await results.consume()

    assert len(query_result) == 2


async def test_delete_many_no_results(client: Pyneo4jClient, session: AsyncSession, setup_test_data):
    with patch.object(client, "cypher") as mock_cypher:
        mock_cypher.return_value = [[], []]

        with pytest.raises(UnexpectedEmptyResult):
            await WorkedWith.delete_many({"language": "non-existent"})


async def test_count(client: Pyneo4jClient, setup_test_data):
    result = await WorkedWith.count({"language": "Python"})
    assert result == 2


async def test_count_no_match(client: Pyneo4jClient, setup_test_data):
    result = await WorkedWith.count({"language": "non-existent"})
    assert result == 0


async def test_count_no_query_result(client: Pyneo4jClient, setup_test_data):
    with patch.object(client, "cypher") as mock_cypher:
        mock_cypher.return_value = [[], []]
        with pytest.raises(UnexpectedEmptyResult):
            await WorkedWith.count({})


async def test_find_many(client: Pyneo4jClient, setup_test_data):
    results = await WorkedWith.find_many({"language": "Javascript"})
    assert len(results) == 2
    assert all(isinstance(result, WorkedWith) for result in results)
    assert all(cast(WorkedWith, result).language == "Javascript" for result in results)


async def test_find_many_no_match(client: Pyneo4jClient, setup_test_data):
    results = await WorkedWith.find_many({"language": "non-existent"})
    assert len(results) == 0


async def test_find_many_raw_result(client: Pyneo4jClient):
    await client.register_models([WorkedWith])

    with patch.object(client, "cypher") as mock_cypher:
        mock_start_node = Node(
            graph=Graph(),
            element_id="start-element-id",
            id_=2,
            properties={},
        )
        mock_end_node = Node(
            graph=Graph(),
            element_id="end-element-id",
            id_=3,
            properties={},
        )

        mock_relationship = Relationship(
            graph=Graph(),
            element_id="element-id",
            id_=1,
            properties={"language": "Go"},
        )
        setattr(mock_relationship, "_start_node", mock_start_node)
        setattr(mock_relationship, "_end_node", mock_end_node)

        mock_cypher.return_value = (
            [[mock_relationship, None]],
            [],
        )

        results = await WorkedWith.find_many({"language": "Go"})
        assert len(results) == 1
        assert isinstance(results[0], WorkedWith)
        assert results[0].language == "Go"
        assert results[0]._start_node_element_id == mock_start_node.element_id
        assert results[0]._start_node_id == mock_start_node.id
        assert results[0]._end_node_element_id == mock_end_node.element_id
        assert results[0]._end_node_id == mock_end_node.id


async def test_find_many_projections(client: Pyneo4jClient, setup_test_data):
    results = await WorkedWith.find_many({"language": "Javascript"}, {"lang": "language"})
    assert len(results) == 2
    assert all(isinstance(result, dict) for result in results)
    assert all("lang" in cast(dict, result) for result in results)
    assert all(cast(dict, result)["lang"] == "Javascript" for result in results)


async def test_find_many_options(client: Pyneo4jClient, setup_test_data):
    results = await WorkedWith.find_many({"language": "Javascript"}, options={"limit": 1})
    assert len(results) == 1
    assert all(isinstance(result, WorkedWith) for result in results)
    assert all(cast(WorkedWith, result).language == "Javascript" for result in results)


async def test_find_many_options_and_projections(client: Pyneo4jClient, setup_test_data):
    results = await WorkedWith.find_many(options={"skip": 1}, projections={"lang": "language"})
    assert len(results) == 6
    assert all(isinstance(result, dict) for result in results)
    assert all("lang" in cast(Dict, result) for result in results)
