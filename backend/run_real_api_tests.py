#!/usr/bin/env uv run python
"""
Real LLM API Test Runner

Safe runner for real LLM API integration tests with budget controls and safety checks.

Usage:
    python run_real_api_tests.py --help
    python run_real_api_tests.py --check-config
    python run_real_api_tests.py --run-basic
    python run_real_api_tests.py --run-all --max-cost=0.25
    python run_real_api_tests.py --run-single test_real_job_description_parsing

Environment Variables Required:
    OPENAI_API_KEY - OpenAI API key for testing
    ANTHROPIC_API_KEY - (Optional) Anthropic API key

Safety Features:
    - Strict token and cost budgets
    - Environment validation
    - Pre-test configuration checks
    - Real-time cost monitoring
    - Automatic test termination if budget exceeded
"""

import os
import sys
import argparse
import logging
from decimal import Decimal
from typing import List, Dict, Any
from pathlib import Path

# Load .env file if it exists
def load_env_file():
    """Load environment variables from .env file"""
    env_path = Path(__file__).parent / '.env'
    if env_path.exists():
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    # Only set if not already in environment
                    if key not in os.environ:
                        os.environ[key] = value

# Load environment variables before Django setup
load_env_file()

# Add Django setup
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cv_tailor.settings')
django.setup()

from django.test import override_settings
from django.test.utils import get_runner
from django.conf import settings
from llm_services.tests.test_real_api_config import RealAPITestConfig, TestDataFactory

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class RealAPITestRunner:
    """Safe runner for real LLM API tests"""

    def __init__(self, max_cost_usd: float = 0.50):
        self.config = RealAPITestConfig()
        self.config.budget.max_cost_total_usd = max_cost_usd
        self.test_modules = [
            'llm_services.tests.test_real_llm_integration',
            'llm_services.tests.test_real_circuit_breaker',
            'llm_services.tests.test_real_pipeline_integration',
        ]

    def check_configuration(self) -> bool:
        """Check if configuration is safe for real API testing"""
        print("🔍 Checking Real API Test Configuration...")
        print("-" * 50)

        # Check API keys
        openai_key = os.environ.get('OPENAI_API_KEY', '')
        anthropic_key = os.environ.get('ANTHROPIC_API_KEY', '')

        print(f"OpenAI API Key: {'✅ Available' if openai_key else '❌ Missing'}")
        print(f"Anthropic API Key: {'✅ Available' if anthropic_key else '❌ Missing (Optional)'}")

        if not openai_key:
            print("❌ ERROR: OPENAI_API_KEY is required for real API tests")
            return False

        # Check environment safety
        is_safe = self.config.is_safe_environment()
        print(f"Safe Environment: {'✅ Yes' if is_safe else '❌ No'}")

        if not is_safe:
            print("⚠️  WARNING: Not in a detected test environment")
            print("   To force tests, set: FORCE_REAL_API_TESTS=true")

        # Check budget
        budget = self.config.budget
        print(f"Budget Configuration:")
        print(f"  Max cost per test: ${budget.max_cost_per_test_usd:.4f}")
        print(f"  Max total cost: ${budget.max_cost_total_usd:.2f}")
        print(f"  Max tokens per test: {budget.max_tokens_per_test}")
        print(f"  Max total tokens: {budget.max_tokens_total}")

        # Validate test data
        print(f"\nTest Data Validation:")
        validation = TestDataFactory.validate_minimal_data()
        for key, tokens in validation.items():
            status = "✅" if tokens <= 50 else "⚠️"
            print(f"  {key}: {tokens} tokens {status}")

        print("-" * 50)
        should_run = (openai_key and (is_safe or os.environ.get('FORCE_REAL_API_TESTS')))
        print(f"Ready to run tests: {'✅ Yes' if should_run else '❌ No'}")

        return should_run

    def run_basic_tests(self) -> bool:
        """Run basic integration tests only"""
        print("🧪 Running Basic Real API Tests...")
        return self._run_test_module('llm_services.tests.test_real_llm_integration')

    def run_all_tests(self) -> bool:
        """Run all real API tests"""
        print("🧪 Running All Real API Tests...")

        success = True
        for module in self.test_modules:
            if not self._run_test_module(module):
                success = False
                break  # Stop on first failure to prevent budget overrun

        return success

    def run_specific_test(self, test_name: str) -> bool:
        """Run a specific test method"""
        print(f"🧪 Running Specific Test: {test_name}")

        # Find the test in modules
        for module in self.test_modules:
            test_path = f"{module}.{test_name}"
            try:
                return self._run_test_module(test_path)
            except Exception:
                continue

        print(f"❌ Test not found: {test_name}")
        return False

    def _run_test_module(self, module_path: str) -> bool:
        """Run a specific test module"""
        try:
            print(f"Running {module_path}...")

            # Apply safe settings
            safe_settings = self.config.get_safe_django_settings()
            with override_settings(**safe_settings):
                TestRunner = get_runner(settings)
                test_runner = TestRunner(verbosity=2, interactive=False)

                failures = test_runner.run_tests([module_path])

                if failures:
                    print(f"❌ {module_path} had {failures} failures")
                    return False
                else:
                    print(f"✅ {module_path} passed")
                    return True

        except Exception as e:
            print(f"❌ Error running {module_path}: {e}")
            return False

    def get_budget_status(self) -> Dict[str, Any]:
        """Get current budget status"""
        return self.config.budget.get_remaining_budget()

    def estimate_costs(self) -> Dict[str, float]:
        """Estimate costs for different test suites"""
        return {
            'basic_tests': 0.10,      # Basic integration tests
            'circuit_breaker': 0.05,  # Circuit breaker tests
            'pipeline_tests': 0.20,   # Full pipeline tests
            'all_tests': 0.35,        # All tests combined
        }


def main():
    parser = argparse.ArgumentParser(description='Real LLM API Test Runner')
    parser.add_argument('--check-config', action='store_true',
                       help='Check test configuration and exit')
    parser.add_argument('--run-basic', action='store_true',
                       help='Run basic integration tests only')
    parser.add_argument('--run-all', action='store_true',
                       help='Run all real API tests')
    parser.add_argument('--run-single', type=str,
                       help='Run a specific test method')
    parser.add_argument('--max-cost', type=float, default=0.50,
                       help='Maximum total cost in USD (default: $0.50)')
    parser.add_argument('--estimate-costs', action='store_true',
                       help='Show cost estimates and exit')
    parser.add_argument('--force', action='store_true',
                       help='Force tests even in non-test environment')

    args = parser.parse_args()

    if args.force:
        os.environ['FORCE_REAL_API_TESTS'] = 'true'

    # Create test runner
    runner = RealAPITestRunner(max_cost_usd=args.max_cost)

    # Check configuration first
    if args.check_config:
        runner.check_configuration()
        return

    if args.estimate_costs:
        estimates = runner.estimate_costs()
        print("💰 Cost Estimates:")
        print("-" * 30)
        for test_suite, cost in estimates.items():
            print(f"{test_suite}: ${cost:.2f}")
        print("-" * 30)
        print(f"Your budget: ${args.max_cost:.2f}")
        return

    # Validate configuration before running tests
    if not runner.check_configuration():
        print("\n❌ Configuration check failed. Please fix issues above.")
        sys.exit(1)

    # Confirm with user before running real API tests
    if not args.force and not args.run_single:
        response = input(f"\n⚠️  This will make real API calls costing up to ${args.max_cost:.2f}. Continue? (y/N): ")
        if response.lower() != 'y':
            print("Test run cancelled.")
            return

    print("\n🚀 Starting Real API Tests...")
    print("=" * 50)

    success = False
    if args.run_basic:
        success = runner.run_basic_tests()
    elif args.run_all:
        success = runner.run_all_tests()
    elif args.run_single:
        success = runner.run_specific_test(args.run_single)
    else:
        print("No test option specified. Use --help for options.")
        return

    # Show final results
    print("\n" + "=" * 50)
    if success:
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed!")

    # Show budget usage
    budget_status = runner.get_budget_status()
    print(f"💰 Budget Status:")
    print(f"  Cost used: ${args.max_cost - budget_status['cost_remaining_usd']:.6f}")
    print(f"  Cost remaining: ${budget_status['cost_remaining_usd']:.6f}")
    print(f"  Usage: {100 - budget_status['cost_percent']:.1f}%")

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()