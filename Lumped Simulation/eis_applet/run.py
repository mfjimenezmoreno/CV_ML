#!/usr/bin/env python3
"""
EIS Biosensor — Lumped Circuit Applet
======================================

Entry point. Run with:
    python run.py

Opens the Dash app on http://localhost:8050
"""

import sys
import os

# Ensure the applet package is on the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app


if __name__ == "__main__":
    print("=" * 60)
    print("  EIS Biosensor — Lumped Circuit Model")
    print("  Starting on http://localhost:8050")
    print("=" * 60)
    app.run(debug=True, host="0.0.0.0", port=8050)
