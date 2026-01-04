"""TelemetryX Python Brain - gRPC Server Entry Point.

Run with: python -m telemetryx.grpc_server
"""

import asyncio

from telemetryx.grpc_server.server import serve


def main() -> None:
    """Entry point for the gRPC server."""
    asyncio.run(serve())


if __name__ == "__main__":
    main()
