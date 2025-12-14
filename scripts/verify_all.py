#!/usr/bin/env python3
"""
Global verification script for Tegmen project.
Runs unit tests, routing verification, and integration tests.
"""

import subprocess
import sys
import time
from typing import List


def run_command(command: List[str], description: str) -> bool:
    """Run a command and print status."""
    print(f"\n{'=' * 50}")
    print(f"🚀 Running: {description}")
    print(f"   Command: {' '.join(command)}")
    print(f"{'=' * 50}\n")

    start_time = time.time()
    try:
        # Use simple subprocess.run for now, streaming output would be better but this is simpler
        result = subprocess.run(
            command,
            check=False,
            capture_output=False,  # Let output flow to stdout
        )
        duration = time.time() - start_time

        if result.returncode == 0:
            print(f"\n✅ {description} PASSED ({duration:.2f}s)")
            return True
        else:
            print(f"\n❌ {description} FAILED (Exit Code: {result.returncode})")
            return False

    except Exception as e:
        print(f"\n❌ {description} ERROR: {e}")
        return False


def main():
    print("🔍 Starting Global Verification for Tegmen...")

    # 1. Unit Tests
    # We use PYTHONPATH=. to ensure src is discoverable
    unit_tests_passed = run_command(
        [
            "uv",
            "run",
            "pytest",
            "tests/test_agent_acadomie.py",
            "tests/test_agent_explorer.py",
            "tests/test_gourmet_tools.py",
        ],
        "Unit Tests (Agents)",
    )

    # 2. Routing Verification
    routing_passed = run_command(
        ["uv", "run", "tests/verify_routing.py"], "Semantic Routing Verification"
    )

    # 3. Integration Tests
    # We check if docker is likely running (via a simple check or just try)
    # Ideally we'd check if ports 8000-8003 are open, but let's just run the script
    integration_passed = run_command(
        ["uv", "run", "tests/test_integration_a2a.py"],
        "End-to-End Integration Tests (A2A)",
    )

    print(f"\n{'=' * 50}")
    print("📊 VERIFICATION SUMMARY")
    print(f"{'=' * 50}")

    all_passed = unit_tests_passed and routing_passed and integration_passed

    print(f"Unit Tests:      {'✅ PASS' if unit_tests_passed else '❌ FAIL'}")
    print(f"Routing Check:   {'✅ PASS' if routing_passed else '❌ FAIL'}")
    print(f"Integration:     {'✅ PASS' if integration_passed else '❌ FAIL'}")

    if all_passed:
        print("\n✨ ALL CHECKS PASSED! Ready for deployment/commit. ✨")
        sys.exit(0)
    else:
        print("\n⚠️ SOME CHECKS FAILED. Please review logs above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
