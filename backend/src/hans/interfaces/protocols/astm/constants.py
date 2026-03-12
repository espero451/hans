from __future__ import annotations


STX = 0x02
ETX = 0x03
EOT = 0x04
ENQ = 0x05
ACK = 0x06
NAK = 0x15
ETB = 0x17
CR = 0x0D
LF = 0x0A


CONTROL_CHARS = {chr(STX), chr(ETX), chr(EOT), chr(ETB)}

R_TEST_CODE_FIELD = 2
R_VALUE_FIELD = 3
R_UNITS_FIELD = 4
R_FLAGS_FIELD = 6
R_STATUS_FIELD = 8
R_COMPLETED_FIELDS = (9, 10, 12)

# Key used to store mapping in config translation.
ASTM_MAPPING_KEY = "_astm_mapping"
