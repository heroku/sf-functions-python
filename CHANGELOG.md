# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

- Function projects must now include a valid `project.toml` file to pass validation.
  Functions generated using `sf generate function` already include this file.
- The `context.org.data_api` client now uses the Salesforce REST API version specified by the
  `com.salesforce.salesforce-api-version` key in `project.toml`, rather than using the Salesforce
  Org's maximum supported REST API version. This version must be `'53.0'` or newer.
- The error messages shown for invalid functions have been improved.

## [0.1.0] - 2022-12-14

### Added

- Initial beta implementation
