#!/usr/bin/env bash

set -euo pipefail

# Using Python here since the GNU and BSD versions of the 'base64' command have differing
# output wrapping behaviour/arguments, which makes writing something portable a pain.
function base64_encode() {
  python3 -c "import base64, sys; print(base64.b64encode(sys.stdin.buffer.read()).decode('ascii'))"
}

invocation_id="00DJS0000000123ABC-$(openssl rand -hex 16)"

sfcontext=$(base64_encode <<'EOF'
{
  "apiVersion": "56.0",
  "payloadVersion": "0.1",
  "userContext": {
    "onBehalfOfUserId": null,
    "orgDomainUrl": "https://example-domain-url.my.salesforce.com",
    "orgId": "00DJS0000000123ABC",
    "salesforceBaseUrl": "https://example-base-url.my.salesforce-sites.com",
    "salesforceInstance": "swe1",
    "userId": "005JS000000H123",
    "username": "user@example.tld"
  }
}
EOF
)

sffncontext=$(base64_encode <<EOF
{
  "accessToken": "EXAMPLE-TOKEN",
  "apexFQN": "ExampleClass:example_function():7",
  "deadline": "2023-01-19T10:11:12.468085Z",
  "functionName": "ExampleProject.examplefunction",
  "invokingNamespace": "",
  "requestId": "${invocation_id}",
  "resource": "https://examplefunction-cod-mni.crag-123abc.evergreen.space"
}
EOF
)

curl "${1:?Provide function runtime url as the first argument to this script!}" \
  -i \
  --connect-timeout 3 \
  -d "${2:?Provide the payload as the second argument to this script!}" \
  -H "content-type: application/json" \
  -H "ce-id: ${invocation_id}" \
  -H "ce-source: urn:event:from:salesforce/JS/56.0/00DJS0000000123ABC/apex/ExampleClass:example_function():7" \
  -H "ce-specversion: 1.0" \
  -H "ce-time: 2023-01-19T10:09:12.476684Z" \
  -H "ce-type: com.salesforce.function.invoke.sync" \
  -H "ce-sfcontext: ${sfcontext}" \
  -H "ce-sffncontext: ${sffncontext}" \
  -H "x-request-id: ${invocation_id}" \
  # -H "x-health-check: true" \
