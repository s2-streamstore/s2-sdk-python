# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# NO CHECKED-IN PROTOBUF GENCODE
# source: s2/v1alpha/s2.proto
# Protobuf Python Version: 5.29.0
"""Generated protocol buffer code."""

from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder

_runtime_version.ValidateProtobufRuntimeVersion(
    _runtime_version.Domain.PUBLIC, 5, 29, 0, "", "s2/v1alpha/s2.proto"
)
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()


from google.protobuf import field_mask_pb2 as google_dot_protobuf_dot_field__mask__pb2


DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(
    b'\n\x13s2/v1alpha/s2.proto\x12\ns2.v1alpha\x1a google/protobuf/field_mask.proto"V\n\x11ListBasinsRequest\x12\x0e\n\x06prefix\x18\x01 \x01(\t\x12\x13\n\x0bstart_after\x18\x02 \x01(\t\x12\x12\n\x05limit\x18\x03 \x01(\x04H\x00\x88\x01\x01\x42\x08\n\x06_limit"M\n\x12ListBasinsResponse\x12%\n\x06\x62\x61sins\x18\x01 \x03(\x0b\x32\x15.s2.v1alpha.BasinInfo\x12\x10\n\x08has_more\x18\x02 \x01(\x08"{\n\x12\x43reateBasinRequest\x12\r\n\x05\x62\x61sin\x18\x01 \x01(\t\x12\'\n\x06\x63onfig\x18\x02 \x01(\x0b\x32\x17.s2.v1alpha.BasinConfig\x12\x0f\n\x05scope\x18\x03 \x01(\tH\x00\x12\x0e\n\x04\x63\x65ll\x18\x04 \x01(\tH\x00\x42\x0c\n\nassignment":\n\x13\x43reateBasinResponse\x12#\n\x04info\x18\x01 \x01(\x0b\x32\x15.s2.v1alpha.BasinInfo"#\n\x12\x44\x65leteBasinRequest\x12\r\n\x05\x62\x61sin\x18\x01 \x01(\t"\x15\n\x13\x44\x65leteBasinResponse"&\n\x15GetBasinConfigRequest\x12\r\n\x05\x62\x61sin\x18\x01 \x01(\t"A\n\x16GetBasinConfigResponse\x12\'\n\x06\x63onfig\x18\x01 \x01(\x0b\x32\x17.s2.v1alpha.BasinConfig"{\n\x17ReconfigureBasinRequest\x12\r\n\x05\x62\x61sin\x18\x01 \x01(\t\x12\'\n\x06\x63onfig\x18\x02 \x01(\x0b\x32\x17.s2.v1alpha.BasinConfig\x12(\n\x04mask\x18\x03 \x01(\x0b\x32\x1a.google.protobuf.FieldMask"C\n\x18ReconfigureBasinResponse\x12\'\n\x06\x63onfig\x18\x01 \x01(\x0b\x32\x17.s2.v1alpha.BasinConfig"V\n\nStreamInfo\x12\x0c\n\x04name\x18\x01 \x01(\t\x12\x12\n\ncreated_at\x18\x02 \x01(\r\x12\x17\n\ndeleted_at\x18\x03 \x01(\rH\x00\x88\x01\x01\x42\r\n\x0b_deleted_at"W\n\x12ListStreamsRequest\x12\x0e\n\x06prefix\x18\x01 \x01(\t\x12\x13\n\x0bstart_after\x18\x02 \x01(\t\x12\x12\n\x05limit\x18\x03 \x01(\x04H\x00\x88\x01\x01\x42\x08\n\x06_limit"P\n\x13ListStreamsResponse\x12\'\n\x07streams\x18\x01 \x03(\x0b\x32\x16.s2.v1alpha.StreamInfo\x12\x10\n\x08has_more\x18\x02 \x01(\x08"O\n\x13\x43reateStreamRequest\x12\x0e\n\x06stream\x18\x01 \x01(\t\x12(\n\x06\x63onfig\x18\x02 \x01(\x0b\x32\x18.s2.v1alpha.StreamConfig"<\n\x14\x43reateStreamResponse\x12$\n\x04info\x18\x01 \x01(\x0b\x32\x16.s2.v1alpha.StreamInfo"%\n\x13\x44\x65leteStreamRequest\x12\x0e\n\x06stream\x18\x01 \x01(\t"\x16\n\x14\x44\x65leteStreamResponse"(\n\x16GetStreamConfigRequest\x12\x0e\n\x06stream\x18\x01 \x01(\t"C\n\x17GetStreamConfigResponse\x12(\n\x06\x63onfig\x18\x01 \x01(\x0b\x32\x18.s2.v1alpha.StreamConfig"~\n\x18ReconfigureStreamRequest\x12\x0e\n\x06stream\x18\x01 \x01(\t\x12(\n\x06\x63onfig\x18\x02 \x01(\x0b\x32\x18.s2.v1alpha.StreamConfig\x12(\n\x04mask\x18\x03 \x01(\x0b\x32\x1a.google.protobuf.FieldMask"E\n\x19ReconfigureStreamResponse\x12(\n\x06\x63onfig\x18\x01 \x01(\x0b\x32\x18.s2.v1alpha.StreamConfig""\n\x10\x43heckTailRequest\x12\x0e\n\x06stream\x18\x01 \x01(\t")\n\x11\x43heckTailResponse\x12\x14\n\x0cnext_seq_num\x18\x01 \x01(\x04"\xa4\x01\n\x0b\x41ppendInput\x12\x0e\n\x06stream\x18\x01 \x01(\t\x12)\n\x07records\x18\x02 \x03(\x0b\x32\x18.s2.v1alpha.AppendRecord\x12\x1a\n\rmatch_seq_num\x18\x03 \x01(\x04H\x00\x88\x01\x01\x12\x1a\n\rfencing_token\x18\x04 \x01(\x0cH\x01\x88\x01\x01\x42\x10\n\x0e_match_seq_numB\x10\n\x0e_fencing_token"P\n\x0c\x41ppendOutput\x12\x15\n\rstart_seq_num\x18\x01 \x01(\x04\x12\x13\n\x0b\x65nd_seq_num\x18\x02 \x01(\x04\x12\x14\n\x0cnext_seq_num\x18\x03 \x01(\x04"7\n\rAppendRequest\x12&\n\x05input\x18\x01 \x01(\x0b\x32\x17.s2.v1alpha.AppendInput":\n\x0e\x41ppendResponse\x12(\n\x06output\x18\x01 \x01(\x0b\x32\x18.s2.v1alpha.AppendOutput">\n\x14\x41ppendSessionRequest\x12&\n\x05input\x18\x01 \x01(\x0b\x32\x17.s2.v1alpha.AppendInput"A\n\x15\x41ppendSessionResponse\x12(\n\x06output\x18\x01 \x01(\x0b\x32\x18.s2.v1alpha.AppendOutput"z\n\nReadOutput\x12\x31\n\x05\x62\x61tch\x18\x01 \x01(\x0b\x32 .s2.v1alpha.SequencedRecordBatchH\x00\x12\x17\n\rfirst_seq_num\x18\x02 \x01(\x04H\x00\x12\x16\n\x0cnext_seq_num\x18\x03 \x01(\x04H\x00\x42\x08\n\x06output"Z\n\x0bReadRequest\x12\x0e\n\x06stream\x18\x01 \x01(\t\x12\x15\n\rstart_seq_num\x18\x02 \x01(\x04\x12$\n\x05limit\x18\x03 \x01(\x0b\x32\x15.s2.v1alpha.ReadLimit"6\n\x0cReadResponse\x12&\n\x06output\x18\x01 \x01(\x0b\x32\x16.s2.v1alpha.ReadOutput"G\n\tReadLimit\x12\x12\n\x05\x63ount\x18\x01 \x01(\x04H\x00\x88\x01\x01\x12\x12\n\x05\x62ytes\x18\x02 \x01(\x04H\x01\x88\x01\x01\x42\x08\n\x06_countB\x08\n\x06_bytes"a\n\x12ReadSessionRequest\x12\x0e\n\x06stream\x18\x01 \x01(\t\x12\x15\n\rstart_seq_num\x18\x02 \x01(\x04\x12$\n\x05limit\x18\x03 \x01(\x0b\x32\x15.s2.v1alpha.ReadLimit"=\n\x13ReadSessionResponse\x12&\n\x06output\x18\x01 \x01(\x0b\x32\x16.s2.v1alpha.ReadOutput"b\n\x0cStreamConfig\x12/\n\rstorage_class\x18\x01 \x01(\x0e\x32\x18.s2.v1alpha.StorageClass\x12\r\n\x03\x61ge\x18\x02 \x01(\x04H\x00\x42\x12\n\x10retention_policy"F\n\x0b\x42\x61sinConfig\x12\x37\n\x15\x64\x65\x66\x61ult_stream_config\x18\x01 \x01(\x0b\x32\x18.s2.v1alpha.StreamConfig"]\n\tBasinInfo\x12\x0c\n\x04name\x18\x01 \x01(\t\x12\r\n\x05scope\x18\x02 \x01(\t\x12\x0c\n\x04\x63\x65ll\x18\x03 \x01(\t\x12%\n\x05state\x18\x04 \x01(\x0e\x32\x16.s2.v1alpha.BasinState"%\n\x06Header\x12\x0c\n\x04name\x18\x01 \x01(\x0c\x12\r\n\x05value\x18\x02 \x01(\x0c"A\n\x0c\x41ppendRecord\x12#\n\x07headers\x18\x01 \x03(\x0b\x32\x12.s2.v1alpha.Header\x12\x0c\n\x04\x62ody\x18\x02 \x01(\x0c"U\n\x0fSequencedRecord\x12\x0f\n\x07seq_num\x18\x01 \x01(\x04\x12#\n\x07headers\x18\x02 \x03(\x0b\x32\x12.s2.v1alpha.Header\x12\x0c\n\x04\x62ody\x18\x03 \x01(\x0c"D\n\x14SequencedRecordBatch\x12,\n\x07records\x18\x01 \x03(\x0b\x32\x1b.s2.v1alpha.SequencedRecord*d\n\x0cStorageClass\x12\x1d\n\x19STORAGE_CLASS_UNSPECIFIED\x10\x00\x12\x1a\n\x16STORAGE_CLASS_STANDARD\x10\x01\x12\x19\n\x15STORAGE_CLASS_EXPRESS\x10\x02*u\n\nBasinState\x12\x1b\n\x17\x42\x41SIN_STATE_UNSPECIFIED\x10\x00\x12\x16\n\x12\x42\x41SIN_STATE_ACTIVE\x10\x01\x12\x18\n\x14\x42\x41SIN_STATE_CREATING\x10\x02\x12\x18\n\x14\x42\x41SIN_STATE_DELETING\x10\x03\x32\xce\x03\n\x0e\x41\x63\x63ountService\x12P\n\nListBasins\x12\x1d.s2.v1alpha.ListBasinsRequest\x1a\x1e.s2.v1alpha.ListBasinsResponse"\x03\x90\x02\x01\x12S\n\x0b\x43reateBasin\x12\x1e.s2.v1alpha.CreateBasinRequest\x1a\x1f.s2.v1alpha.CreateBasinResponse"\x03\x90\x02\x02\x12S\n\x0b\x44\x65leteBasin\x12\x1e.s2.v1alpha.DeleteBasinRequest\x1a\x1f.s2.v1alpha.DeleteBasinResponse"\x03\x90\x02\x02\x12\x62\n\x10ReconfigureBasin\x12#.s2.v1alpha.ReconfigureBasinRequest\x1a$.s2.v1alpha.ReconfigureBasinResponse"\x03\x90\x02\x02\x12\\\n\x0eGetBasinConfig\x12!.s2.v1alpha.GetBasinConfigRequest\x1a".s2.v1alpha.GetBasinConfigResponse"\x03\x90\x02\x01\x32\xdb\x03\n\x0c\x42\x61sinService\x12S\n\x0bListStreams\x12\x1e.s2.v1alpha.ListStreamsRequest\x1a\x1f.s2.v1alpha.ListStreamsResponse"\x03\x90\x02\x01\x12V\n\x0c\x43reateStream\x12\x1f.s2.v1alpha.CreateStreamRequest\x1a .s2.v1alpha.CreateStreamResponse"\x03\x90\x02\x02\x12V\n\x0c\x44\x65leteStream\x12\x1f.s2.v1alpha.DeleteStreamRequest\x1a .s2.v1alpha.DeleteStreamResponse"\x03\x90\x02\x02\x12_\n\x0fGetStreamConfig\x12".s2.v1alpha.GetStreamConfigRequest\x1a#.s2.v1alpha.GetStreamConfigResponse"\x03\x90\x02\x01\x12\x65\n\x11ReconfigureStream\x12$.s2.v1alpha.ReconfigureStreamRequest\x1a%.s2.v1alpha.ReconfigureStreamResponse"\x03\x90\x02\x02\x32\x90\x03\n\rStreamService\x12M\n\tCheckTail\x12\x1c.s2.v1alpha.CheckTailRequest\x1a\x1d.s2.v1alpha.CheckTailResponse"\x03\x90\x02\x01\x12?\n\x06\x41ppend\x12\x19.s2.v1alpha.AppendRequest\x1a\x1a.s2.v1alpha.AppendResponse\x12X\n\rAppendSession\x12 .s2.v1alpha.AppendSessionRequest\x1a!.s2.v1alpha.AppendSessionResponse(\x01\x30\x01\x12>\n\x04Read\x12\x17.s2.v1alpha.ReadRequest\x1a\x18.s2.v1alpha.ReadResponse"\x03\x90\x02\x01\x12U\n\x0bReadSession\x12\x1e.s2.v1alpha.ReadSessionRequest\x1a\x1f.s2.v1alpha.ReadSessionResponse"\x03\x90\x02\x01\x30\x01\x62\x06proto3'
)

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, "s2.v1alpha.s2_pb2", _globals)
if not _descriptor._USE_C_DESCRIPTORS:
    DESCRIPTOR._loaded_options = None
    _globals["_ACCOUNTSERVICE"].methods_by_name["ListBasins"]._loaded_options = None
    _globals["_ACCOUNTSERVICE"].methods_by_name[
        "ListBasins"
    ]._serialized_options = b"\220\002\001"
    _globals["_ACCOUNTSERVICE"].methods_by_name["CreateBasin"]._loaded_options = None
    _globals["_ACCOUNTSERVICE"].methods_by_name[
        "CreateBasin"
    ]._serialized_options = b"\220\002\002"
    _globals["_ACCOUNTSERVICE"].methods_by_name["DeleteBasin"]._loaded_options = None
    _globals["_ACCOUNTSERVICE"].methods_by_name[
        "DeleteBasin"
    ]._serialized_options = b"\220\002\002"
    _globals["_ACCOUNTSERVICE"].methods_by_name[
        "ReconfigureBasin"
    ]._loaded_options = None
    _globals["_ACCOUNTSERVICE"].methods_by_name[
        "ReconfigureBasin"
    ]._serialized_options = b"\220\002\002"
    _globals["_ACCOUNTSERVICE"].methods_by_name["GetBasinConfig"]._loaded_options = None
    _globals["_ACCOUNTSERVICE"].methods_by_name[
        "GetBasinConfig"
    ]._serialized_options = b"\220\002\001"
    _globals["_BASINSERVICE"].methods_by_name["ListStreams"]._loaded_options = None
    _globals["_BASINSERVICE"].methods_by_name[
        "ListStreams"
    ]._serialized_options = b"\220\002\001"
    _globals["_BASINSERVICE"].methods_by_name["CreateStream"]._loaded_options = None
    _globals["_BASINSERVICE"].methods_by_name[
        "CreateStream"
    ]._serialized_options = b"\220\002\002"
    _globals["_BASINSERVICE"].methods_by_name["DeleteStream"]._loaded_options = None
    _globals["_BASINSERVICE"].methods_by_name[
        "DeleteStream"
    ]._serialized_options = b"\220\002\002"
    _globals["_BASINSERVICE"].methods_by_name["GetStreamConfig"]._loaded_options = None
    _globals["_BASINSERVICE"].methods_by_name[
        "GetStreamConfig"
    ]._serialized_options = b"\220\002\001"
    _globals["_BASINSERVICE"].methods_by_name[
        "ReconfigureStream"
    ]._loaded_options = None
    _globals["_BASINSERVICE"].methods_by_name[
        "ReconfigureStream"
    ]._serialized_options = b"\220\002\002"
    _globals["_STREAMSERVICE"].methods_by_name["CheckTail"]._loaded_options = None
    _globals["_STREAMSERVICE"].methods_by_name[
        "CheckTail"
    ]._serialized_options = b"\220\002\001"
    _globals["_STREAMSERVICE"].methods_by_name["Read"]._loaded_options = None
    _globals["_STREAMSERVICE"].methods_by_name[
        "Read"
    ]._serialized_options = b"\220\002\001"
    _globals["_STREAMSERVICE"].methods_by_name["ReadSession"]._loaded_options = None
    _globals["_STREAMSERVICE"].methods_by_name[
        "ReadSession"
    ]._serialized_options = b"\220\002\001"
    _globals["_STORAGECLASS"]._serialized_start = 3170
    _globals["_STORAGECLASS"]._serialized_end = 3270
    _globals["_BASINSTATE"]._serialized_start = 3272
    _globals["_BASINSTATE"]._serialized_end = 3389
    _globals["_LISTBASINSREQUEST"]._serialized_start = 69
    _globals["_LISTBASINSREQUEST"]._serialized_end = 155
    _globals["_LISTBASINSRESPONSE"]._serialized_start = 157
    _globals["_LISTBASINSRESPONSE"]._serialized_end = 234
    _globals["_CREATEBASINREQUEST"]._serialized_start = 236
    _globals["_CREATEBASINREQUEST"]._serialized_end = 359
    _globals["_CREATEBASINRESPONSE"]._serialized_start = 361
    _globals["_CREATEBASINRESPONSE"]._serialized_end = 419
    _globals["_DELETEBASINREQUEST"]._serialized_start = 421
    _globals["_DELETEBASINREQUEST"]._serialized_end = 456
    _globals["_DELETEBASINRESPONSE"]._serialized_start = 458
    _globals["_DELETEBASINRESPONSE"]._serialized_end = 479
    _globals["_GETBASINCONFIGREQUEST"]._serialized_start = 481
    _globals["_GETBASINCONFIGREQUEST"]._serialized_end = 519
    _globals["_GETBASINCONFIGRESPONSE"]._serialized_start = 521
    _globals["_GETBASINCONFIGRESPONSE"]._serialized_end = 586
    _globals["_RECONFIGUREBASINREQUEST"]._serialized_start = 588
    _globals["_RECONFIGUREBASINREQUEST"]._serialized_end = 711
    _globals["_RECONFIGUREBASINRESPONSE"]._serialized_start = 713
    _globals["_RECONFIGUREBASINRESPONSE"]._serialized_end = 780
    _globals["_STREAMINFO"]._serialized_start = 782
    _globals["_STREAMINFO"]._serialized_end = 868
    _globals["_LISTSTREAMSREQUEST"]._serialized_start = 870
    _globals["_LISTSTREAMSREQUEST"]._serialized_end = 957
    _globals["_LISTSTREAMSRESPONSE"]._serialized_start = 959
    _globals["_LISTSTREAMSRESPONSE"]._serialized_end = 1039
    _globals["_CREATESTREAMREQUEST"]._serialized_start = 1041
    _globals["_CREATESTREAMREQUEST"]._serialized_end = 1120
    _globals["_CREATESTREAMRESPONSE"]._serialized_start = 1122
    _globals["_CREATESTREAMRESPONSE"]._serialized_end = 1182
    _globals["_DELETESTREAMREQUEST"]._serialized_start = 1184
    _globals["_DELETESTREAMREQUEST"]._serialized_end = 1221
    _globals["_DELETESTREAMRESPONSE"]._serialized_start = 1223
    _globals["_DELETESTREAMRESPONSE"]._serialized_end = 1245
    _globals["_GETSTREAMCONFIGREQUEST"]._serialized_start = 1247
    _globals["_GETSTREAMCONFIGREQUEST"]._serialized_end = 1287
    _globals["_GETSTREAMCONFIGRESPONSE"]._serialized_start = 1289
    _globals["_GETSTREAMCONFIGRESPONSE"]._serialized_end = 1356
    _globals["_RECONFIGURESTREAMREQUEST"]._serialized_start = 1358
    _globals["_RECONFIGURESTREAMREQUEST"]._serialized_end = 1484
    _globals["_RECONFIGURESTREAMRESPONSE"]._serialized_start = 1486
    _globals["_RECONFIGURESTREAMRESPONSE"]._serialized_end = 1555
    _globals["_CHECKTAILREQUEST"]._serialized_start = 1557
    _globals["_CHECKTAILREQUEST"]._serialized_end = 1591
    _globals["_CHECKTAILRESPONSE"]._serialized_start = 1593
    _globals["_CHECKTAILRESPONSE"]._serialized_end = 1634
    _globals["_APPENDINPUT"]._serialized_start = 1637
    _globals["_APPENDINPUT"]._serialized_end = 1801
    _globals["_APPENDOUTPUT"]._serialized_start = 1803
    _globals["_APPENDOUTPUT"]._serialized_end = 1883
    _globals["_APPENDREQUEST"]._serialized_start = 1885
    _globals["_APPENDREQUEST"]._serialized_end = 1940
    _globals["_APPENDRESPONSE"]._serialized_start = 1942
    _globals["_APPENDRESPONSE"]._serialized_end = 2000
    _globals["_APPENDSESSIONREQUEST"]._serialized_start = 2002
    _globals["_APPENDSESSIONREQUEST"]._serialized_end = 2064
    _globals["_APPENDSESSIONRESPONSE"]._serialized_start = 2066
    _globals["_APPENDSESSIONRESPONSE"]._serialized_end = 2131
    _globals["_READOUTPUT"]._serialized_start = 2133
    _globals["_READOUTPUT"]._serialized_end = 2255
    _globals["_READREQUEST"]._serialized_start = 2257
    _globals["_READREQUEST"]._serialized_end = 2347
    _globals["_READRESPONSE"]._serialized_start = 2349
    _globals["_READRESPONSE"]._serialized_end = 2403
    _globals["_READLIMIT"]._serialized_start = 2405
    _globals["_READLIMIT"]._serialized_end = 2476
    _globals["_READSESSIONREQUEST"]._serialized_start = 2478
    _globals["_READSESSIONREQUEST"]._serialized_end = 2575
    _globals["_READSESSIONRESPONSE"]._serialized_start = 2577
    _globals["_READSESSIONRESPONSE"]._serialized_end = 2638
    _globals["_STREAMCONFIG"]._serialized_start = 2640
    _globals["_STREAMCONFIG"]._serialized_end = 2738
    _globals["_BASINCONFIG"]._serialized_start = 2740
    _globals["_BASINCONFIG"]._serialized_end = 2810
    _globals["_BASININFO"]._serialized_start = 2812
    _globals["_BASININFO"]._serialized_end = 2905
    _globals["_HEADER"]._serialized_start = 2907
    _globals["_HEADER"]._serialized_end = 2944
    _globals["_APPENDRECORD"]._serialized_start = 2946
    _globals["_APPENDRECORD"]._serialized_end = 3011
    _globals["_SEQUENCEDRECORD"]._serialized_start = 3013
    _globals["_SEQUENCEDRECORD"]._serialized_end = 3098
    _globals["_SEQUENCEDRECORDBATCH"]._serialized_start = 3100
    _globals["_SEQUENCEDRECORDBATCH"]._serialized_end = 3168
    _globals["_ACCOUNTSERVICE"]._serialized_start = 3392
    _globals["_ACCOUNTSERVICE"]._serialized_end = 3854
    _globals["_BASINSERVICE"]._serialized_start = 3857
    _globals["_BASINSERVICE"]._serialized_end = 4332
    _globals["_STREAMSERVICE"]._serialized_start = 4335
    _globals["_STREAMSERVICE"]._serialized_end = 4735
# @@protoc_insertion_point(module_scope)
