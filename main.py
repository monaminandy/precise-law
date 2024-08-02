import flask
from flask import Flask, request, redirect, url_for, flash, get_flashed_messages
import os
from google.cloud import translate_v2 as translate
import vertexai
from vertexai.preview.generative_models import GenerativeModel, Part
import base64


try:
    import io
    from io import BytesIO
    import pandas
except Exception as e:
    print("Some Modules are missing {}". format(e))

def file_to_base64(file_path):
    # Read the file in binary mode
    with open(file_path, 'rb') as file:
        file_data = file.read()
        
    # Encode the file data to base64
    base64_encoded_data = base64.b64encode(file_data)
    
    # Convert the base64 bytes to a string
    base64_encoded_str = base64_encoded_data.decode('utf-8')
    
    return base64_encoded_str

app =flask.Flask(__name__)
app.secret_key = 'supersecretkey'  # Required for flash messages

# Configure upload folder and allowed extensions
ALLOWED_EXTENSIONS = {'pdf'}


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET','POST'])
def index():
    if 'language' in request.form:
        language = request.form['language']
    else:
        language = 'en'
    messages = get_flashed_messages()
    message = messages[0] if messages else ''
    return f'''
    <!doctype html>
    <html style="background-color:rgba(248, 202, 164, 0.589);">
    <title>Precise Law</title>
    
    <div style="">
    <div style="margin: 50px;">
    <p style="text-align:center;font-size: 35px;"> PRECISE LAW </h1>
    <p style="text-align:justify;font-size: 15px";> Precis Law is an innovative online platform designed to simplify the complex world of legal documents.
      By uploading your legal document to our user-friendly interface, you can effortlessly obtain a clear and
        concise summary in your preferred language.
    <br>
    Our advanced technology meticulously analyzes your document, extracting the essential information and 
    transforming it into an easily understandable format. Whether you're grappling with intricate legal jargon
      or simply need a quick overview of a lengthy contract, Precis Law empowers you to comprehend your legal 
      matters with ease.
    <br>
    Experience the convenience of having your legal documents translated into your native language, allowing you 
    to make informed decisions without the need for specialized legal expertise.</p>
     <p style="text-align:justify;font-size: 25px";>Steps:<br></p>
     <p style="text-align:justify;font-size: 15px";>
        1.Upload Your Legal Document. <br>
        2.Select Your Native Language.<br>
        3.Click Upload. </p>
        </div>
    <div style="display:flex;align-items=center;justify-content:center;">
    <div style="display:inline-flex;align-items:center;justify-content:center;">
        <form action="/upload" method="post" enctype="multipart/form-data">
        <p style="text-align:justify;font-size: 20px"> Upload Files In PDF Format Only </p>
            <input type="file" name="file" style="font-size:15px;">
            <br>
            <p style="text-align:justify;font-size: 20px"> Choose Your Native Language </p>
            <select name="language" style="font-size:15px;">
                <option value="en">English</option>
                <option value="es">Spanish</option>
                <option value="de">German</option>
                <option value="zh">Chinese</option>
                <option value="ja">Japanese</option>
                <option value="fr">French</option>
            </select>
            <br> <br>
            <div style="display:flex;align-items:center;justify-content:center";>
            <input type="submit" value="Upload" style="font-size:15px; ">
            </div>
        </form>
    </div>
    </div>
    <div style="margin: 50px;">
    {message}
    </div>
    </div>
    </html>
    '''

@app.route('/upload', methods=['POST'])
def upload_file():
    if flask.request.method == 'POST':
        language = flask.request.form['language']
        flask.session['language'] = language
    else:
        language = flask.session.get('language', 'en')
    if 'file' not in request.files:
        flash('No file part')
        return redirect(url_for('index'))
    file = request.files['file']
    if file.filename == '':
        flash('No selected file')
        return redirect(url_for('index'))
    #Uploading the file
    if file and allowed_file(file.filename):
        filename = file.filename
        filepath = os.path.join(filename)
        file.save(filepath)
        text = Part.from_data(mime_type= "application/pdf", data = file_to_base64(filepath))
    #Passing it through the model
        PROJECT_ID = os.environ["PROJECT_ID"]
        REGION = os.environ["REGION"]
        
        vertexai.init(project=PROJECT_ID, location=REGION)

        generative_multimodal_model = GenerativeModel("gemini-1.5-pro-001")
        response = generative_multimodal_model.generate_content(["summarise it by points", text])
        output = response.text
        translate_client = translate.Client()
        result = translate_client.translate(output, target_language = language)
        finaloutput = result['translatedText']
    #Getting the result
        flash(f'Summarised Version:"{finaloutput}"')
        return redirect(url_for('index'))
    flash('File type not allowed')
    return redirect(url_for('index'))
    

if __name__ == '__main__':
    app.run(host="0.0.0.0",port=3000)

