"""Tests for BaseRepository CRUD operations."""

import pytest
from common.exceptions import EntityNotFoundError
from common.repository import BaseRepository
from conftest import SampleEntity


class TestBaseRepository:
    def test_create_and_get_by_id(self, session):
        repo = BaseRepository(session, SampleEntity)
        entity = SampleEntity(name="test")

        created = repo.create(entity)
        session.commit()

        found = repo.get_by_id(created.id)
        assert found is not None
        assert found.name == "test"

    def test_get_by_id_returns_none(self, session):
        repo = BaseRepository(session, SampleEntity)
        assert repo.get_by_id(999) is None

    def test_get_or_raise_found(self, session):
        repo = BaseRepository(session, SampleEntity)
        entity = repo.create(SampleEntity(name="exists"))
        session.commit()

        found = repo.get_or_raise(entity.id)
        assert found.name == "exists"

    def test_get_or_raise_not_found(self, session):
        repo = BaseRepository(session, SampleEntity)
        with pytest.raises(EntityNotFoundError):
            repo.get_or_raise(999)

    def test_list_all(self, session):
        repo = BaseRepository(session, SampleEntity)
        for i in range(5):
            repo.create(SampleEntity(name=f"item-{i}"))
        session.commit()

        items = repo.list_all()
        assert len(items) == 5

    def test_list_all_with_offset_limit(self, session):
        repo = BaseRepository(session, SampleEntity)
        for i in range(5):
            repo.create(SampleEntity(name=f"item-{i}"))
        session.commit()

        items = repo.list_all(offset=2, limit=2)
        assert len(items) == 2

    def test_update(self, session):
        repo = BaseRepository(session, SampleEntity)
        entity = repo.create(SampleEntity(name="old"))
        session.commit()

        repo.update(entity, {"name": "new"})
        session.commit()

        found = repo.get_by_id(entity.id)
        assert found.name == "new"

    def test_delete(self, session):
        repo = BaseRepository(session, SampleEntity)
        entity = repo.create(SampleEntity(name="to-delete"))
        session.commit()

        repo.delete(entity)
        session.commit()

        assert repo.get_by_id(entity.id) is None
