# Things to test...

# CLI:
# - check subcommand
# - serve subcommand (with some error so exits)
# - manpage?

# Valid CloudEvents:
# - minimal payload with none of the optional fields
# - full payload with all of the optional fields
# - Data payload of various shapes, including empty.

# Invalid CloudEvents:
# - Wrong Content-Type
# - Missing mandatory fields
# - Missing extension fields
# - Extension fields not valid base64
# - Extension fields not JSON deserializable
# - Extension fields not correct shape (TypeError, missing fields)
# - Differentiating between user and SF cause of invalid payload?

# Invalid functions (build time):
# - missing module
# - module fails to import (SyntaxError)
# - module fails to import (NameError)
# - module fails to import (ModuleNotFoundError)
# - module fails to import (ImportError)
# - missing function definition
# - function invalid type (not a function)
# - function invalid type (sync not async)
# - function invalid type (wrong number of args)

# Functions that fail at runtime:
# - raises
# - returns something that isn't JSON serializable
# - times out

# Valid functions:
# - absolute imports from function package
# - relative imports from function package
# - function with full type signature
# - function with no types
# - returning None
# - returning something that needs JSON serialization
# - returning something that's already JSON serialized? (should we support this?)
# - logging
# - contents of invocation event and context population correctly
# - data client

# Other:
# - Health check
# - ExtraInfo headers
# - HTTP status codes
