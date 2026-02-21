"""Common test fixtures."""

import pytest
from common.database import create_engine_from_url, create_session_factory
from common.models import Base, IntIDMixin
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column


class SampleEntity(IntIDMixin, Base):
    """A sample entity for testing BaseRepository."""

    __tablename__ = "sample_entity"

    name: Mapped[str] = mapped_column(String(50))


@pytest.fixture
def engine():
    eng = create_engine_from_url("sqlite:///:memory:")
    Base.metadata.create_all(eng)
    yield eng
    Base.metadata.drop_all(eng)
    eng.dispose()


@pytest.fixture
def session(engine):
    factory = create_session_factory(engine)
    sess = factory()
    yield sess
    sess.close()
