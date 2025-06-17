# Changelog

All notable changes to this project will be documented in this file.

## [0.1.0] - 2025-06-17
- Merged PR #1 by @MarcChen: Add initial implementation of HoopsFactory Downloader
This pull request introduces a new Python project, `hoopsfactory-downloader`, designed to automate downloading videos from HoopsFactory. Key changes include the addition of environment variable configuration, comprehensive documentation updates, and dependency management setup using Poetry.

### Environment Configuration:
* [`.env.template`](diffhunk://#diff-749e06f64632f62a0c0dfbf4c4f3850e27e94ac109aa121fabd5c29469ae88deR1-R12): Added template for environment variables required to configure login credentials, base URL, and download directory. This simplifies setup for users.

### Documentation Updates:
* [`README.md`](diffhunk://#diff-b335630551682c19a781afebcf4d07bf978fb1f8ac04c6bf87428ed5106870f5L1-R202): Overhauled documentation to include prerequisites, installation steps, environment variable setup, usage instructions, troubleshooting tips, and security notes. Added detailed guidance for automated execution using Windows Task Scheduler.

### Dependency Management:
* [`pyproject.toml`](diffhunk://#diff-50c86b7ed8ac2cf95bd48334961bf0530cdc77b5a56f852c5c61b89d735fd711R1-R24): Configured the project with Poetry, specifying dependencies (`playwright`, `requests`, `python-dotenv`) and development tools (`pytest`, `black`, `flake8`). Defined a script entry point for easier execution.

