"""Dependency Injection module."""

from .container import Container, create_container, init_database

__all__ = [
    "Container",
    "create_container",
    "init_database",
]
