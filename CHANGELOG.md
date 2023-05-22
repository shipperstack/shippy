# Changelog

The format is based on [Keep a Changelog][keep-a-changelog].

[keep-a-changelog]: https://keepachangelog.com/en/1.0.0/


# [Unreleased]


[Unreleased]: https://github.com/shipperstack/shippy/compare/1.11.1...HEAD


# [1.11.1] - 2023-05-22

## Added
- Added an argument to show shippy's version

## Changed
- Fixed a crash that occurred when the GitHub API was down
- Updated library dependencies
  - sentry-sdk (1.21.0 -> 1.23.1)
  - requests (2.29.0 -> 2.30.0)
  - setuptools (67.7.2 -> 67.8.0)

[1.11.1]: https://github.com/shipperstack/shippy/compare/1.11.0...1.11.1


# [1.11.0] - 2023-04-30

## Changed
- shippy now fetches the allowed variants from the server
- shippy now requires shipper 2.14.0 or higher
- Updated library dependencies
  - loguru (0.6.0 -> 0.7.0)
  - rich (13.3.3 -> 13.3.5)
  - setuptools (67.6.1 -> 67.7.2)
  - sentry-sdk (1.19.1 -> 1.21.0)
  - requests (2.28.2 -> 2.29.0)

[1.11.0]: https://github.com/shipperstack/shippy/compare/1.10.4...1.11.0


# [1.10.4] - 2023-04-09

## Changed
- Fixed a looping bug that caused shippy to ask for login credentials repeatedly
- Fixed a bug that might occur when raising an upload exception


[1.10.4]: https://github.com/shipperstack/shippy/compare/1.10.3...1.10.4


# [1.10.3] - 2023-04-09

## Changed
- Switched to urllib for better handling of URLs
- shippy no longer checks for trailing slashes (thanks to urllib)
- Updated library dependencies
  - setuptools (67.4.0 -> 67.6.1)
  - sentry-sdk (1.16.0 -> 1.19.1)
  - rich (13.3.1 -> 13.3.3)
  - semver (2.13.0 -> 3.0.0)


[1.10.3]: https://github.com/shipperstack/shippy/compare/1.10.2...1.10.3


# [1.10.2] - 2023-03-04

## Changed
- shippy now checks if it has been rate-limited for all requests, including login
- Updated library dependencies
  - sentry-sdk (1.15.0 -> 1.16.0)
- General code cleanup and refactor

[1.10.2]: https://github.com/shipperstack/shippy/compare/1.10.1...1.10.2


# [1.10.1] - 2023-02-27

## Added
- Added more exception handling while checking previous upload attempts

## Changed
- Fixed a bug with logging in to servers
- shippy now quits if an exception occurs while logging in, so users don't have to force-quit shippy
- General code cleanup


# [1.10.0] - 2023-02-22

## Added
- Added better logging
- Added custom User Agent string for shippy

## Changed
- shippy now handles 503 errors returned by Cloudflare
- shippy now handles more 5xx errors returned from the server
- A lot of code refactoring to reduce bugs and clean up logic
- Updated library dependencies
  - setuptools (65.6.3 -> 67.4.0)
  - sentry-sdk (1.12.1 -> 1.15.0)
  - rich (13.0.0 -> 13.3.1)
  - requests (2.28.1 -> 2.28.2)
  - humanize (4.4.0 -> 4.5.0)


# [1.9.0] - 2023-01-08

## Added
- Added mechanism to resume uploads after a network failure or crash
- Added mechanisms for alpha/beta build releases
- Added logging mechanism

## Changed
- Updated library dependencies
  - setuptools (65.6.0 -> 65.6.3)
  - sentry-sdk (1.11.1 -> 1.12.1) 
  - rich (12.6.0 -> 13.0.0)
- General code cleanup
- Adjusted message pretty-printing levels
- Stop printing traceback on `KeyboardInterrupt`s
 

# [1.8.0] - 2022-11-23

## Added
- Added a check when loading the configuration file to guard against malformed server URLs

## Changed
- Changed the outdated updater URL to the new repository location
- Updated library dependencies
  - sentry-sdk (1.9.9 -> 1.11.1)
  - rich (12.5.1 -> 12.6.0)
  - setuptools (65.4.1 -> 65.6.0)
- Other miscellaneous changes to improve code quality
- Fixed shippy sending unnecessary bug reports to Sentry when a connection failure occurs 


# [1.7.6] - 2022-09-30

## Changed
- Updated library dependencies
  - sentry-sdk (1.7.2 -> 1.9.9)
  - setuptools (63.2.0 -> 65.4.1)
  - humanize (4.2.3 -> 4.4.0)


# [1.7.5] - 2022-07-19

## Changed
- Updated library dependencies
  - rich (12.4.4 -> 12.5.1)
  - sentry-sdk (1.6.0 -> 1.7.2)
  - setuptools (63.1.0 -> 63.2.0)
 

# [1.7.4] - 2022-07-05

## Changed
- shippy is now licensed under GPLv3
- shippy now requires Python 3.7 or higher
- Updated library dependencies
  - sentry-sdk (1.5.11 -> 1.6.0)
  - setuptools (62.1.0 -> 63.1.0)
  - rich (12.4.1 -> 12.4.4)
  - requests (2.27.1 -> 2.28.1)
  - humanize (4.1.0 -> 4.2.3)


# [1.7.3] - 2022-05-11

## Changed
- Fixed shippy sending incorrect headers during upload


# [1.7.2] - 2022-05-11

## Changed
- Fix shippy not handling errors during the upload phase
- Updated library dependencies
  - rich (12.3.0 -> 12.4.1)


# [1.7.1] - 2022-05-07

## Changed
- shippy now fetches the regex pattern from the server
- shippy directly prints the error message received from the server, instead of uselessly matching the error code to a custom message
- General code cleanup
- Updated library dependencies
  - humanize (4.0.0 -> 4.1.0)
  - sentry-sdk (1.5.10 -> 1.5.11)


# [1.7.0] - 2022-04-30

## Added
- shippy now supports SHA256 checksum files

## Changed
- shippy can check for checksum files that end with the postfix `sum` (for example, `.sha256sum`)
- shippy now sends back the checksum type expected by the server
- General code cleanup
- Updated library dependencies
  - rich (12.2.0 -> 12.3.0)
- Bumped server compatibility version to shipper 1.15.0


# [1.6.0] - 2022-04-19

## Changed
- shippy now checks the compatible version returned by the server
- General code cleanup
- Updated library dependencies
  - sentry-sdk (1.5.6 -> 1.5.10)
  - rich (11.2.0 -> 12.2.0)


# [1.5.4] - 2022-02-26

## Changed
- Fixed a bug with the shippy client that caused it to crash during upload finalization
- Updated library dependencies


# [1.5.3] - 2022-02-20

## Added
- Added prettified message printing to quickly read status messages
- Added status message for when waiting on server to process build artifact

## Changed
- Reduced chunk size to 1 MB to avoid having requests dropped by middleware
- General code cleanup


# [1.5.2] - 2022-02-19

## Changed
- Use `rich` module for all text output and spinner/progress indicators
- Clean up dependencies
- Updated library dependencies


# [1.5.1] - 2021-07-11

## Changed
- Updated shippy to conform with changed API endpoint
- Bumped server compatibility version to shipper 1.8.2


# [1.5.0] - 2021-07-10

## Changed
- Updated API endpoint URLs according to the changes in shipper
- Upload exceptions are now treated as errors and styled accordingly when printed to console
- The server error message has been updated
- Server compatibility version bumped to 1.8.0


# [1.4.2] - 2021-07-03

## Changed
- Fixed a really, really weird redirection edge-case bug: if the server URL schema was set to HTTP but the web server automatically redirected clients to HTTPS, shippy would issue a GET request instead of a POST request when signing in, which would fail because the login endpoint only accepts POST requests. If this happens, shippy now figures out what is going on and rewrites the server URL while letting the user know
- Fixed a bug where the login function could occasionally fail if the response received from the server was unexpected
- General code cleanup


# [1.4.1] - 2021-07-02

## Added
- Added config option `UploadWithoutPrompt`. shippy will automatically upload builds found in the current directory without asking the user for confirmation
- Added command-line option `-y` and `--yes`, which is functionally equal to the `UploadWithoutPrompt` config above

## Changed
- Fixed a bug where shippy would create deprecated sections
- shippy now automatically deletes deprecated sections if detected
- Fixed a bug where shippy would use case-insensitive configuration files
- Code cleanup and optimization


# [1.4.0] - 2021-06-29

## Added
- Added a flag to "disable" the build immediately after uploading (for internal use only)

## Changed
- shippy correctly identifies a missing device error
- Updated invalid configuration message
- Config schema change: the shipper section has been removed
- Bumped server compat to 1.7.0


# [1.3.19] - 2021-06-18

## Changed
- shippy checks if the token is valid on start and prompts if the token is invalid
- Bumped server compatibility version to 1.6.16

# [1.3.18] - 2021-06-15

## Changed
- Hotfix for a potential bug introduced in 1.3.17 while backporting shippy to support older Python versions
  If your upload hangs at 100%, upgrade to this version and try again


# [1.3.17] - 2021-06-15

## Changed
- Fixed logic to work in lower Python versions
- shippy now supports >=Python 3.5 (temporarily, until maintainers can update their systems)


# [1.3.16] - 2021-06-15

## Changed
- Python requirement changed from 3.5 to 3.8


# [1.3.15] - 2021-06-02

## Changed
- shippy now handles connection failures instead of crashing
- shippy no longer crashes on a KeyboardInterrupt (Ctrl-C)
- Bumped server compatibility version to 1.6.12
- Changed and simplified error and warning messages
- General code cleanup


# [1.3.14] - 2021-05-27

## Changed
- The chunk size is now fixed at 10 MB
- shippy now shows more details when logging into the server fails
- shippy will now exit if the server is out-of-date to prevent any potential errors
- General code cleanup

## Removed
- Removed option to upload directly to shipper (use chunked upload mechanism instead)
- Removed unused debug mechanism


# [1.3.13] - 2021-05-24

## Changed
- shippy now identifies 404 errors and asks maintainers to double-check device status


# [1.3.12] - 2021-05-24

## Changed
- Fixed a bug with shippy crashing during response handling
- shippy now outputs error messages in red


# [1.3.11] - 2021-05-24

## Changed
- Fixed the `humanize` module import crash on startup


# [1.3.10] - 2021-05-24

## Changed
- shippy will now defer maintainers to the developers if there is a server-side error
- If the response is not in the form of a JSON, shippy prints the contents instead
- shippy now prints the progress of the upload in humanized format
- Minor code cleanup


# [1.3.9] - 2021-05-24

## Added
- shippy now checks for updates on startup by querying GitHub releases


# [1.3.8] - 2021-05-23

Re-release of 1.3.7


# [1.3.7] - 2021-05-23

## Changed
- shippy no longer tries multiple times if an upload fails
- shippy now warns if multiple builds have been detected
- Made error message more descriptive to help catch more problems
- Code cleanup


# [1.3.6] - 2021-05-22

## Changed
- Fixed a bug with setting the default chunk size if the value is not set


# [1.3.5] - 2021-05-22

## Changed
- Report on exceptions instead of catching them and discarding them
- shippy now displays the upload type in the printout


# [1.3.4] - 2021-05-22

## Changed
- Quick patch to fix the KeyError handling if a default value is not set


# [1.3.3] - 2021-05-20

## Changed
- shippy uses a much lower chunk size by default (10 MB)
- shippy allows you to edit the chunk size config without having to edit the config file, using the commandline argument `-c` or `--chunk-size`
- Chunked-based uploading is now the default (to opt out, edit the configuration file)
- General code cleanup


# [1.3.2] - 2021-05-19

## Changed
- shippy now checks the build before uploading so that you don't waste time uploading an invalid build that shipper will reject
- General code cleanup


# [1.3.1] - 2021-05-19

## Changed
- Hotfix for a bug with the server compatibility check function


# [1.3.0] - 2021-05-19

## Added
- Added support for chunk-based uploading
- Added check for shipper version compatibility

## Changed
- shippy now verifies the URL schema before saving the server URL
- Fixed bug where shippy would constantly ask if you would like to upload again on failure
- Changed API schema means shippy is now incompatible with old shipper versions (and vice versa)
- shippy now backs off if rate-limited (only on chunked uploads)
- Lots and lots of code cleanup and general fix-ups


# [1.2.6] - 2021-05-17

## Changed
- Fixed a couple of problems with packaging


# [1.2.5] - 2021-05-17

## Added
- Added a new chunk-based upload mechanism (beta, requires new version of shipper yet to be released)

## Changed
- Large code cleanup
- Fixed bug where shippy would continuously ask if you would want to re-upload a failed build
- shippy no longer ships with PyInstaller, but is available on PyPI (or will be soon)
- Now licensed under MIT


# [1.2.4] - 2021-04-27

## Changed
- Cleaned up imports
- KeyboardInterrupt errors are no longer reported to Sentry


# [1.2.3] - 2021-02-21

## Added
- Added Sentry to catch bugs

## Changed
- Fixed crash when reading a configuration file created by an older version of shippy
- shippy will now prompt the user multiple times for failed uploads

## Removed
- `VERSION_CODE` has now been deprecated


# [1.2.2] - 2021-02-19

## Changed
- Fixed a regression in 1.2.1


# [1.2.1] - 2021-02-19

## Changed
- Fixed a problem with the undefined exception handler


# [1.2.0] - 2021-02-16

## Added
- Added a progress bar to check the upload status

## Changed
- General code cleanup
- shippy now allows you to specify the server URL during setup
- shippy is more resistent against crashes and failures
- shippy is now more verbose about errors when they occur
- shippy will alert you to more problems reported from the server


[1.10.1]: https://github.com/shipperstack/shippy/compare/1.10.0...1.10.1
[1.10.0]: https://github.com/shipperstack/shippy/compare/1.9.0...1.10.0
[1.9.0]: https://github.com/shipperstack/shippy/compare/1.8.0...1.9.0
[1.8.0]: https://github.com/shipperstack/shippy/compare/1.7.6...1.8.0
[1.7.6]: https://github.com/shipperstack/shippy/compare/1.7.5...1.7.6
[1.7.5]: https://github.com/shipperstack/shippy/compare/1.7.4...1.7.5
[1.7.4]: https://github.com/shipperstack/shippy/compare/1.7.3...1.7.4
[1.7.3]: https://github.com/shipperstack/shippy/compare/1.7.2...1.7.3
[1.7.2]: https://github.com/shipperstack/shippy/compare/1.7.1...1.7.2
[1.7.1]: https://github.com/shipperstack/shippy/compare/1.7.0...1.7.1
[1.7.0]: https://github.com/shipperstack/shippy/compare/1.6.0...1.7.0
[1.6.0]: https://github.com/shipperstack/shippy/compare/1.5.4...1.6.0
[1.5.4]: https://github.com/shipperstack/shippy/compare/1.5.3...1.5.4
[1.5.3]: https://github.com/shipperstack/shippy/compare/1.5.2...1.5.3
[1.5.2]: https://github.com/shipperstack/shippy/compare/1.5.1...1.5.2
[1.5.1]: https://github.com/shipperstack/shippy/compare/1.5.0...1.5.1
[1.5.0]: https://github.com/shipperstack/shippy/compare/1.4.2...1.5.0
[1.4.2]: https://github.com/shipperstack/shippy/compare/1.4.1...1.4.2
[1.4.1]: https://github.com/shipperstack/shippy/compare/1.4.0...1.4.1
[1.4.0]: https://github.com/shipperstack/shippy/compare/1.3.19...1.4.0
[1.3.19]: https://github.com/shipperstack/shippy/compare/1.3.18...1.3.19
[1.3.18]: https://github.com/shipperstack/shippy/compare/1.3.17...1.3.18
[1.3.17]: https://github.com/shipperstack/shippy/compare/1.3.16...1.3.17
[1.3.16]: https://github.com/shipperstack/shippy/compare/1.3.15...1.3.16
[1.3.15]: https://github.com/shipperstack/shippy/compare/1.3.14...1.3.15
[1.3.14]: https://github.com/shipperstack/shippy/compare/1.3.13...1.3.14
[1.3.13]: https://github.com/shipperstack/shippy/compare/1.3.12...1.3.13
[1.3.12]: https://github.com/shipperstack/shippy/compare/1.3.11...1.3.12
[1.3.11]: https://github.com/shipperstack/shippy/compare/1.3.10...1.3.11
[1.3.10]: https://github.com/shipperstack/shippy/compare/1.3.9...1.3.10
[1.3.9]: https://github.com/shipperstack/shippy/compare/1.3.8...1.3.9
[1.3.8]: https://github.com/shipperstack/shippy/compare/1.3.7...1.3.8
[1.3.7]: https://github.com/shipperstack/shippy/compare/1.3.6...1.3.7
[1.3.6]: https://github.com/shipperstack/shippy/compare/1.3.5...1.3.6
[1.3.5]: https://github.com/shipperstack/shippy/compare/1.3.4...1.3.5
[1.3.4]: https://github.com/shipperstack/shippy/compare/1.3.3...1.3.4
[1.3.3]: https://github.com/shipperstack/shippy/compare/1.3.2...1.3.3
[1.3.2]: https://github.com/shipperstack/shippy/compare/1.3.1...1.3.2
[1.3.1]: https://github.com/shipperstack/shippy/compare/1.3.0...1.3.1
[1.3.0]: https://github.com/shipperstack/shippy/compare/1.2.6...1.3.0
[1.2.6]: https://github.com/shipperstack/shippy/compare/1.2.5...1.2.6
[1.2.5]: https://github.com/shipperstack/shippy/compare/1.2.4...1.2.5
[1.2.4]: https://github.com/shipperstack/shippy/compare/1.2.3...1.2.4
[1.2.3]: https://github.com/shipperstack/shippy/compare/1.2.2...1.2.3
[1.2.2]: https://github.com/shipperstack/shippy/compare/1.2.1...1.2.2 
[1.2.1]: https://github.com/shipperstack/shippy/compare/1.2.0...1.2.1
[1.2.0]: https://github.com/shipperstack/shippy/compare/8e5a52e5d19417c406f5a36ef626513175865e55...1.2.0
