#!/bin/bash
# Test script for orchestrator with various CLI parameter combinations
# Usage: ./test_orchestrator_cli.sh

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Enable orchestrator via environment variable
export DOCSIBLE_USE_ORCHESTRATOR=true

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Testing Docsible with Orchestrator${NC}"
echo -e "${BLUE}DOCSIBLE_USE_ORCHESTRATOR=${DOCSIBLE_USE_ORCHESTRATOR}${NC}"
echo -e "${BLUE}========================================${NC}\n"

# Counter for tests
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

# Function to run a test
run_test() {
    local test_name="$1"
    shift
    local cmd="$@"

    TESTS_RUN=$((TESTS_RUN + 1))
    echo -e "\n${YELLOW}Test $TESTS_RUN: $test_name${NC}"
    echo -e "${BLUE}Command: $cmd${NC}"

    if eval "$cmd"; then
        echo -e "${GREEN}✓ PASSED${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        return 0
    else
        echo -e "${RED}✗ FAILED${NC}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi
}

# Test 1: Basic role with --dry-run
run_test "Basic role with --dry-run" \
    "docsible role --role tests/fixtures/simple_role --dry-run"

# Test 2: Role with --graph
run_test "Role with --graph" \
    "docsible role --role tests/fixtures/simple_role --graph --dry-run"

# Test 3: Role with --hybrid
run_test "Role with --hybrid" \
    "docsible role --role tests/fixtures/simple_role --hybrid --dry-run"

# Test 4: Role with --graph --hybrid
run_test "Role with --graph --hybrid" \
    "docsible role --role tests/fixtures/simple_role --graph --hybrid --dry-run"

# Test 5: Complex role with --complexity-report
run_test "Complex role with --complexity-report" \
    "docsible role --role tests/fixtures/complex_role --complexity-report --dry-run"

# Test 6: Role with --simplification-report
run_test "Role with --simplification-report" \
    "docsible role --role tests/fixtures/complex_role --simplification-report --dry-run"

# Test 7: Role with --show-dependencies
run_test "Role with --show-dependencies" \
    "docsible role --role tests/fixtures/complex_role --show-dependencies --dry-run"

# Test 8: Role with --analyze-only
run_test "Role with --analyze-only" \
    "docsible role --role tests/fixtures/complex_role --analyze-only"

# Test 9: Role with --minimal
run_test "Role with --minimal" \
    "docsible role --role tests/fixtures/simple_role --minimal --dry-run"

# Test 10: Role with --no-vars
run_test "Role with --no-vars" \
    "docsible role --role tests/fixtures/simple_role --no-vars --dry-run"

# Test 11: Role with --no-tasks
run_test "Role with --no-tasks" \
    "docsible role --role tests/fixtures/simple_role --no-tasks --dry-run"

# Test 12: Role with --no-diagrams
run_test "Role with --no-diagrams" \
    "docsible role --role tests/fixtures/simple_role --graph --no-diagrams --dry-run"

# Test 13: Complex conditional role
run_test "Complex conditional role" \
    "docsible role --role tests/fixtures/complex_conditional_role --graph --dry-run"

# Test 14: Role with playbook
if [ -f "tests/fixtures/multi_role_project/site.yml" ]; then
    run_test "Role with playbook" \
        "docsible role --role tests/fixtures/multi_role_project/roles/webserver --playbook tests/fixtures/multi_role_project/site.yml --dry-run"
fi

# Test 15: All complexity flags combined
run_test "All complexity flags" \
    "docsible role --role tests/fixtures/complex_role --complexity-report --include-complexity --simplification-report --show-dependencies --dry-run"

# Test 16: ansible-* role (if exists)
if [ -d "role_test/ansible-complex-k8s-infra" ]; then
    run_test "ansible-complex-k8s-infra role" \
        "docsible role --role role_test/ansible-complex-k8s-infra --graph --complexity-report --dry-run"
fi

# Test 17: Collection (if exists) - check for any _collection directories
COLLECTION_DIR=$(find role_test -maxdepth 1 -type d -name "*_collection" | head -1)
if [ -n "$COLLECTION_DIR" ]; then
    run_test "Collection documentation" \
        "docsible --verbose role --collection $COLLECTION_DIR --dry-run"
fi

# Test 18: Actually generate documentation (no dry-run) for simple role
run_test "Generate actual documentation" \
    "docsible role --role tests/fixtures/simple_role --output TEST_README.md"

# Clean up generated file
if [ -f "tests/fixtures/simple_role/TEST_README.md" ]; then
    echo -e "\n${BLUE}Cleaning up generated file...${NC}"
    rm tests/fixtures/simple_role/TEST_README.md
    echo -e "${GREEN}✓ Cleaned up TEST_README.md${NC}"
fi

# Print summary
echo -e "\n${BLUE}========================================${NC}"
echo -e "${BLUE}Test Summary${NC}"
echo -e "${BLUE}========================================${NC}"
echo -e "Total tests run: ${TESTS_RUN}"
echo -e "${GREEN}Tests passed: ${TESTS_PASSED}${NC}"
if [ $TESTS_FAILED -gt 0 ]; then
    echo -e "${RED}Tests failed: ${TESTS_FAILED}${NC}"
else
    echo -e "${GREEN}Tests failed: ${TESTS_FAILED}${NC}"
fi
echo -e "${BLUE}========================================${NC}"

# Exit with appropriate code
if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "\n${GREEN}All tests passed! ✓${NC}\n"
    exit 0
else
    echo -e "\n${RED}Some tests failed! ✗${NC}\n"
    exit 1
fi
