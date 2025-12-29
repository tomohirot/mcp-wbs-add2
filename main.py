"""
Cloud Functions entry point
Routes requests to appropriate handlers based on path
"""

from flask import Request
from src.main import health_check, wbs_create as wbs_create_handler


def wbs_create(request: Request):
    """
    Main Cloud Functions entry point
    Routes requests based on path:
    - /health -> health_check
    - /* -> wbs_create_handler
    """
    # Get request path
    path = request.path

    # Route to health check
    if path == "/health" or path.endswith("/health"):
        return health_check(request)

    # Route to WBS creation
    return wbs_create_handler(request)


__all__ = ["wbs_create"]
