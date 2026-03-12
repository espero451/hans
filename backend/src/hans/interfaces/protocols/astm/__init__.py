from __future__ import annotations

from .codec import (
    _extract_barcode,
    _first_nonempty,
    _parse_result_datetime,
    _resolve_delimiters_from_lines,
    _split_records,
    classify_records,
    invalid_reason,
    parse_message,
    resolve_delimiters,
)
from .constants import (
    ACK,
    ASTM_MAPPING_KEY,
    CONTROL_CHARS,
    CR,
    ENQ,
    EOT,
    ETB,
    ETX,
    LF,
    NAK,
    R_COMPLETED_FIELDS,
    R_FLAGS_FIELD,
    R_STATUS_FIELD,
    R_TEST_CODE_FIELD,
    R_UNITS_FIELD,
    R_VALUE_FIELD,
    STX,
)
from .framing import calc_checksum, frame_message
from .mapping import (
    AstmMapping,
    AstmOrderInMapping,
    AstmOrderOutMapping,
    AstmPatientMapping,
    AstmQueryMapping,
    AstmResultMapping,
    astm_mapping,
    resolve_join_separator,
)
from .models import (
    AstmDelimiters,
    AstmMessage,
    AstmRecord,
    QueryResponseContext,
    ResultPayload,
)
from .query import (
    build_patient_record,
    build_query_response,
    extract_query_barcodes,
    query_response_contexts,
    split_patient_name,
)
from .results import parse_results, result_payload_as_dom
from .session import AstmDispatcher, AstmSession, DomainMessageRouter, HandleResult, handle_astm_message
from .utils import format_csv, format_peer, optional_str

# Backward-compatible aliases for old private names.
_astm_mapping = astm_mapping
_resolve_join_separator = resolve_join_separator
_split_patient_name = split_patient_name
_build_patient_record = build_patient_record
_query_response_contexts = query_response_contexts
_result_payload_as_dom = result_payload_as_dom
_format_peer = format_peer
_format_csv = format_csv
_optional_str = optional_str
