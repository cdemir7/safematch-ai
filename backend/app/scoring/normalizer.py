"""
Value normalization utilities for the scoring engine.

Responsibilities
----------------
- normalize raw neighborhood attribute values onto a common scale
  (e.g. 0-1) before weighted aggregation
- handle missing-value strategies consistently across criteria

Rules
-----
No HTTP calls.
No database access.
No external APIs.
No LLM usage.
Pure deterministic logic.
Fully testable.

Sprint Status
-------------
Architecture phase only.
Implementation planned for Sprint 3.
"""
