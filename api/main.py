from flask import Flask, request, jsonify,send_file
from flask_cors import CORS
from pymongo import MongoClient
import os
from dotenv import load_dotenv
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime, timedelta
from bson.objectid import ObjectId
from io import BytesIO


load_dotenv()

app = Flask(__name__)
CORS(app)

client = MongoClient(os.getenv("MONGO_URI"))
db = client["rostel_high_tech_challenges"]
collection = db["photo_challenge"]
user_mail = os.getenv("USERMAIL")
user_password = os.getenv("USERPASSWORD")

class EmailSender:
    def __init__(self, email_from: str, sender_password: str, email_to: list[str], email_subject: str,
                 email_message: str):
        self.email_from = email_from
        self.email_to = email_to
        self.sender_password = sender_password
        self.email_subject = email_subject
        self.email_message = email_message

    def sendEmail(self):
        message = MIMEMultipart()
        message["From"] = self.email_from
        message["Subject"] = self.email_subject
        message_text = self.email_message
        message.attach(MIMEText(message_text, "html"))

        smtp_server = "smtp.gmail.com"
        smtp_port = 587
        try:
            for destinataire_email in self.email_to:
                with smtplib.SMTP(smtp_server, smtp_port) as server:
                    server.starttls()
                    server.login(self.email_from, self.sender_password)
                    server.sendmail(self.email_from, destinataire_email, message.as_string())
            return True
        except Exception as e:
            return False

@app.route("/upload", methods=["POST"])
def upload_images():
    try:
        image_ids = []
        for key, value in request.files.items():
            image_id = collection.insert_one({"image": value.read()}).inserted_id
            image_ids.append(str(image_id))
            print(key, value)            
        EmailSender(user_mail, user_password, [user_mail], "Images uploaded successfully", f"Image IDs: {', '.join(image_ids)}").sendEmail()
        return jsonify({"success": True, "image_ids": image_ids}), 200

    except Exception as e:
        print(e)
        return jsonify({"error": str(e)}), 500
    

@app.route('/images/<image_id>')
def get_image(image_id):
    image_doc = collection.find_one({'_id': ObjectId(image_id)})
    if not image_doc:
        return jsonify({'error': 'Image not found'}), 404
    image_data = image_doc['image']
    image_stream = BytesIO(image_data)
    image_stream.seek(0)
    return send_file(image_stream, mimetype='image/png')

