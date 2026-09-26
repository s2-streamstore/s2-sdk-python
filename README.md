# s2-sdk
<div>
  <p>
    <!-- PyPI -->
    <a href="https://pypi.org/project/s2-sdk/"><img src="https://img.shields.io/pypi/v/s2-sdk" /></a>
    <!-- Read the docs -->
    <a href="https://s2-sdk.readthedocs.io/"><img src="https://img.shields.io/readthedocs/s2-sdk/latest" /></a>
    <!-- Discord -->
    <a href="https://discord.gg/vTCs7kMkAf"><img src="https://img.shields.io/discord/1209937852528599092?logo=discord" /></a>
    <!-- LICENSE -->
    <a href="https://github.com/s2-streamstore/s2-sdk-python/blob/main/LICENSE"><img src="https://img.shields.io/github/license/s2-streamstore/s2-sdk-python" /></a>
  </p>
</div>

`s2-sdk` is the Python SDK for [S2](https://s2.dev/).

## Project links

- [PyPI](https://pypi.org/project/s2-sdk/)
- [Documentation](https://s2-sdk.readthedocs.io/)
- [GitHub](https://github.com/s2-streamstore/s2-sdk-python)

## Requirements

Python >= 3.11

## Installation

You can install the package from the [Python Package Index](https://pypi.org/project/s2-sdk) using the package manager of your choice. E.g., with `pip`:

```bash
pip install s2-sdk
```

## Storage classes

Use plain strings for storage-class names:

```python
from s2_sdk import StreamConfig

config = StreamConfig(storage_class="express")
```

Discover available names and defaults with `await client.list_locations()`.
Each location exposes `storage_classes` and `default_storage_class`; both may
be `None` on older servers. See [the discovery example](https://github.com/s2-streamstore/s2-sdk-python/blob/main/examples/locations.py).

Leaving `storage_class` as `None` omits the field: creation inherits the
location or basin default, and reconfiguration leaves the value unchanged.

The `StorageClass` enum has been removed. Replace `StorageClass.EXPRESS` with
`"express"`, `StorageClass.STANDARD` with `"standard"`, and type annotations with
`str`.

## Get in touch

Join our [Discord](https://discord.gg/vTCs7kMkAf) server. We would love to hear
from you.

You can also email us at [hi@s2.dev](mailto:hi@s2.dev).
