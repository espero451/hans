import socket
import time

HOST = "127.0.0.1"
PORT = 5100

ENQ = b"\x05"
ACK = b"\x06"
EOT = b"\x04"
STX = b"\x02"
ETX = b"\x03"
CR = b"\r"
LF = b"\n"

def recv_byte(sock):
    return sock.recv(1)

def send_ack(sock):
    sock.sendall(ACK)

# ASTM message body
msg = "H|\\^&||||||||||P|1\rQ|1|000000000002\rL|1|N\r"  # Q3: barcode
frame_body = b"1" + msg.encode("ascii")
frame = STX + frame_body + ETX + b"00" + CR + LF  # checksum 00, validation off

s = socket.create_connection((HOST, PORT))
s.sendall(ENQ)
print("ENQ ->", recv_byte(s))

s.sendall(frame)
print("FRAME ->", recv_byte(s))

s.sendall(EOT)

# read response
data = b""
while True:
    b = recv_byte(s)
    if not b:
        break
    if b == ENQ:
        send_ack(s)
        continue
    if b == STX:
        chunk = b""
        while True:
            c = recv_byte(s)
            chunk += c
            if chunk.endswith(CR + LF):
                break
        send_ack(s)
        data += b + chunk
        continue
    if b == EOT:
        break

print(data.decode("ascii", errors="ignore").replace("\r", "\\r"))
s.close()
