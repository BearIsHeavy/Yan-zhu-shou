#!/usr/bin/env python3
"""
Main test runner for YanZhuShou API.

Runs all test modules and provides a summary report.

Usage:
    python test_api/main.py

Requirements:
    - FastAPI server running on http://127.0.0.1:8000
    - Test user: test@example.com / 123456

Test Modules:
    - test_user.py - User APIs
    - test_blog.py - Blog APIs
    - test_feedback.py - Feedback APIs
    - test_question.py - Question Bank APIs
    - test_mistake.py - Mistake Notebook APIs
    - test_rag.py - RAG (Knowledge, Books, Reports) APIs
"""

import asyncio
import sys
from datetime import datetime
from typing import List, Tuple

# Import test modules
from test_api.test_base import BaseTest
from test_api.test_user import main as test_user
from test_api.test_blog import main as test_blog
from test_api.test_feedback import main as test_feedback
from test_api.test_question import main as test_question
from test_api.test_mistake import main as test_mistake
from test_api.test_rag import main as test_rag


# Test module configuration
TEST_MODULES = [
    ("User APIs", test_user),
    ("Blog APIs", test_blog),
    ("Feedback APIs", test_feedback),
    ("Question Bank APIs", test_question),
    ("Mistake Notebook APIs", test_mistake),
    ("RAG APIs", test_rag),
]


def print_header():
    """Print test run header."""
    print("\n" + "=" * 70)
    print(" " * 20 + "YanZhuShou API Test Suite")
    print("=" * 70)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Base URL: http://127.0.0.1:8000")
    print(f"Test User: test@example.com")
    print("=" * 70 + "\n")


def print_module_header(name: str):
    """Print module test header."""
    print(f"\n{'─' * 70}")
    print(f"  Testing: {name}")
    print(f"{'─' * 70}\n")


def print_module_result(name: str, success: bool, duration: float):
    """Print module test result."""
    status = "✓ PASSED" if success else "✗ FAILED"
    print(f"\n  {status} - {name} ({duration:.2f}s)")


def print_summary(results: List[Tuple[str, bool, float]]):
    """Print test summary."""
    print("\n" + "=" * 70)
    print(" " * 25 + "TEST SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for _, success, _ in results if success)
    failed = len(results) - passed
    total_time = sum(duration for _, _, duration in results)
    
    print(f"\n  Total Modules: {len(results)}")
    print(f"  Passed: {passed}")
    print(f"  Failed: {failed}")
    print(f"  Total Time: {total_time:.2f}s")
    print(f"\n  Success Rate: {(passed/len(results)*100):.1f}%")
    
    print("\n  Module Results:")
    print("  " + "-" * 66)
    
    for name, success, duration in results:
        status = "✓" if success else "✗"
        print(f"    {status} {name:<35} {duration:>6.2f}s")
    
    print("  " + "-" * 66)
    print("=" * 70 + "\n")
    
    return failed == 0


async def run_all_tests(selected_modules: List[str] = None) -> bool:
    """
    Run all test modules.
    
    Args:
        selected_modules: Optional list of module names to run
        
    Returns:
        True if all tests passed, False otherwise
    """
    print_header()
    
    results = []
    
    for module_name, test_func in TEST_MODULES:
        # Skip if specific modules selected and this one not included
        if selected_modules and module_name not in selected_modules:
            continue
        
        print_module_header(module_name)
        
        start_time = asyncio.get_event_loop().time()
        
        try:
            success = await test_func()
        except Exception as e:
            print(f"\n  ✗ EXCEPTION in {module_name}: {e}")
            success = False
        
        duration = asyncio.get_event_loop().time() - start_time
        results.append((module_name, success, duration))
        
        print_module_result(module_name, success, duration)
    
    # Print summary
    all_passed = print_summary(results)
    
    return all_passed


def main():
    """Main entry point."""
    # Parse command line arguments
    selected_modules = None
    if len(sys.argv) > 1:
        selected_modules = sys.argv[1:]
        print(f"\nRunning selected modules: {', '.join(selected_modules)}\n")
    
    # Run tests
    try:
        success = asyncio.run(run_all_tests(selected_modules))
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTest run interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nTest run failed with error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
