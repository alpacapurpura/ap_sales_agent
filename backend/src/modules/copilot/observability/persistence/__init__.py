"""Persistence layer — SQLAlchemy repositories for the observability tables.

Every repository takes a ``Session`` and exposes pure CRUD with tenant
isolation where applicable. No domain logic; that lives in
``recording`` / ``cost`` / ``reporting`` / ``pricing``.
"""
