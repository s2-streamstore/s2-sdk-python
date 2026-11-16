# Agent Instructions

- A released SDK must keep parsing responses from a newer service:
  - An enum the service can return subclasses `_OpenEnum`. Enums only ever sent by the SDK stay closed.
  - A mapper that switches on a kind (resource set, retention policy, metric) returns `Unknown(kind)` for one it does not recognize, rather than raising or returning `None`.
