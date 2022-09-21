#!/usr/bin/env bash

set -euo pipefail

# Using Python here since the GNU and BSD versions of the 'base64' command have differing
# output wrapping behaviour/arguments, which makes writing something portable a pain.
function base64_encode() {
  python3 -c "import base64, sys; print(base64.b64encode(sys.stdin.buffer.read()).decode('ascii'))"
}

sfcontext=$(base64_encode <<'EOF'
{
  "apiVersion": "55.0",
  "payloadVersion": "0.1",
  "userContext": {
    "orgId": "00Dxx0000006IYJ",
    "userId": "005xx000001X8Uz",
    "onBehalfOfUserId": null,
    "username": "test-zqisnf6ytlqv@example.com",
    "salesforceBaseUrl": "https://d8d000005zejveai-dev-ed.my.salesforce.com",
    "orgDomainUrl": "https://d8d000005zejveai-dev-ed.my.salesforce.com"
  }
}
EOF
)

sffncontext=$(base64_encode <<'EOF'
{
  "accessToken": "00D8d000005zeJv!ARQAQCLjHe.WiHQ1VxcZS2qUi.Hgez8PHzjhq0icJY8wzYeCDAUJIOBQ1DjFu05wuD.tgJoUV2hIq2aLpf9oYUyk_AoEI0cb",
  "functionInvocationId": null,
  "functionName": "MyFunction",
  "apexClassId": null,
  "apexClassFQN": null,
  "requestId": "00Dxx0000006IYJEA2-4Y4W3Lw_LkoskcHdEaZze--MyFunction-2020-09-03T20:56:27.608444Z",
  "resource": "http://dhagberg-wsl1:8080"
}
EOF
)

curl "${1:?Provide function runtime url as the first argument to this script!}" \
  -i \
  -d "${2:?Provide the payload as the second argument to this script!}" \
  -H "Content-Type: application/json" \
  -H "ce-specversion: 1.0" \
  -H "ce-id: 00Dxx0000006IYJEA2-4Y4W3Lw_LkoskcHdEaZze--MyFunction-$(openssl rand -hex 12)" \
  -H "ce-source: urn:event:from:salesforce/xx/228.0/00Dxx0000006IYJ/apex/MyFunctionApex:test():7" \
  -H "ce-type: com.salesforce.function.invoke.sync" \
  -H "ce-time: 2020-09-03T20:56:28.297915Z" \
  -H "ce-sfcontext: ${sfcontext}" \
  -H "ce-sffncontext: ${sffncontext}" \
  -H "Authorization: C2C eyJ2ZXIiOiIxLjAiLCJraWQiOiJDT1JFLjAwRHh4MDAwMDAwNklZSi4xNTk5MTU5NjQwMzUwIiwidHlwIjoiand0IiwiY2x2IjoiSjIuMS4xIiwiYWxnIjoiRVMyNTYifQ.eyJhdWQiOiJwbGF0Zm9ybS1mdW5jdGlvbnMiLCJhdXQiOiJTRVJWSUNFIiwibmJmIjoxNTk5MTY2NTU4LCJjdHgiOiJzZmRjLnBsYXRmb3JtLWZ1bmN0aW9ucyIsImlzcyI6ImNvcmUvZGhhZ2Jlcmctd3NsMS8wMER4eDAwMDAwMDZJWUpFQTIiLCJzdHkiOiJUZW5hbnQiLCJpc3QiOjEsImV4cCI6MTU5OTE2NjY3OCwiaWF0IjoxNTk5MTY2NTg4LCJqdGkiOiJDMkMtMTA3NTg2OTg1NTMxNTMyOTkzMjE3OTEyMzQwNTIzMjgzOTEifQ.jZZ4ksYlq0vKtBf0yEfpJVL2yYh3QHOwp0KCk-QxzDyF_7VARB-N74Cqpj2JWhVP4TcBLGXYuldB-Sk6P5HlGQ" \
  # -H "x-health-check: true" \
