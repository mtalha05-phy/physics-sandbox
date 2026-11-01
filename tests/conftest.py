"""Test bootstrap: make `import app` work and keep tests away from real data."""
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
# The live server creates its ScoreManager at import time. Point it at a throw-away file so running the
# tests can never write fake players (the old suite added "testviewer" to the real leaderboard).
os.environ.setdefault("SCORES_PATH", os.path.join(tempfile.mkdtemp(prefix="sq-tests-"), "leaderboard.json"))
