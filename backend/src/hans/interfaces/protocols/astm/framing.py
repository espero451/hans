from __future__ import annotations

from .constants import CR, ETB, ETX, LF, STX
from .models import AstmMessage


# --- Framing ----------------------------------------------------------

def calc_checksum(payload: bytes) -> str:
    # Calculate ASTM checksum.
    total = sum(payload) % 256
    return f"{total:02X}"


def frame_message(message: AstmMessage, frame_size: int) -> list[bytes]:
    # Frame ASTM message for transport.
    payload = message.serialize(include_trailing_record_sep=True).encode("ascii", errors="ignore")
    if not payload:
        return []

    chunks = [payload[i:i + frame_size] for i in range(0, len(payload), frame_size)]
    frames = []
    frame_no = 1
    for idx, chunk in enumerate(chunks):
        end_char = ETB if idx < len(chunks) - 1 else ETX
        frame_id = ord(str(frame_no))
        body = bytes([frame_id]) + chunk
        checksum = calc_checksum(body + bytes([end_char]))
        frame = b"".join(
            [
                bytes([STX]),
                body,
                bytes([end_char]),
                checksum.encode("ascii"),
                bytes([CR, LF]),
            ]
        )
        frames.append(frame)
        frame_no = 1 if frame_no >= 7 else frame_no + 1
    return frames
