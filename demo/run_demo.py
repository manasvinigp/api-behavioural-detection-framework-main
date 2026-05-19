"""Small helper to show demo commands and (optionally) run them.

This script prints the commands to run the local demo and can be extended
to orchestrate the mock API and validation pipeline.
"""
import os
import shlex
import subprocess
from pathlib import Path


def print_commands():
    repo = Path(__file__).resolve().parents[1]
    print("Demo commands (run in project root):\n")
    print("# Activate venv on Windows:\n.\\.venv\\Scripts\\activate\n")
    print("# Install project:\n", "pip install -e .\n")
    print("# Start mock API:\n", "python mock_apis/users_api.py\n")
    print("# Run validation:\n",
          "acv validate --spec openapi/sample_users_api.yaml --url http://localhost:8000\n")


def main():
    print_commands()


if __name__ == '__main__':
    main()
