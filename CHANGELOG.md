# Changelog

## [0.1.1](https://github.com/s2-streamstore/s2-sdk-python/compare/v0.1.0...v0.1.1) (2026-04-08)


### Bug Fixes

* `producer.close()` orphans drain task on error   ([#17](https://github.com/s2-streamstore/s2-sdk-python/issues/17)) ([e448d1d](https://github.com/s2-streamstore/s2-sdk-python/commit/e448d1d8885cd70581746db753d9a9344692d66b))
* body gen hangs on retry when inputs exhausted in append session ([#13](https://github.com/s2-streamstore/s2-sdk-python/issues/13)) ([043be93](https://github.com/s2-streamstore/s2-sdk-python/commit/043be930772f007919d94ebb63c2544acad4c370))
* linger resets on each record arrival in `append_record_batches` ([#14](https://github.com/s2-streamstore/s2-sdk-python/issues/14)) ([70ce203](https://github.com/s2-streamstore/s2-sdk-python/commit/70ce203556ff334a75cb788b3ca53d4dc2839de7))

## 0.1.0 (2026-04-07)


### Features

* add initial version of `s2-sdk` ([#1](https://github.com/s2-streamstore/s2-sdk-python/issues/1)) ([3dc9795](https://github.com/s2-streamstore/s2-sdk-python/commit/3dc979596b10db0881dd3132165467a227ad79d3))
