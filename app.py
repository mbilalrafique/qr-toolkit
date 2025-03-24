from flask import Flask, render_template, request, flash
import cv2
import numpy as np
from pyzbar.pyzbar import decode
from werkzeug.utils import secure_filename
import os
from PIL import Image
import validators

app = Flask(__name__)

# Security Configurations
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB file size limit
app.secret_key = "supersecretkey"

# Ensure upload folder exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

def allowed_file(filename):
    """Check if uploaded file has a valid image extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def is_valid_image(file_path):
    """Check if the file is a real image using PIL."""
    try:
        img = Image.open(file_path)  # Try to open as an image
        img.verify()  # Verify it's an actual image
        return True
    except Exception:
        return False

def scan_qr_code(image_path):
    """Scan QR code from an image and return the content."""
    try:
        img = cv2.imread(image_path)
        qr_codes = decode(img)
        qr_texts = [qr.data.decode('utf-8') for qr in qr_codes if qr.data]

        if not qr_texts:
            return None, "🛑 No QR code detected. Please try another image."

        qr_content = qr_texts[0]  # Use the first detected QR code

        # Validate if QR content is a URL
        if validators.url(qr_content):
            return qr_content, None
        else:
            return None, "⚠️ The QR code content is not a valid URL."

    except Exception as e:
        print("Error scanning image:", e)
        return None, "🚫 Error processing image. Please try again with a valid QR image."

@app.route("/", methods=["GET", "POST"])
def home():
    qr_text = None  
    error_message = None

    if request.method == "POST":
        if "file" not in request.files:
            flash("No file uploaded! Please select an image.", "error")
            return render_template("index.html")

        file = request.files["file"]

        if file.filename == "":
            flash("No file selected. Please upload an image.", "error")
            return render_template("index.html")

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(file_path)

            # Check if it's a real image
            if not is_valid_image(file_path):
                os.remove(file_path)  # Delete invalid file
                flash("🚫 Invalid image file! Please upload a valid PNG, JPG, or GIF.", "error")
                return render_template("index.html")

            # Scan QR code
            qr_text, error_message = scan_qr_code(file_path)

            # Delete the file immediately after processing
            os.remove(file_path)

            if error_message:
                flash(error_message, "warning")
        
        else:
            flash("🚫 Invalid file type! Only PNG, JPG, or GIF images are allowed.", "error")

    return render_template("index.html", qr_text=qr_text)

if __name__ == "__main__":
    app.run(debug=True)
