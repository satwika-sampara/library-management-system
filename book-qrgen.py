import os
import qrcode
import pandas as pd

# Create directory to save QR code images if it doesn't exist
if not os.path.exists("qrcodes-books"):
    os.makedirs("qrcodes-books")

# Example book data
books = [
    {"ISBN": "9780070077850", "Book": "satellite communication"},
    {"ISBN": "9789339219505", "Book": "electronic devices and circuits"},
    {"ISBN": "9788120327726", "Book": "vlsi"},
    {"ISBN": "9778131714508", "Book": "digital design"},
    {"ISBN": "9788183710817", "Book": "digital signal processing"},
    # Add more books as needed
]
# Generate QR codes for each book
for book in books:
    qr_data = f"{book['ISBN']} {book['Book']}"
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
    qr.add_data(qr_data)
    qr.make(fit=True)

    # Save QR code as an image file
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(f"qrcodes-books/{book['ISBN']}.png")  # Save QR code image with ISBN as filename

# Create a DataFrame for book records
df = pd.DataFrame(books)

# Save book records to a CSV file
df.to_csv('bookrecord.csv', index=False)
