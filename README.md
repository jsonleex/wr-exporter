# wr-exporter

This is a simple exporter for weread.

## Requirements

- python 3.12.4
- selenium 4.23.1
- webdriver-manager 4.0.2

## Usage

```shell
usage: wre [-h] [-o OUTPUT] [--dev] url

Simple Exporter for weread.

positional arguments:
  url         The url of the book to export

options:
  -h, --help  show this help message and exit
  -o OUTPUT   Output directory for the exported files
  --dev       Disable headless mode, use only for debugging
```
