import qrcode
import base64
import secrets


secret = base64.b32encode(secrets.token_bytes(32)).decode("ascii")
uri = f"otpauth://totp/d-point?secret={secret}&issuer=d-point&algorithm=SHA256"
qr = qrcode.QRCode(border=4)
qr.add_data(uri)
qr.make()
qr.print_ascii(invert=True)
print(f"Base32 encoded secret: {secret}")
