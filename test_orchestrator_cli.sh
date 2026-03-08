#!/bin/bash
# Test script for the intent-based CLI commands
# Usage: ./test_orchestrator_cli.sh

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Testing Docsible Intent-Based CLI${NC}"
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

# --- docsible document role ---

# Test 1: Basic role with --dry-run
run_test "Basic role with --dry-run" \
    "docsible document role --role tests/fixtures/simple_role --dry-run"

# Test 2: Role with --graph
run_test "Role with --graph" \
    "docsible document role --role tests/fixtures/simple_role --graph --dry-run"

# Test 3: Role with --hybrid
run_test "Role with --hybrid" \
    "docsible document role --role tests/fixtures/simple_role --hybrid --dry-run"

# Test 4: Role with --graph --hybrid
run_test "Role with --graph --hybrid" \
    "docsible document role --role tests/fixtures/simple_role --graph --hybrid --dry-run"

# Test 5: Complex role with --complexity-report
run_test "Complex role with --complexity-report" \
    "docsible document role --role tests/fixtures/complex_role --complexity-report --dry-run"

# Test 6: Role with --simplification-report
run_test "Role with --simplification-report" \
    "docsible document role --role tests/fixtures/complex_role --simplification-report --dry-run"

# Test 7: Role with --show-dependencies
run_test "Role with --show-dependencies" \
    "docsible document role --role tests/fixtures/complex_role --show-dependencies --dry-run"

# Test 8: Role with --minimal
run_test "Role with --minimal" \
    "docsible document role --role tests/fixtures/simple_role --minimal --dry-run"

# Test 9: Role with --no-vars
run_test "Role with --no-vars" \
    "docsible document role --role tests/fixtures/simple_role --no-vars --dry-run"

# Test 10: Role with --no-tasks
run_test "Role with --no-tasks" \
    "docsible document role --role tests/fixtures/simple_role --no-tasks --dry-run"

# Test 11: Role with --no-diagrams
run_test "Role with --no-diagrams" \
    "docsible document role --role tests/fixtures/simple_role --graph --no-diagrams --dry-run"

# Test 12: Complex conditional role
run_test "Complex conditional role" \
    "docsible document role --role tests/fixtures/complex_conditional_role --graph --dry-run"

# Test 13: Role with playbook (conditional)
if [ -f "tests/fixtures/multi_role_project/site.yml" ]; then
    run_test "Role with playbook" \
        "docsible document role --role tests/fixtures/multi_role_project/roles/webserver --playbook tests/fixtures/multi_role_project/site.yml --dry-run"
fi

# Test 14: All complexity flags combined
run_test "All complexity flags" \
    "docsible document role --role tests/fixtures/complex_role --complexity-report --include-complexity --simplification-report --show-dependencies --dry-run"

# Test 15: ansible-* role (if exists)
if [ -d "role_test/ansible-complex-k8s-infra" ]; then
    run_test "ansible-complex-k8s-infra role" \
        "docsible document role --role role_test/ansible-complex-k8s-infra --graph --complexity-report --dry-run"
fi

# Test 16: Collection (if exists)
COLLECTION_DIR=$(find role_test -maxdepth 1 -type d -name "*_collection" | head -1)
if [ -n "$COLLECTION_DIR" ]; then
    run_test "Collection documentation" \
        "docsible --verbose document role --collection $COLLECTION_DIR --dry-run"
fi

# Test 17: edge_case_role basic dry-run
run_test "edge_case_role basic dry-run" \
    "docsible document role --role tests/fixtures/edge_case_role --dry-run"

# Test 18: edge_case_role with --graph (exercises block tasks in diagrams)
run_test "edge_case_role with --graph" \
    "docsible document role --role tests/fixtures/edge_case_role --graph --dry-run"

# Test 19: edge_case_role with --no-handlers (ensure handlers section can be suppressed)
run_test "edge_case_role with --no-handlers" \
    "docsible document role --role tests/fixtures/edge_case_role --no-handlers --dry-run"

# Test 20: edge_case_role with --no-vars (ensure vars + defaults suppression)
run_test "edge_case_role with --no-vars" \
    "docsible document role --role tests/fixtures/edge_case_role --no-vars --dry-run"

# --- docsible analyze role ---

# Test 17: Analyze role (no docs written; complexity_report forced on)
run_test "Analyze role" \
    "docsible analyze role --role tests/fixtures/complex_role"

# --- docsible validate role ---

# Test 18: Validate role (dry_run enforced internally)
run_test "Validate role" \
    "docsible validate role --role tests/fixtures/simple_role"

# --- Actual file generation ---

run_test "Generate actual documentation" \
    "docsible document role --role tests/fixtures/simple_role --output TEST_README.md"

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

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "\n${GREEN}All tests passed! ✓${NC}\n"
    exit 0
else
    echo -e "\n${RED}Some tests failed! ✗${NC}\n"
    exit 1
fi
