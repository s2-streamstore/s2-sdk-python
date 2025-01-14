# API Reference

```{eval-rst}
.. automodule:: streamstore
    :members:
    :member-order: bysource

.. module:: streamstore._client

.. autoclass:: Basin()
    :members:
    :member-order: bysource

.. autoclass:: Stream()
    :members:
    :member-order: bysource

.. module:: streamstore.schemas
    :no-index:
.. autoclass:: Record(body: bytes, headers: list[tuple[bytes, bytes]] = [])
    :members:

.. automodule:: streamstore.schemas
    :members:
    :exclude-members: Record
    :member-order: bysource

.. _metered-bytes:

Metered bytes
=============

    .. code-block:: python

        metered_bytes = lambda record: 8 + 2 * len(record.headers) \
            + sum((len(name) + len(value)) for (name, value) in record.headers) \
            + len(record.body)

```