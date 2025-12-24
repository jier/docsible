#!/bin/bash
# Comparison test script for doc_the_role vs doc_the_role_orchestrated
# This script runs both implementations and compares their outputs to ensure equivalence
# Usage: ./test_implementation_comparison.sh

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Test counters
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

# Temporary directory for outputs
TEMP_DIR=$(mktemp -d)
trap "rm -rf $TEMP_DIR" EXIT

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Implementation Comparison Tests${NC}"
echo -e "${BLUE}Comparing: doc_the_role vs doc_the_role_orchestrated${NC}"
echo -e "${BLUE}Temp directory: ${TEMP_DIR}${NC}"
echo -e "${BLUE}========================================${NC}\n"

# Function to run comparison test
compare_outputs() {
    local test_name="$1"
    shift
    local cmd_args="$@"

    TESTS_RUN=$((TESTS_RUN + 1))
    echo -e "\n${CYAN}========================================${NC}"
    echo -e "${YELLOW}Test $TESTS_RUN: $test_name${NC}"
    echo -e "${CYAN}========================================${NC}"
    echo -e "${BLUE}Command: docsible role $cmd_args${NC}"

    # Files for storing outputs
    local original_output="$TEMP_DIR/original_${TESTS_RUN}.txt"
    local orchestrated_output="$TEMP_DIR/orchestrated_${TESTS_RUN}.txt"
    local diff_output="$TEMP_DIR/diff_${TESTS_RUN}.txt"

    # Run original implementation
    echo -e "\n${BLUE}Running original implementation...${NC}"
    if DOCSIBLE_USE_ORCHESTRATOR=false docsible role $cmd_args > "$original_output" 2>&1; then
        echo -e "${GREEN}✓ Original completed${NC}"
    else
        local exit_code=$?
        echo -e "${YELLOW}⚠ Original exited with code: $exit_code${NC}"
        echo "$exit_code" > "$original_output.exitcode"
    fi

    # Run orchestrated implementation
    echo -e "${BLUE}Running orchestrated implementation...${NC}"
    if DOCSIBLE_USE_ORCHESTRATOR=true docsible role $cmd_args > "$orchestrated_output" 2>&1; then
        echo -e "${GREEN}✓ Orchestrated completed${NC}"
    else
        local exit_code=$?
        echo -e "${YELLOW}⚠ Orchestrated exited with code: $exit_code${NC}"
        echo "$exit_code" > "$orchestrated_output.exitcode"
    fi

    # Compare exit codes if they exist
    if [ -f "$original_output.exitcode" ] || [ -f "$orchestrated_output.exitcode" ]; then
        local orig_exit=$(cat "$original_output.exitcode" 2>/dev/null || echo "0")
        local orch_exit=$(cat "$orchestrated_output.exitcode" 2>/dev/null || echo "0")

        if [ "$orig_exit" != "$orch_exit" ]; then
            echo -e "${RED}✗ FAILED - Exit codes differ: original=$orig_exit, orchestrated=$orch_exit${NC}"
            TESTS_FAILED=$((TESTS_FAILED + 1))
            return 1
        fi
    fi

    # Compare outputs
    echo -e "\n${BLUE}Comparing outputs...${NC}"
    if diff -u "$original_output" "$orchestrated_output" > "$diff_output" 2>&1; then
        echo -e "${GREEN}✓ PASSED - Outputs are identical${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        return 0
    else
        echo -e "${RED}✗ FAILED - Outputs differ${NC}"
        echo -e "${YELLOW}Diff (first 50 lines):${NC}"
        head -50 "$diff_output"
        echo -e "\n${YELLOW}Full diff saved to: $diff_output${NC}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi
}

# Function to compare generated files
compare_generated_files() {
    local test_name="$1"
    local role_path="$2"
    shift 2
    local cmd_args="$@"

    TESTS_RUN=$((TESTS_RUN + 1))
    echo -e "\n${CYAN}========================================${NC}"
    echo -e "${YELLOW}Test $TESTS_RUN: $test_name (File Generation)${NC}"
    echo -e "${CYAN}========================================${NC}"
    echo -e "${BLUE}Command: docsible role $cmd_args${NC}"

    # Create temporary copies of the role
    local orig_role="$TEMP_DIR/orig_role_${TESTS_RUN}"
    local orch_role="$TEMP_DIR/orch_role_${TESTS_RUN}"

    cp -r "$role_path" "$orig_role"
    cp -r "$role_path" "$orch_role"

    # Run original implementation
    echo -e "\n${BLUE}Running original implementation...${NC}"
    local orig_args="${cmd_args//$role_path/$orig_role}"
    if DOCSIBLE_USE_ORCHESTRATOR=false docsible role $orig_args > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Original completed${NC}"
    else
        echo -e "${RED}✗ Original failed${NC}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi

    # Run orchestrated implementation
    echo -e "${BLUE}Running orchestrated implementation...${NC}"
    local orch_args="${cmd_args//$role_path/$orch_role}"
    if DOCSIBLE_USE_ORCHESTRATOR=true docsible role $orch_args > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Orchestrated completed${NC}"
    else
        echo -e "${RED}✗ Orchestrated failed${NC}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi

    # Compare generated README files
    echo -e "\n${BLUE}Comparing generated README files...${NC}"
    local orig_readme="$orig_role/README.md"
    local orch_readme="$orch_role/README.md"

    if [ ! -f "$orig_readme" ]; then
        echo -e "${RED}✗ FAILED - Original README not generated${NC}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi

    if [ ! -f "$orch_readme" ]; then
        echo -e "${RED}✗ FAILED - Orchestrated README not generated${NC}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi

    local diff_output="$TEMP_DIR/readme_diff_${TESTS_RUN}.txt"
    if diff -u "$orig_readme" "$orch_readme" > "$diff_output" 2>&1; then
        echo -e "${GREEN}✓ PASSED - Generated READMEs are identical${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        return 0
    else
        echo -e "${RED}✗ FAILED - Generated READMEs differ${NC}"
        echo -e "${YELLOW}Diff (first 50 lines):${NC}"
        head -50 "$diff_output"
        echo -e "\n${YELLOW}Full diff saved to: $diff_output${NC}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi
}

# Test 1: Basic dry-run
compare_outputs "Basic dry-run" \
    "--role tests/fixtures/simple_role --dry-run"

# Test 2: Dry-run with graph
compare_outputs "Dry-run with graph" \
    "--role tests/fixtures/simple_role --graph --dry-run"

# Test 3: Dry-run with hybrid
compare_outputs "Dry-run with hybrid mode" \
    "--role tests/fixtures/simple_role --hybrid --dry-run"

# Test 4: Dry-run with graph and hybrid
compare_outputs "Dry-run with graph and hybrid" \
    "--role tests/fixtures/simple_role --graph --hybrid --dry-run"

# Test 5: Complexity report
compare_outputs "Complexity report" \
    "--role tests/fixtures/complex_role --complexity-report --dry-run"

# Test 6: Simplification report
compare_outputs "Simplification report" \
    "--role tests/fixtures/complex_role --simplification-report --dry-run"

# Test 7: Show dependencies
compare_outputs "Show dependencies" \
    "--role tests/fixtures/complex_role --show-dependencies --dry-run"

# Test 8: Analyze-only mode
compare_outputs "Analyze-only mode" \
    "--role tests/fixtures/complex_role --analyze-only"

# Test 9: Minimal mode
compare_outputs "Minimal mode" \
    "--role tests/fixtures/simple_role --minimal --dry-run"

# Test 10: No vars flag
compare_outputs "No vars flag" \
    "--role tests/fixtures/simple_role --no-vars --dry-run"

# Test 11: No tasks flag
compare_outputs "No tasks flag" \
    "--role tests/fixtures/simple_role --no-tasks --dry-run"

# Test 12: No diagrams flag
compare_outputs "No diagrams flag" \
    "--role tests/fixtures/simple_role --graph --no-diagrams --dry-run"

# Test 13: All complexity flags
compare_outputs "All complexity flags" \
    "--role tests/fixtures/complex_role --complexity-report --include-complexity --simplification-report --show-dependencies --dry-run"

# Test 14: File generation - Simple role
if [ -d "tests/fixtures/simple_role" ]; then
    compare_generated_files "File generation - simple role" \
        "tests/fixtures/simple_role" \
        "--role tests/fixtures/simple_role --no-backup"
fi

# Test 15: File generation - Complex role with graph
if [ -d "tests/fixtures/complex_role" ]; then
    compare_generated_files "File generation - complex role with graph" \
        "tests/fixtures/complex_role" \
        "--role tests/fixtures/complex_role --graph --no-backup"
fi

# Test 16: File generation - Hybrid mode
if [ -d "tests/fixtures/simple_role" ]; then
    compare_generated_files "File generation - hybrid mode" \
        "tests/fixtures/simple_role" \
        "--role tests/fixtures/simple_role --hybrid --no-backup"
fi

# Test 17: Complex conditional role
if [ -d "tests/fixtures/complex_conditional_role" ]; then
    compare_outputs "Complex conditional role" \
        "--role tests/fixtures/complex_conditional_role --graph --dry-run"
fi

# Test 18: Role with playbook
if [ -f "tests/fixtures/multi_role_project/site.yml" ]; then
    compare_outputs "Role with playbook" \
        "--role tests/fixtures/multi_role_project/roles/webserver --playbook tests/fixtures/multi_role_project/site.yml --dry-run"
fi

# Print summary
echo -e "\n${BLUE}========================================${NC}"
echo -e "${BLUE}Comparison Test Summary${NC}"
echo -e "${BLUE}========================================${NC}"
echo -e "Total tests run: ${TESTS_RUN}"
echo -e "${GREEN}Tests passed: ${TESTS_PASSED}${NC}"
if [ $TESTS_FAILED -gt 0 ]; then
    echo -e "${RED}Tests failed: ${TESTS_FAILED}${NC}"
    echo -e "\n${YELLOW}Note: Diff files are preserved in: ${TEMP_DIR}${NC}"
    echo -e "${YELLOW}Review the diffs to understand the differences.${NC}"
else
    echo -e "${GREEN}Tests failed: ${TESTS_FAILED}${NC}"
fi

if [ $TESTS_PASSED -gt 0 ] && [ $TESTS_FAILED -eq 0 ]; then
    echo -e "\n${GREEN}Success Rate: 100%${NC}"
elif [ $TESTS_RUN -gt 0 ]; then
    local success_rate=$((TESTS_PASSED * 100 / TESTS_RUN))
    echo -e "\n${YELLOW}Success Rate: ${success_rate}%${NC}"
fi

echo -e "${BLUE}========================================${NC}"

# Exit with appropriate code
if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "\n${GREEN}✓ All comparison tests passed!${NC}"
    echo -e "${GREEN}Both implementations produce identical outputs.${NC}\n"
    exit 0
else
    echo -e "\n${RED}✗ Some comparison tests failed!${NC}"
    echo -e "${RED}Implementations produce different outputs.${NC}\n"
    exit 1
fi
