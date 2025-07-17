
import cv2
import csv
import time
import numpy as np
import pandas as pd
from QR_Generator import QR_GEN, ZBarSymbol
from flask import Flask, render_template, Response, request
import datetime
import pyzbar as pyzbar
from pyzbar.pyzbar import decode
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import pyzbar.pyzbar as pyzbar
import pyzbar.pyzbar
import datetime
import json
#from datetime import datetime
FINE_RATE_PER_DAY = 100
app = Flask(__name__)

def FPS(img, fps, latency):
	cv2.putText(img, f"FPS: {str(int(fps))}", org=(7, 25), fontFace=cv2.FONT_HERSHEY_PLAIN,
				fontScale=1, color=(0, 0, 0), thickness=1)

	cv2.putText(img, f"Latency: {str(latency)}s", org=(97, 25), fontFace=cv2.FONT_HERSHEY_PLAIN,
				fontScale=1, color=(0, 0, 0), thickness=1)

	return img

def gen_frames_attendance():
	pTime, pTimeL = 0, 0
	previous = time.time()
	delta = 0
	message = ""
	a = 0

	gen = QR_GEN("names.csv")
	#url = "http://192.168.0.110:8080/video"

	cap = cv2.VideoCapture(0)
	cap.set(10, 150)

	while True:
		_, img = cap.read()
		# img = cv2.flip(img, 1)

		img = cv2.resize(img, (640, 480))
		gen.qr_check_attendance(img)

		decrypt = decode(img, symbols=[ZBarSymbol.QRCODE])
		if decrypt:
			polygon_cords = decrypt[0].polygon
			img = gen.plot_polygon(img, polygon_cords)

		# # FPS
		cTimeL = time.time()

		cTime = time.time()
		if (cTime - pTime) != 0:
			fps = 1 / (cTime - pTime)
			latency = np.round((cTimeL - pTimeL), 4)
			pTime, pTimeL = cTime, cTimeL
			a += 1
			img = FPS(img, fps, latency)

		# Video stream
		ret, buffer = cv2.imencode('.jpg', img)
		img = buffer.tobytes()
		yield (b'--frame\r\n'
			   b'Content-Type: image/jpeg\r\n\r\n' + img + b'\r\n')

def change_type(sub):
	"""
	Makes each element of list or array change to string
	:param sub: list or any array
	:return: string type of all elements
	"""

	if isinstance(sub, list):
		return [change_type(ele) for ele in sub]
	elif isinstance(sub, tuple):
		return tuple(change_type(ele) for ele in sub)
	else:
		return str(sub)

def calculate_fine(return_date):
    """
    Calculate the fine based on the difference between return_date and current date.
    """
    #global return_date
    current_date = datetime.datetime.now()
    #print("##################" + return_date + "#################")
    #return_date = datetime.datetime.strptime(return_date, "%Y-%m-%d").date()
    
    if current_date > return_date:
        days_overdue = (current_date - return_date).days
        fine_amount = days_overdue * FINE_RATE_PER_DAY
        return fine_amount
    else:
        return 0
	
def send_email_alert(fine,name,date_string):
    # Email configuration
    sender_email = "satwikaece@gmail.com"  # Replace with your email address
    receiver_email = ["satwika444@gmail.com","satwikaece@gmail.com"]  # Replace with the recipient's email address
    password = "dfzg rjmr wttl xpox"  # Replace with your email password

    # Create message container
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = ", ".join(receiver_email)
    msg['Subject'] = "Library Alert"
    #global scanned_name
   
    if fine>0:
      body = f"Mr/Ms.{name}, Please note that a fine of Rs. {fine} has been accrued for late book return."
    elif  datetime.datetime.now().strftime("%Y-%m-%d") < date_string.strftime("%Y-%m-%d"):
      body = f" Mr/Ms.{name}, It is a gentle remainder of returning a book on {date_string}."
    elif  datetime.datetime.now().strftime("%Y-%m-%d") == date_string.strftime("%Y-%m-%d"):
      body = f" Mr/Ms.{name}, A book is due for return today! if you already submitted the book please ignore.!"
    else:
          body=f" Mr/Ms.{name}, a book has been issued today the return date is {date_string}!"
    # Add message body  
      
         
    msg.attach(MIMEText(body, 'plain'))
    server = smtplib.SMTP('smtp.gmail.com', 587) # Connect to SMTP server
    server.starttls()
    server.login(sender_email, password) # Login to email account
    text = msg.as_string()# Send email
    server.sendmail(sender_email, receiver_email, text)
    server.quit()# Close SMTP server connection
    return "sending email alert!" 

return_date = ""  # Initialize return_date variable

@app.route('/set_return_date', methods=['POST'])
#return_date = request.form['return_date']
def set_return_date():
    global return_date
    return_date = request.form['return_date']
    current_date = datetime.datetime.now().strftime("%Y-%m-%d")   
    global scanned_name
    global scanned_roll
    global  book
    global  isbn
    updated_rows = []
    submitted_date = ""
    updated_data = []
    return_date = datetime.datetime.strptime(return_date, "%Y-%m-%d")
    fine = calculate_fine(return_date)
    count = 0
    with open('qr_data_record.csv', 'r', newline='') as csvfile:
        # Create a CSV reader
        reader = csv.DictReader(csvfile)
        print(reader)
        for row in reader:
            print("looping through the reader")
            if row['Student Name'] == scanned_name and row['ISBN No'] == isbn:
                print("updating the submitted data")
                count += 1
                if row['Submitted Date'] != "":
                    row['Submitted Date'] = ""
                    row['Return Date'] = return_date
                else:
                    row['Submitted Date'] = current_date
            
            if row['Submitted Date'] == "" and row['Update Date'] != current_date:
                print("book is not yet submitted")
                r_d = row['Return Date'] 
                if isinstance(r_d, datetime.datetime):
                  r_d_str = r_d.strftime('%Y-%m-%d %H:%M:%S')
                  date_string, time_string = r_d_str.split(" ")
                else:
                  date_time = datetime.datetime.strptime(r_d, '%Y-%m-%d %H:%M:%S')
                  date_string = date_time.strftime('%Y-%m-%d')
                  time_string = date_time.strftime('%H:%M:%S')
                date_string = datetime.datetime.strptime(date_string, "%Y-%m-%d")
                if date_string - datetime.timedelta(days=2) <= datetime.datetime.now():
                    print("sending email alert")
                    row['Update Date'] = current_date
                    fine = calculate_fine(date_string)
                    row['Fine'] = fine
                    updated_data.append(row)
                    send_email_alert(fine,row['Student Name'] , date_string )
                    time.sleep(1)
                    print("return date is less than current date ") 
                else:
                    print("return date is greater than current date ")
           
            print("adding same data")
            updated_rows.append(row)
        
        if count == 0:
            updated_rows.append({'Student Name': scanned_name, 'R.No': scanned_roll, 'ISBN No': isbn, 'Book Name': book, 'In Date': current_date, 'Return Date': return_date, 'Submitted Date': submitted_date, 'Fine': fine , 'Update Date' : current_date})
            send_email_alert(fine,scanned_name,return_date )

    with open('qr_data_record.csv', 'w', newline='') as csvfile:
        fieldnames = ['Student Name', 'R.No', 'ISBN No', 'Book Name', 'In Date', 'Return Date', 'Submitted Date', 'Fine', 'Update Date']  # Update fieldnames if necessary
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()  # Write the header row
        writer.writerows(updated_rows)  # Write the updated rows
    
    return "Thankyou!"
               
def gen_frames_library():
    
    processed_qr_codes = []  # List to store processed QR codes
    qr_data1 = ""
    qr_data2 = ""

    pTime, pTimeL = 0, 0

    cap = cv2.VideoCapture(0)
    cap.set(10, 150)

    while True:   # Start an infinite loop to continuously read frames from the camera
 
        _, img = cap.read()  # Read a frame from the camera and store it in the 'img' variable

        img = cv2.resize(img, (640, 480)) # Resize the captured frame to a fixed size of 640x480 pixels


        decodedObjects = pyzbar.pyzbar.decode(img)   # Detect and decode any QR codes present in the current frame

        for obj in decodedObjects:   # Iterate through the detected objects
            print (obj)
            if obj.type == "QRCODE":  # Check if the detected object is a QR code
                print ("obj type is qr code")
                qr_data = obj.data.decode('utf-8')  # Extract the data from the QR code
                print('Data : ', qr_data, '\n')       # Display the scanned data on the frame            
                cv2.putText(img, f'{qr_data}', (50, 50),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)
				
                if qr_data in processed_qr_codes:  # Check if QR code already processed
                    continue  # Skip if QR code already processed
                else:
                    processed_qr_codes.append(qr_data)  # Add QR code to processed list
					
                if qr_data1 == "":   # If qr_data1 is empty, store the current QR code data in it
                    qr_data1 = qr_data  
                else:
                    qr_data2 = qr_data    # If qr_data1 is not empty, store the current QR code data in qr_data2

        if qr_data1 != "" and qr_data2 != "":
            # Process both QR codes and append data as a single record
            global scanned_name
            global scanned_roll
            global  book
            global  isbn
			
            scanned_name, scanned_roll = qr_data1.split(" ")
            isbn,book = qr_data2.split(" ") 
            # Get current date
            
            
            # Calculate return date (example: 7 days from the current date)
            #return_date = (datetime.datetime.now() + datetime.timedelta(days=7)).strftime("%d-%m-%Y")
						
            #global return_date
            
			

            # Append data to CSV file
            

            qr_data1 = ""
            qr_data2 = ""
            print(return_date)
            # return_date=set_return_date 
			# Check if return date matches current date for alert
            #return_date=datetime.datetime.strptime(return_date, "%d-%m-%Y")
            print ("comparing return date with current date")
            #if return_date <= datetime.datetime.now().strftime("%d-%m-%Y"):
            
        cTimeL = time.time()

        cTime = time.time()
        if (cTime - pTime) != 0:
            fps = 1 / (cTime - pTime)
            pTime, pTimeL = cTime, cTimeL

        ret, buffer = cv2.imencode('.jpg', img)
        img = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + img + b'\r\n')

@app.route('/')
def index():
	return render_template('index.html')

@app.route('/attendance')
def attendance():
	return render_template('attendance.html')

@app.route('/library')
def library():
	return render_template('library.html')



@app.route('/data_attendance', methods=['GET', 'POST'])
def data_attendance():
	f = "attendance.csv"
	data = []
	with open(f) as file:
		csvfile = csv.reader(file)
		for row in csvfile:
			data.append(row)

	data = pd.DataFrame(data)
	return render_template('data.html', data=data.to_html(classes='mystyle', header=False, index=False))

@app.route('/data_library', methods=['GET', 'POST'])
def data_library():
	f = "qr_data_record.csv"
	data = []
	with open(f) as file:
		csvfile = csv.reader(file)
		for row in csvfile:
			data.append(row)

	data = pd.DataFrame(data)
	return render_template('data.html', data=data.to_html(classes='mystyle', header=False, index=False))

@app.route('/video_feed_attendance')
def video_feed():
	return Response(gen_frames_attendance(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/video_feed_library')
def video_feed_library():
	return Response(gen_frames_library(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == "__main__":
	app.run(debug=True)