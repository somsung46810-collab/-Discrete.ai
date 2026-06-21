"""Compatibility launcher for the embedded CyGlobs runtime."""

from cyglobs_app import create_server, main

__all__ = ["create_server", "main"]


if __name__ == "__main__":
    main()
