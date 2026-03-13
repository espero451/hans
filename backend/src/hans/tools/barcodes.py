def generate_zpl_label(barcode: str) -> str:
    return f"""
^XA
^FO50,30^A0N,40,40^FDHans LIMS^FS
^FO50,80^BCN,100,Y,N,N^FD{barcode}^FS
^XZ
"""
