import qrcode

print("=" * 40)
print("      QR CODE GENERATOR")
print("=" * 40)

data = input("Enter a URL or text: ").strip()

filename = input("Enter file name (without .png): ").strip()

if filename == "":
    filename = "qrcode"

qr = qrcode.QRCode(
    version=1,
    error_correction=qrcode.constants.ERROR_CORRECT_M,
    box_size=10,
    border=4
)

qr.add_data(data)
qr.make(fit=True)

image = qr.make_image(fill_color="black", back_color="white")

image.save(f"{filename}.png")

print(f"\n✅ QR Code saved as '{filename}.png'")