# InfraO
![tests](https://github.com/my-organization/infrao/workflows/Tests/badge.svg)
[![codecov.io](https://codecov.io/github/my-organization/infrao/coverage.svg?branch=main)](https://codecov.io/github/my-organization/infrao?branch=main)
![release](https://github.com/my-organization/infrao/workflows/Release/badge.svg)

[![GPLv2 license](https://img.shields.io/badge/License-GPLv2-blue.svg)](https://www.gnu.org/licenses/old-licenses/gpl-2.0.en.html)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Imports: isort](https://img.shields.io/badge/%20imports-isort-%231674b1?style=flat&labelColor=ef8336)](https://pycqa.github.io/isort/)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)

## Usage

The plugin currently is able to initialize a PostgreSQL database based on an initial version of a database schema (which is built according to the InfraO- xsd schema). A working PostgreSQL database with the PostGIS extension is required. To use the tool a connection to the database (database: postgres) must be established in QGIS beforehand.

## Installation

The plugin can be downloaded and installed by moving the contents to your QGIS profiles' plugin folder. The folder can be found from QGIS > Settings > User profiles > Open active profile folder. The plugin must be activated from QGIS > Manage and install extensions. A restart of QGIS might be required.

## Development

Refer to [development](docs/development.md) for developing this QGIS3 plugin.

## License
This plugin is licenced with [GNU General Public License, version 2](https://www.gnu.org/licenses/old-licenses/gpl-2.0.en.html)

See [LICENSE](LICENSE) for more information.
