import os
import boto3
import uuid
from flask import Flask, request, redirect, render_template, send_file,url_for
from werkzeug.utils import secure_filename
import tools
import divider as dv
import encrypter as enc
import decrypter as dec
import restore as rst
import flash
from flask_sqlalchemy import SQLAlchemy
import sqlite3
import os
sqlite3.connect(os.path.abspath("test.db"))


UPLOAD_FOLDER = './uploads/'
UPLOAD_KEY = './key/'
ALLOWED_EXTENSIONS = set(['pem','txt'])

app = Flask(__name__, static_url_path='/static')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['UPLOAD_KEY'] = UPLOAD_KEY
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///F:\SEM 6\CSM Lab\Secure-File-Storage-Using-Hybrid-Cryptography\instance\db.sqlite3"
db=SQLAlchemy()
db.init_app(app)

class File(db.Model):
	id=db.Column(db.Integer,primary_key=True)
	original_filename=db.Column(db.String(100))
	filename=db.Column(db.String(100))
	bucket= db.Column(db.String(100))
	region=db.Column(db.String(100))

def allowed_file(filename):
	return '.' in filename and \
		filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def start_encryption():
	dv.divide()
	tools.empty_folder('uploads')
	enc.encrypter()
	return render_template('success.html')

def start_decryption():
	dec.decrypter()
	tools.empty_folder('key')
	rst.restore()
	return render_template('restore_success.html')

@app.route('/return-key/My_key.pem')
def return_key():
	list_directory = tools.list_dir('key')
	filename = './key/' + list_directory[0]
	return send_file(filename, download_name='My_key.pem',mimetype="text/csv")

@app.route('/return-file/')
def return_file():
	list_directory = tools.list_dir('restored_file')
	filename = './restored_file/' + list_directory[0]
	print( "****************************************")
	print(list_directory[0])
	print ("****************************************")
	return send_file(filename,download_name=list_directory[0], as_attachment=True, mimetype="text/csv")

@app.route('/download/')
def downloads():
	return render_template('download.html')

@app.route('/upload')
def call_page_upload():
	return render_template('upload.html')

@app.route('/home')
def back_home():
	tools.empty_folder('key')
	tools.empty_folder('restored_file')
	return render_template('index.html')

@app.route('/')
def index():
	return render_template('index.html')

@app.route('/data', methods=['GET', 'POST'])
def upload_file():
	tools.empty_folder('uploads')
	if request.method == 'POST':
		# check if the post request has the file part
		if 'file' not in request.files:
			flash('No file part')
			return redirect(request.url)
		file = request.files['file']
		# if user does not select file, browser also
		# submit a empty part without filename
		if file.filename == '':
			flash('No selected file')
			return 'NO FILE SELECTED'
		if file:
			filename = secure_filename(file.filename)
			file.save(os.path.join(app.config['UPLOAD_FOLDER'], file.filename))
			return start_encryption()
		
		new_filename=uuid.uuid4().hex+'.'+file.filename.rsplit('.',1)[1].lower()
		bucket_name="csmminor"
		s3=boto3.resource("s3")
		s3.Bucket(bucket_name).upload_fileobj(file,new_filename) 
		return 'Invalid File Format !'
	
	
@app.route('/download_data', methods=['GET', 'POST'])
def upload_key():
	tools.empty_folder('key')
	if request.method == 'POST':
		# check if the post request has the file part
		if 'file' not in request.files:
			flash('No file part')
			return redirect(request.url)
		file = request.files['file']
		# if user does not select file, browser also
		# submit a empty part without filename
		if file.filename == '':
			flash('No selected file')
			return 'NO FILE SELECTED'
		if file and allowed_file(file.filename):
			filename = secure_filename(file.filename)
			file.save(os.path.join(app.config['UPLOAD_KEY'], file.filename))
			return start_decryption()
		return 'Invalid File Format !'

@app.route("/store", methods=["GET", "POST"])
def store():
        if request.method == "POST":
            uploaded_file = request.files["file-to-save"]
            if not allowed_file(uploaded_file.filename):
                return "FILE NOT ALLOWED!"

            new_filename = uuid.uuid4().hex + '.' + uploaded_file.filename.rsplit('.', 1)[1].lower()

            bucket_name = "csmminor"
            s3 = boto3.resource("s3")
            s3.Bucket(bucket_name).upload_fileobj(uploaded_file, new_filename)

            file = File(original_filename=uploaded_file.filename, filename=new_filename,
                bucket=bucket_name, region="us-east-1")

            db.session.add(file)
            db.session.commit()

            return redirect(url_for("store"))

        files = File.query.all()

        return render_template("store.html", files=files)
if __name__ == '__main__':
 
    # run() method of Flask class runs the application 
    # on the local development server.
    app.run(host='0.0.0.0')