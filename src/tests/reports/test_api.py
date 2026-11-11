import asyncio

import fastapi
import httpx
import strawberry
import strawberry.fastapi


@strawberry.type
class Query:
    @strawberry.field
    def hello(self) -> str:
        return 'world'


def test_throwaway_schema_answers_a_query() -> None:
    """Strawberry installs and serves a query under the project's Python."""
    app = fastapi.FastAPI()
    app.include_router(
        strawberry.fastapi.GraphQLRouter(strawberry.Schema(query=Query)),
        prefix='/graphql',
    )

    async def post() -> httpx.Response:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url='http://test') as client:
            return await client.post('/graphql', json={'query': '{ hello }'})

    response = asyncio.run(post())
    assert response.status_code == 200
    assert response.json() == {'data': {'hello': 'world'}}
