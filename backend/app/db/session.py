"""
Database session management.

Responsibilities
----------------
- create the SQLAlchemy 2 engine (with GeoAlchemy2 support for
  PostGIS geometry columns)
- provide a session factory / dependency for request-scoped sessions
- manage connection pooling configuration

Sprint Status
-------------
Architecture phase only.
No database connection implemented yet.
Implementation planned for Sprint 3.
"""
