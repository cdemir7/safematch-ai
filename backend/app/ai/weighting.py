"""
Gemini weighting layer.

Responsibilities
----------------
Transform user profile into recommendation weights.

Gemini returns structured output.

Output example
--------------
{
    "deprem_guvenlik": 0.35,
    "ulasim": 0.20,
    "egitim": 0.15
}

Safety rules
------------
Minimum earthquake weight must always be preserved
(see scoring.constants.DEPREM_MIN_WEIGHT).

Sprint Status
-------------
Architecture phase only.
No Gemini integration implemented yet.
Implementation planned for Sprint 3.
"""
