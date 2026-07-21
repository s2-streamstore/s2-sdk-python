# Changelog

## [0.7.0](https://github.com/s2-streamstore/s2-sdk-python/compare/v0.6.0...v0.7.0) (2026-07-21)


### ⚠ BREAKING CHANGES

* introduce `ReadSession` with caught-up state tracking  ([#88](https://github.com/s2-streamstore/s2-sdk-python/issues/88))

### Features

* introduce `ReadSession` with caught-up state tracking  ([#88](https://github.com/s2-streamstore/s2-sdk-python/issues/88)) ([55da950](https://github.com/s2-streamstore/s2-sdk-python/commit/55da9502bac470b0baf8cbd6780c9e89474ce866))


### Documentation

* use context manager in read session examples ([#90](https://github.com/s2-streamstore/s2-sdk-python/issues/90)) ([6cfbd98](https://github.com/s2-streamstore/s2-sdk-python/commit/6cfbd98558fcba56c5c14cf426eee327004c6f46))

## [0.6.0](https://github.com/s2-streamstore/s2-sdk-python/compare/v0.5.0...v0.6.0) (2026-07-08)


### ⚠ BREAKING CHANGES

* incorrect and inconsistent yield semantics in `append_record_batches` ([#85](https://github.com/s2-streamstore/s2-sdk-python/issues/85))

### Bug Fixes

* incorrect and inconsistent yield semantics in `append_record_batches` ([#85](https://github.com/s2-streamstore/s2-sdk-python/issues/85)) ([65c5590](https://github.com/s2-streamstore/s2-sdk-python/commit/65c559042332a1c06eaa320be0b03ac03dd7a355))
* uncaught `asyncio.CancelledError` in `Connection.send_headers` ([#87](https://github.com/s2-streamstore/s2-sdk-python/issues/87)) ([c050a9d](https://github.com/s2-streamstore/s2-sdk-python/commit/c050a9d02326293bbf1099c71a12efca956b6f36))

## [0.5.0](https://github.com/s2-streamstore/s2-sdk-python/compare/v0.4.3...v0.5.0) (2026-07-07)


### Features

* use `a.s2.dev` as the default account endpoint ([#83](https://github.com/s2-streamstore/s2-sdk-python/issues/83)) ([4e060c7](https://github.com/s2-streamstore/s2-sdk-python/commit/4e060c7b8899742967d512bf19e10e5fec6a4b6c))

## [0.4.3](https://github.com/s2-streamstore/s2-sdk-python/compare/v0.4.2...v0.4.3) (2026-06-23)


### Documentation

* update encryption examples for central docs site  ([#79](https://github.com/s2-streamstore/s2-sdk-python/issues/79)) ([973f6b7](https://github.com/s2-streamstore/s2-sdk-python/commit/973f6b7a242475fa4300b7b01cd03c8b4384cdab))

## [0.4.2](https://github.com/s2-streamstore/s2-sdk-python/compare/v0.4.1...v0.4.2) (2026-06-13)


### Bug Fixes

* incorrect ack deadline semantics in append session  ([#64](https://github.com/s2-streamstore/s2-sdk-python/issues/64)) ([248e5c0](https://github.com/s2-streamstore/s2-sdk-python/commit/248e5c0b1a2776edcd59783826feee34842651d8))
* unawaited `asyncio.Task` cancellations  ([#78](https://github.com/s2-streamstore/s2-sdk-python/issues/78)) ([4d4ac80](https://github.com/s2-streamstore/s2-sdk-python/commit/4d4ac8022ec4b773dff506b0f0cbec220906ec67))

## [0.4.1](https://github.com/s2-streamstore/s2-sdk-python/compare/v0.4.0...v0.4.1) (2026-06-09)


### Bug Fixes

* missing `fallible` decorator for public methods in `ops` mod ([#71](https://github.com/s2-streamstore/s2-sdk-python/issues/71)) ([74d7c70](https://github.com/s2-streamstore/s2-sdk-python/commit/74d7c70c7ca3aaaa7f4538dd5e3d9840f55f6e38))
* missing check for unexpected response stream close in append session  ([#74](https://github.com/s2-streamstore/s2-sdk-python/issues/74)) ([1d68ddf](https://github.com/s2-streamstore/s2-sdk-python/commit/1d68ddf22a3eaa4c6b2fbd0826d46b70435a5161))

## [0.4.0](https://github.com/s2-streamstore/s2-sdk-python/compare/v0.3.1...v0.4.0) (2026-05-23)


### ⚠ BREAKING CHANGES

* add `location` ops, replace `BasinScope` with `LocationInfo` ([#61](https://github.com/s2-streamstore/s2-sdk-python/issues/61))

### Features

* add `location` ops, replace `BasinScope` with `LocationInfo` ([#61](https://github.com/s2-streamstore/s2-sdk-python/issues/61)) ([d1157ad](https://github.com/s2-streamstore/s2-sdk-python/commit/d1157adb1471dbba6abdc1c6a495cfac204d6c4e))

## [0.3.1](https://github.com/s2-streamstore/s2-sdk-python/compare/v0.3.0...v0.3.1) (2026-05-23)


### Documentation

* add missing note block to `ensure_stream` op ([#59](https://github.com/s2-streamstore/s2-sdk-python/issues/59)) ([2ce5fef](https://github.com/s2-streamstore/s2-sdk-python/commit/2ce5fefb5d1aece49d2a46dbf945391387b412cd))

## [0.3.0](https://github.com/s2-streamstore/s2-sdk-python/compare/v0.2.2...v0.3.0) (2026-05-21)


### Features

* add `ensure_basin` and `ensure_stream` ops   ([#56](https://github.com/s2-streamstore/s2-sdk-python/issues/56)) ([b57079c](https://github.com/s2-streamstore/s2-sdk-python/commit/b57079c7aab1d104320491526b635a94cb6cd00e))

## [0.2.2](https://github.com/s2-streamstore/s2-sdk-python/compare/v0.2.1...v0.2.2) (2026-05-17)


### Bug Fixes

* uncapped and eager backoff calculation  ([#52](https://github.com/s2-streamstore/s2-sdk-python/issues/52)) ([89ba250](https://github.com/s2-streamstore/s2-sdk-python/commit/89ba250d48c2d388bc3c9ec7063dcc8c12afe515))

## [0.2.1](https://github.com/s2-streamstore/s2-sdk-python/compare/v0.2.0...v0.2.1) (2026-05-11)


### Bug Fixes

* batch accumulator doesn't flush when source iter raises  ([#49](https://github.com/s2-streamstore/s2-sdk-python/issues/49)) ([cd20814](https://github.com/s2-streamstore/s2-sdk-python/commit/cd208149b2d69a2e075a44f6a894ffc469d57014))
* incorrect frame signal reset condition after resending append inputs  ([#47](https://github.com/s2-streamstore/s2-sdk-python/issues/47)) ([49c3237](https://github.com/s2-streamstore/s2-sdk-python/commit/49c3237a7c37cc5b63f0327688aab53ac468412d))
* pending streams not failed when GOAWAY is received  ([#50](https://github.com/s2-streamstore/s2-sdk-python/issues/50)) ([74baa61](https://github.com/s2-streamstore/s2-sdk-python/commit/74baa612bf102d12b850301fc678d4df6f1c670d))

## [0.2.0](https://github.com/s2-streamstore/s2-sdk-python/compare/v0.1.3...v0.2.0) (2026-04-23)


### Features

* encryption support ([#37](https://github.com/s2-streamstore/s2-sdk-python/issues/37)) ([2106eda](https://github.com/s2-streamstore/s2-sdk-python/commit/2106eda2f4ba531584f6e66f1b703aa4d519a7b7))

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
