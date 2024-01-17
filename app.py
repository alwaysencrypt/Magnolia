import os
from flask import Flask, render_template, request, send_file
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///uploads.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class File(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    path = db.Column(db.String(255), nullable=False)

# Ensure the 'uploads' directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

with app.app_context():
    # Create the database tables
    db.create_all()

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        files = request.files.getlist('fileToUpload')
        uploaded_files = []
        for file in files:
            if file:
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                # Save file information to the database
                new_file = File(filename=filename, path=file_path)
                db.session.add(new_file)
                db.session.commit()
                uploaded_files.append(new_file)

        # Cleanup process to remove entries from the database for files not found on the server
        stored_files = File.query.all()
        for file_info in stored_files:
            if not os.path.exists(file_info.path):
                db.session.delete(file_info)
                db.session.commit()

        return render_template('upload.html', uploaded_files=uploaded_files)

    uploaded_files = File.query.all()
    return render_template('upload.html', uploaded_files=uploaded_files)

@app.route('/download/<int:file_id>')
def download_file(file_id):
    file_info = File.query.get(file_id)
    if file_info:
        return send_file(file_info.path, as_attachment=True)
    else:
        return "File not found"

@app.route('/delete/<int:file_id>', methods=['POST'])
def delete_file(file_id):
    file_info = File.query.get(file_id)
    if file_info:
        # Delete the file from the filesystem
        os.remove(file_info.path)
        # Delete the file information from the database
        db.session.delete(file_info)
        db.session.commit()
        return "File deleted successfully"
    else:
        return "File not found"

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')