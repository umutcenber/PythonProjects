from PIL import Image
import os

print("=" * 40)
print("       IMAGE RESIZER")
print("=" * 40)

image_path = input("Enter image path: ").strip()

if not os.path.exists(image_path):
    print("❌ Image not found.")
    exit()

try:
    width = int(input("New width: "))
    height = int(input("New height: "))
except ValueError:
    print("❌ Width and height must be numbers.")
    exit()

try:
    image = Image.open(image_path)

    resized = image.resize((width, height))

    filename, extension = os.path.splitext(image_path)

    output = f"{filename}_resized{extension}"

    resized.save(output)

    print(f"\n✅ Image saved as:\n{output}")

except Exception as e:
    print(f"❌ Error: {e}")