# Changelog

The format is based on [Keep a Changelog][keep-a-changelog].

[keep-a-changelog]: https://keepachangelog.com/en/1.0.0/

# [Unreleased]

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
- VERSION_CODE has now been deprecated


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


[Unreleased]: https://github.com/ericswpark/shippy/compare/1.5.2...HEAD
[1.5.2]: https://github.com/ericswpark/shippy/compare/1.5.1...1.5.2
[1.5.1]: https://github.com/ericswpark/shippy/compare/1.5.0...1.5.1
[1.5.0]: https://github.com/ericswpark/shippy/compare/1.4.2...1.5.0
[1.4.2]: https://github.com/ericswpark/shippy/compare/1.4.1...1.4.2
[1.4.1]: https://github.com/ericswpark/shippy/compare/1.4.0...1.4.1
[1.4.0]: https://github.com/ericswpark/shippy/compare/1.3.19...1.4.0
[1.3.19]: https://github.com/ericswpark/shippy/compare/1.3.18...1.3.19
[1.3.18]: https://github.com/ericswpark/shippy/compare/1.3.17...1.3.18
[1.3.17]: https://github.com/ericswpark/shippy/compare/1.3.16...1.3.17
[1.3.16]: https://github.com/ericswpark/shippy/compare/1.3.15...1.3.16
[1.3.15]: https://github.com/ericswpark/shippy/compare/1.3.14...1.3.15
[1.3.14]: https://github.com/ericswpark/shippy/compare/1.3.13...1.3.14
[1.3.13]: https://github.com/ericswpark/shippy/compare/1.3.12...1.3.13
[1.3.12]: https://github.com/ericswpark/shippy/compare/1.3.11...1.3.12
[1.3.11]: https://github.com/ericswpark/shippy/compare/1.3.10...1.3.11
[1.3.10]: https://github.com/ericswpark/shippy/compare/1.3.9...1.3.10
[1.3.9]: https://github.com/ericswpark/shippy/compare/1.3.8...1.3.9
[1.3.8]: https://github.com/ericswpark/shippy/compare/1.3.7...1.3.8
[1.3.7]: https://github.com/ericswpark/shippy/compare/1.3.6...1.3.7
[1.3.6]: https://github.com/ericswpark/shippy/compare/1.3.5...1.3.6
[1.3.5]: https://github.com/ericswpark/shippy/compare/1.3.4...1.3.5
[1.3.4]: https://github.com/ericswpark/shippy/compare/1.3.3...1.3.4
[1.3.3]: https://github.com/ericswpark/shippy/compare/1.3.2...1.3.3
[1.3.2]: https://github.com/ericswpark/shippy/compare/1.3.1...1.3.2
[1.3.1]: https://github.com/ericswpark/shippy/compare/1.3.0...1.3.1
[1.3.0]: https://github.com/ericswpark/shippy/compare/1.2.6...1.3.0
[1.2.6]: https://github.com/ericswpark/shippy/compare/1.2.5...1.2.6
[1.2.5]: https://github.com/ericswpark/shippy/compare/1.2.4...1.2.5
[1.2.4]: https://github.com/ericswpark/shippy/compare/1.2.3...1.2.4
[1.2.3]: https://github.com/ericswpark/shippy/compare/1.2.2...1.2.3
[1.2.2]: https://github.com/ericswpark/shippy/compare/1.2.1...1.2.2 
[1.2.1]: https://github.com/ericswpark/shippy/compare/1.2.0...1.2.1
[1.2.0]: https://github.com/ericswpark/shippy/compare/8e5a52e5d19417c406f5a36ef626513175865e55...1.2.0