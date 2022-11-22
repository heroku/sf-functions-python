#!/usr/bin/env bash

set -euo pipefail

# Using Python here since the GNU and BSD versions of the 'base64' command have differing
# output wrapping behaviour/arguments, which makes writing something portable a pain.
function base64_encode() {
  python3 -c "import base64, sys; print(base64.b64encode(sys.stdin.buffer.read()).decode('ascii'))"
}

invocation_id="00Dxx0000006IYJEA2-4Y4W3Lw_LkoskcHdEaZze--MyFunction-$(openssl rand -hex 12)"

sfcontext=$(base64_encode <<'EOF'
{
  "apiVersion": "53.0",
  "payloadVersion": "0.1",
  "userContext": {
    "orgId": "00Dxx0000006IYJ",
    "userId": "005xx000001X8Uz",
    "username": "user@example.tld",
    "salesforceBaseUrl": "https://example-base-url.my.salesforce-sites.com",
    "orgDomainUrl": "https://example-domain-url.my.salesforce.com"
  }
}
EOF
)

sffncontext=$(base64_encode <<EOF
{
  "accessToken": "EXAMPLE-TOKEN",
  "requestId": "${invocation_id}"
}
EOF
)

curl "${1:?Provide function runtime url as the first argument to this script!}" \
  -i \
  --connect-timeout 3 \
  -d "${2:?Provide the payload as the second argument to this script!}" \
  -H "Content-Type: application/json" \
  -H "ce-id: ${invocation_id}" \
  -H "ce-source: urn:event:from:salesforce/xx/228.0/00Dxx0000006IYJ/apex/MyFunctionApex:test():7" \
  -H "ce-specversion: 1.0" \
  -H "ce-type: com.salesforce.function.invoke.sync" \
  -H "ce-sfcontext: ${sfcontext}" \
  -H "ce-sffncontext: ${sffncontext}" \
  # -H "x-health-check: true" \
