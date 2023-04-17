# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

- The supported version of the dependency `uvicorn` has been raised from `>=0.20.0,<0.21` to `>=0.21.1,<0.22`.
- The supported version of the dependency `starlette` has been raised from `>=0.23.1,<0.24` to `>=0.26.1,<0.27`.
- The supported version of the dependency `structlog` has been raised from `>=22.3.0,<23` to `>=23.1.0,<24`.

## [0.5.1] - 2023-02-06

### Fixed

- Requests made by `DataAPI` now use the correct `Content-Type`.
- Requests made by `DataAPI` now correctly send an empty body for requests where no body is expected (such as `query` or `delete`).
- The `testing.mock_event` function now generates a unique event time each time it is called.

## [0.5.0] - 2023-02-02

### Changed

- `DataAPI` now raises the new `data_api.exceptions.ClientError` exception when an exception in
  the underlying HTTP library occurs, rather than exposing that library's exceptions directly.
- `MissingIdFieldError` has been renamed to `MissingFieldError` and the name of the missing
  field is now exposed in the exception value.
- Added missing class attribute docstrings to `SalesforceRestApiError`, `InnerSalesforceRestApiError` and `ReferenceId`.
- Updated the docstrings for the public APIs to align with the style guidelines.
- Updated the user-facing error and CLI messages to align with the style guidelines.

### Fixed

- All `DataAPI` exceptions now have suitable string representations, making it easier to diagnose
  errors seen in function logs.
- The `testing.mock_event` function now generates a unique event ID each time it is called.

## [0.4.0] - 2023-01-25

### Added

- Added a `testing` module, containing `mock_event` and `mock_context` functions for simplifying unit testing of Python functions.
- Added example code snippets and attribute values to the docstrings for public APIs.

## [0.3.0] - 2023-01-17

### Added

- Invocation metadata is now set on the function response via the `x-extra-info` header.

### Changed

- All publicly exported `dataclass`es (such as `Context`, `InvocationEvent` and `Record`) now only accept their fields being passed as keyword arguments, rather than as positional arguments.
- If an unhandled internal runtime error occurs, the log output now includes the full stack trace,
  and the function response's HTTP status code is now `503` rather than `500`.
- The docstrings for several public types and APIs have been improved.
- The minimum version of the dependencies `orjson`, `starlette` and `structlog` have been raised.

## [0.2.0] - 2022-12-22

### Changed

- Function projects must now include a valid `project.toml` file to pass validation.
  Functions generated using `sf generate function` already include this file.
- The `context.org.data_api` client now uses the Salesforce REST API version specified by the
  `com.salesforce.salesforce-api-version` key in `project.toml`, rather than using the Salesforce
  Org's maximum supported REST API version. This version must be `'53.0'` or newer.
- The error messages shown for invalid functions have been improved.

## [0.1.0] - 2022-12-14

### Added

- Initial beta implementation.
