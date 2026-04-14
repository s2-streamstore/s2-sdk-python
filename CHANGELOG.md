# Changelog

## [0.1.3](https://github.com/s2-streamstore/s2-sdk-python/compare/v0.1.2...v0.1.3) (2026-04-14)


### Bug Fixes

* incorrect tracking of limits after client-side filtering ([#34](https://github.com/s2-streamstore/s2-sdk-python/issues/34)) ([d69e4f0](https://github.com/s2-streamstore/s2-sdk-python/commit/d69e4f0f7e7dc8ec997bd675b96944577bc3036c))

## [0.1.2](https://github.com/s2-streamstore/s2-sdk-python/compare/v0.1.1...v0.1.2) (2026-04-11)


### Bug Fixes

* `CommandRecord.trim` raises `OverflowError` instead of `S2ClientError` ([#29](https://github.com/s2-streamstore/s2-sdk-python/issues/29)) ([f394b1e](https://github.com/s2-streamstore/s2-sdk-python/commit/f394b1ec769d395493256cb89adbb97d2485e077))
* ack for an already cancelled ticket future crashes append session ([#27](https://github.com/s2-streamstore/s2-sdk-python/issues/27)) ([496acfe](https://github.com/s2-streamstore/s2-sdk-python/commit/496acfe4d8f9132f83651614e553627bf0e0ca27))
* linger timeout closes async iterator in `append_record_batches` ([#28](https://github.com/s2-streamstore/s2-sdk-python/issues/28)) ([aaf4bfe](https://github.com/s2-streamstore/s2-sdk-python/commit/aaf4bfe08bd517ee8b429cdc805f1479e08d1343))
* malformed terminal message raises `AttributeError` instead of `S2ServerError` ([#30](https://github.com/s2-streamstore/s2-sdk-python/issues/30)) ([fe08739](https://github.com/s2-streamstore/s2-sdk-python/commit/fe0873989fb3c57dfa036523b9eadbe3a15e8362))
* received data not fully acknowledged during h2 stream cleanup ([#31](https://github.com/s2-streamstore/s2-sdk-python/issues/31)) ([f3527d6](https://github.com/s2-streamstore/s2-sdk-python/commit/f3527d6356e212adb26fd72d248b695c0efede7d))


### Documentation

* add examples for centralized SDK docs  ([#12](https://github.com/s2-streamstore/s2-sdk-python/issues/12)) ([9895ffb](https://github.com/s2-streamstore/s2-sdk-python/commit/9895ffb8da830c297ce1037b3a3743854cee6a59))

## [0.1.1](https://github.com/s2-streamstore/s2-sdk-python/compare/v0.1.0...v0.1.1) (2026-04-08)


### Bug Fixes

* `producer.close()` orphans drain task on error   ([#17](https://github.com/s2-streamstore/s2-sdk-python/issues/17)) ([e448d1d](https://github.com/s2-streamstore/s2-sdk-python/commit/e448d1d8885cd70581746db753d9a9344692d66b))
* body gen hangs on retry when inputs exhausted in append session ([#13](https://github.com/s2-streamstore/s2-sdk-python/issues/13)) ([043be93](https://github.com/s2-streamstore/s2-sdk-python/commit/043be930772f007919d94ebb63c2544acad4c370))
* linger resets on each record arrival in `append_record_batches` ([#14](https://github.com/s2-streamstore/s2-sdk-python/issues/14)) ([70ce203](https://github.com/s2-streamstore/s2-sdk-python/commit/70ce203556ff334a75cb788b3ca53d4dc2839de7))

## 0.1.0 (2026-04-07)


### Features

* add initial version of `s2-sdk` ([#1](https://github.com/s2-streamstore/s2-sdk-python/issues/1)) ([3dc9795](https://github.com/s2-streamstore/s2-sdk-python/commit/3dc979596b10db0881dd3132165467a227ad79d3))
