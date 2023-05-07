import pytest

from skim import server


@pytest.fixture
async def client(aiohttp_client):
    app = server.create_application()
    return await aiohttp_client(app)


async def test_health(client):
    response = await client.get('/health')
    assert response.status == 204
