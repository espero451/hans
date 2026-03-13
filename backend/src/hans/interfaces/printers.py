import socket


def send_zpl(zpl: str, ip: str, port: int = 9100, timeout: float = 3.0) -> None:
    # Send ZPL over raw TCP to a network printer.
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(timeout)
        s.connect((ip, port))
        s.sendall(zpl.encode())
