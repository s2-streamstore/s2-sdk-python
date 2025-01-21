__all__ = [
    "CommandRecord",
    "metered_bytes",
]

from typing import Iterable

from streamstore.schemas import Record, SequencedRecord


class CommandRecord:
    """
    Helper class for creating `command records <https://s2.dev/docs/stream#command-records>`_.
    """

    FENCE = b"fence"
    TRIM = b"trim"

    @staticmethod
    def fence(token: bytes) -> Record:
        """
        Create a fence command record.

        Args:
            token: `Fencing token <https://s2.dev/docs/stream#fencing-token>`_. Cannot exceed 16 bytes. If empty, clears the previously set token.
        """
        if len(token) > 16:
            raise ValueError("fencing token cannot be greater than 16 bytes")
        return Record(body=token, headers=[(bytes(), CommandRecord.FENCE)])

    @staticmethod
    def trim(desired_first_seq_num: int) -> Record:
        """
        Create a trim command record.

        Args:
            desired_first_seq_num: Sequence number for the first record to exist after trimming
                preceeding records in the stream.

        Note:
            If **desired_first_seq_num** was smaller than the sequence number for the first existing
            record in the stream, trimming doesn't happen.
        """
        return Record(
            body=desired_first_seq_num.to_bytes(8),
            headers=[(bytes(), CommandRecord.TRIM)],
        )


def metered_bytes(records: Iterable[Record | SequencedRecord]) -> int:
    """
    Each record is metered using the following formula:

    .. code-block:: python

        8 + 2 * len(headers)
        + sum((len(name) + len(value)) for (name, value) in headers)
        + len(body)

    """
    return sum(
        (
            8
            + 2 * len(record.headers)
            + sum((len(name) + len(value)) for (name, value) in record.headers)
            + len(record.body)
        )
        for record in records
    )
