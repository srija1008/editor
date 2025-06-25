from flask import Flask, request, render_template, send_file, redirect, url_for
from PIL import Image, ImageOps
from gtts import gTTS
import os
from moviepy.editor import VideoFileClip
import chardet

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
EDITED_FOLDER = 'edited'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

STATIC_UPLOADS = os.path.join('static', 'uploads')
os.makedirs(STATIC_UPLOADS, exist_ok=True)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(EDITED_FOLDER, exist_ok=True)
os.makedirs(os.path.join('static', 'tts_audio'), exist_ok=True)
STATIC_TTS = os.path.join('static', 'tts_audio')
os.makedirs(STATIC_TTS, exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/text-editor')
def text_editor():
    return render_template('text_editor.html', content=None)

@app.route('/upload-text', methods=['POST'])
def upload_text():
    file = request.files['textfile']
    raw = file.read()  # Read the file as raw bytes
    encoding = chardet.detect(raw)['encoding'] or 'utf-8'  # Detect the encoding using chardet
    try:
        text = raw.decode(encoding, errors='replace')  # Decode with detected encoding
    except UnicodeDecodeError:
        text = raw.decode('utf-8', errors='replace')  # Fallback to UTF-8 if auto-detection fails
    return render_template('text_editor.html', content=text)

@app.route('/save-text', methods=['POST'])
def save_text():
    edited_text = request.form['edited_text']
    path = os.path.join(EDITED_FOLDER, 'edited.txt')
    with open(path, 'w') as f:
        f.write(edited_text)
    return send_file(path, as_attachment=True)
@app.route('/image-editor')
def image_editor():
    return render_template('image_editor.html', image_url=None)

@app.route('/upload-image', methods=['POST'])
def upload_image():
    file = request.files['imagefile']
    filename = 'uploaded.png'
    filepath = os.path.join(STATIC_UPLOADS, filename)
    file.save(filepath)
    return render_template('image_editor.html',
                           image_url=url_for('static', filename='uploads/' + filename),
                           image_filename=filename)

@app.route('/rotate-image', methods=['POST'])
def rotate_image():
    filename = request.form['filename']
    filepath = os.path.join(STATIC_UPLOADS, filename)
    img = Image.open(filepath).rotate(90, expand=True)
    img.save(filepath)
    return render_template('image_editor.html',
                           image_url=url_for('static', filename='uploads/' + filename),
                           image_filename=filename)

@app.route('/crop-image', methods=['POST'])
def crop_image():
    filename = request.form['filename']
    filepath = os.path.join(STATIC_UPLOADS, filename)

    left = int(request.form['left'])
    top = int(request.form['top'])
    right = int(request.form['right'])
    bottom = int(request.form['bottom'])

    img = Image.open(filepath)
    cropped = img.crop((left, top, right, bottom))
    cropped.save(filepath)

    return render_template('image_editor.html',
                           image_url=url_for('static', filename='uploads/' + filename),
                           image_filename=filename)

@app.route('/resize-image', methods=['POST'])
def resize_image():
    filename = request.form['filename']
    width = int(request.form['width'])
    height = int(request.form['height'])
    filepath = os.path.join(STATIC_UPLOADS, filename)

    img = Image.open(filepath)
    resized = img.resize((width, height))
    resized.save(filepath)

    return render_template('image_editor.html',
                           image_url=url_for('static', filename='uploads/' + filename),
                           image_filename=filename)

@app.route('/grayscale-image', methods=['POST'])
def grayscale_image():
    filename = request.form['filename']
    filepath = os.path.join(STATIC_UPLOADS, filename)

    img = Image.open(filepath)
    gray = ImageOps.grayscale(img)
    gray.save(filepath)

    return render_template('image_editor.html',
                           image_url=url_for('static', filename='uploads/' + filename),
                           image_filename=filename)

@app.route('/download-image', methods=['POST'])
def download_image():
    filename = request.form['filename']
    filepath = os.path.join(STATIC_UPLOADS, filename)
    return send_file(filepath, as_attachment=True)

@app.route('/upload-video', methods=['POST'])
def upload_video():
    file = request.files['videofile']
    input_path = os.path.join(UPLOAD_FOLDER, 'input.mp4')
    output_path = os.path.join(EDITED_FOLDER, 'edited.mp4')
    file.save(input_path)
    clip = VideoFileClip(input_path).rotate(90)  # Example: rotate
    clip.write_videofile(output_path, codec='libx264', audio_codec='aac')
    return send_file(output_path, as_attachment=True)
@app.route('/video-editor')
def video_editor():
    return render_template('video_editor.html')


@app.route('/tts', methods=['GET', 'POST'])
def tts():
    audio_path = None
    if request.method == 'POST':
        text = request.form['tts_text']
        lang = request.form['lang']
        tts = gTTS(text=text, lang=lang)
        audio_filename = 'speech.mp3'
        audio_path = os.path.join('static', 'tts_audio', audio_filename)
        os.makedirs(os.path.dirname(audio_path), exist_ok=True)
        tts.save(audio_path)
        return render_template('audio_editor.html', audio_url=url_for('static', filename='tts_audio/' + audio_filename))
    return render_template('audio_editor.html', audio_url=None)
if __name__ == '__main__':
    app.run(debug=True)
