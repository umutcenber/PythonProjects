from PyPDF2 import PdfMerger
import os

print("=" * 40)
print("         PDF MERGER")
print("=" * 40)

merger = PdfMerger()

pdf_files = []

while True:
    file = input("Enter PDF file path (or type 'done'): ").strip()

    if file.lower() == "done":
        break

    if not os.path.exists(file):
        print("❌ File not found.")
        continue

    if not file.lower().endswith(".pdf"):
        print("❌ Please enter a PDF file.")
        continue

    pdf_files.append(file)

if len(pdf_files) < 2:
    print("❌ You need at least 2 PDF files.")
    exit()

output_name = input("Output file name (without .pdf): ").strip()

if output_name == "":
    output_name = "merged"

output_file = f"{output_name}.pdf"

counter = 1
while os.path.exists(output_file):
    output_file = f"{output_name}_{counter}.pdf"
    counter += 1

for pdf in pdf_files:
    merger.append(pdf)

merger.write(output_file)
merger.close()

print(f"\n✅ Successfully created '{output_file}'")