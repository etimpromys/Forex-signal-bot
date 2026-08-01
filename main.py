"""
main.py
Entry point. Run this directly for a local test, or on a GitHub Actions schedule.

Usage:
    python main.py
"""

import engine

if __name__ == "__main__":
    engine.run_once()
