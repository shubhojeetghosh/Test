"""Shared pytest configuration.

Current application regression tests install dependencies backed by a
temporary SQLite database. The production FastAPI app has no USE_DB switch;
test isolation is configured explicitly by those test fixtures.
"""
