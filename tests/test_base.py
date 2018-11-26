import asyncio

import pytest

from ai.backend.client.base import BaseFunction, api_function
from ai.backend.client.session import Session, AsyncSession


class DummyFunction:

    session = None

    @api_function
    @classmethod
    async def get_or_create(cls):
        await asyncio.sleep(0)
        return 'created'

    @api_function
    async def calculate(self):
        await asyncio.sleep(0)
        return 'done'


def test_api_function_metaclass():
    # Here, we repeat intentionally the same stuffs
    # to check if our metaclass works across multiple
    # re-definition and re-instantiation scenarios.

    with Session() as session:
        Dummy = type('DummyFunction', (BaseFunction, ), {
            **DummyFunction.__dict__,
            'session': session,
        })

        assert Dummy.session is session
        assert Dummy().session is session

        assert Dummy.get_or_create() == 'created'
        assert Dummy().calculate() == 'done'
        assert Dummy.get_or_create() == 'created'
        assert Dummy().calculate() == 'done'

    with Session() as session:
        Dummy = type('DummyFunction', (BaseFunction, ), {
            **DummyFunction.__dict__,
            'session': session,
        })

        assert Dummy.session is session
        assert Dummy().session is session

        assert Dummy.get_or_create() == 'created'
        assert Dummy().calculate() == 'done'
        assert Dummy.get_or_create() == 'created'
        assert Dummy().calculate() == 'done'


@pytest.mark.asyncio
async def test_api_function_metaclass_async():

    async with AsyncSession() as session:
        Dummy = type('DummyFunction', (BaseFunction, ), {
            **DummyFunction.__dict__,
            'session': session,
        })

        assert Dummy.session is session
        assert Dummy().session is session

        assert await Dummy.get_or_create() == 'created'
        assert await Dummy().calculate() == 'done'
        assert await Dummy.get_or_create() == 'created'
        assert await Dummy().calculate() == 'done'

    async with AsyncSession() as session:
        Dummy = type('DummyFunction', (BaseFunction, ), {
            **DummyFunction.__dict__,
            'session': session,
        })

        assert Dummy.session is session
        assert Dummy().session is session

        assert await Dummy.get_or_create() == 'created'
        assert await Dummy().calculate() == 'done'
        assert await Dummy.get_or_create() == 'created'
        assert await Dummy().calculate() == 'done'
