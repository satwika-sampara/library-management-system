import pandas as pd
import qrcode

def generate_qr_codes(input_csv, output_folder):
    # Read the CSV file
    df = pd.read_csv(input_csv)

    # Iterate over each row in the DataFrame
    for index, row in df.iterrows():
        # Extract data from the row
        name = row['Name']
        roll = row['Roll']

        # Combine data into a single string
        qr_data = f"{name} {roll}"

        # Generate QR code
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(qr_data)
        qr.make(fit=True)

        # Create an image from the QR code
        qr_img = qr.make_image(fill_color="black", back_color="white")

        # Save the QR code image
        output_file = f"{output_folder}/qr_{index}.png"
        qr_img.save(output_file)

        print(f"QR code generated for {name} with roll number {roll}. Saved as {output_file}")

# Example usage
generate_qr_codes('names.csv', 'qr_codes')
