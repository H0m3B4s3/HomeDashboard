#!/bin/bash

set -e

# Colors for output
green='\033[0;32m'
red='\033[0;31m'
yellow='\033[1;33m'
reset='\033[0m'

function print_step() {
  echo -e "${yellow}==> $1${reset}"
}
function print_success() {
  echo -e "${green}$1${reset}"
}
function print_error() {
  echo -e "${red}$1${reset}"
}

# Activate virtual environment
print_step "Activating virtual environment..."
if [ -d "venv" ]; then
  source venv/bin/activate
  print_success "Virtual environment activated."
else
  print_error "Virtual environment not found! Run: python3 -m venv venv && source venv/bin/activate"
  exit 1
fi

# Set PYTHONPATH to project root
export PYTHONPATH=$(pwd)

# Recreate database
print_step "Recreating database..."
python3 scripts/create_db.py && print_success "Database created."

# Seed categories
print_step "Seeding categories..."
python3 scripts/seed_categories.py && print_success "Categories seeded."

# Add sample events
print_step "Adding sample events..."
python3 scripts/add_sample_events.py && print_success "Sample events added."

# Run all tests
print_step "Running all test scripts..."
TEST_FAILED=0
for test_script in tests/test_*.py; do
  echo -e "${yellow}Running $test_script...${reset}"
  if python3 "$test_script"; then
    print_success "Passed: $test_script"
  else
    print_error "FAILED: $test_script"
    TEST_FAILED=1
  fi
done
if [ $TEST_FAILED -eq 0 ]; then
  print_success "All tests passed."
else
  print_error "Some tests failed. Check output above."
fi

# Start the dev server (always runs)
print_step "Starting development server..."
./tools/dev.sh 