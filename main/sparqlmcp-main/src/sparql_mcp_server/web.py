import asyncio
import logging
from fastapi import FastAPI
import uvicorn

app = FastAPI(title="SPARQL-MCP Web")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


async def run() -> None:
    logging.basicConfig(level=logging.INFO)
    logging.info("SPARQL-MCP web server starting on http://0.0.0.0:8765 …")
    config = uvicorn.Config(app, host="0.0.0.0", port=8765, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()
