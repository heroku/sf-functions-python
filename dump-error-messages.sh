#!/usr/bin/env bash

set -euo pipefail

export PYTHONUNBUFFERED=1
server_log="${TMPDIR}/runtime_server_log.txt"

echo "# Python Functions user-facing messages"

echo -e "\n## CLI help text"

echo -e "\nNote: End users mostly won't use the sf-functions-python CLI directly, since they will"
echo "instead use the sf CLI which wraps it - however, I'm including these for completeness."

cli_args=(
  "--help"
  "check --help"
  "serve --help"
)

for arg in "${cli_args[@]}"; do
  command="sf-functions-python ${arg}"
  echo -e "\n### ${command}\n"
  echo '```term'
  ${command} 2>&1
  echo '```'
done

echo -e "\n## Checking/running a valid function"

echo -e "\nIn the context of the buildpack self-check:\n"
echo '```term'
sf-functions-python check "tests/fixtures/basic"
echo '```'

echo -e "\nIn the context of the CLI start command:\n"
sf-functions-python serve "tests/fixtures/basic" &> "${server_log}" &
sleep 1
echo '```term'
cat "${server_log}"
echo '```'
kill $!
rm "${server_log}"

echo -e "\n## Checking/running functions that fail the self-check"

echo -e "\nNote: The same base error message is used for both the self-check and the start command, however,"
echo -e "the prefix is different ('Function failed validation:' vs 'Unable to load function: ' etc)."

functions_that_fail_self_check=(
  "tests/fixtures/invalid_missing_function"
  "tests/fixtures/invalid_missing_main_py"
  "tests/fixtures/invalid_not_a_function"
  "tests/fixtures/invalid_not_async"
  "tests/fixtures/invalid_number_of_args"
  "tests/fixtures/invalid_syntax_error"
  "tests/fixtures/project_toml_api_version_invalid"
  "tests/fixtures/project_toml_api_version_missing"
  "tests/fixtures/project_toml_api_version_too_old"
  "tests/fixtures/project_toml_api_version_triple_digits"
  "tests/fixtures/project_toml_api_version_wrong_type"
  "tests/fixtures/project_toml_file_missing"
  "tests/fixtures/project_toml_invalid_toml"
  "tests/fixtures/project_toml_invalid_unicode"
  "tests/fixtures/project_toml_salesforce_table_missing"
  "tests/fixtures/project_toml_salesforce_table_wrong_type"
)

for fixture in "${functions_that_fail_self_check[@]}"; do
  echo -e "\n### ${fixture}\n"
  echo -e "In the context of the production deploy self-check:\n"
  echo '```term'
  sf-functions-python check "${fixture}" 2>&1 || true
  echo '```'
  echo -e "\nIn the context of the CLI start command:\n"
  echo '```term'
  sf-functions-python serve "${fixture}" 2>&1 || true
  echo '```'
done

echo -e "\n## Functions that fail at runtime"
echo -e "\nThese are cases we cannot catch using the self-check, as they only occur when the function is running."

function invoke_function() {
  local fixture="${1}"
  local payload="${2}"
  local description="${3:-$fixture}"
  echo -e "\n### ${description}"
  sf-functions-python serve "${fixture}" &> "${server_log}" &
  sleep 1
  ./invoke.sh http://localhost:8080 "${payload}" > /dev/null || true
  echo -e "\nServer log:\n"
  echo '```term'
  cat "${server_log}"
  echo '```'
  kill $!
  rm "${server_log}"
}

invoke_function "tests/fixtures/raises_exception_at_runtime" "{}"
invoke_function "tests/fixtures/return_value_not_serializable" "{}"
invoke_function "tests/fixtures/basic" "this is invalid JSON" "Invalid CloudEvent payload (should not be possible to trigger this in practice)"
