from flask import Flask, request, render_template, send_file, redirect, url_for
from PIL import Image, ImageOps

import os
import chardet
from moviepy.video.tools.subtitles import SubtitlesClip
from moviepy.config import change_settings

from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip
change_settings({
    "IMAGEMAGICK_BINARY": "C:\\Program Files\\ImageMagick-7.1.1-Q16-HDRI\\magick.exe"
})

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
EDITED_FOLDER = 'edited'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

STATIC_UPLOADS = os.path.join('static', 'uploads')
os.makedirs(STATIC_UPLOADS, exist_ok=True)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(EDITED_FOLDER, exist_ok=True)

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

@app.route('/video-editor')
def video_editor():
    return render_template('video_editor.html',video_url=None)

@app.route('/upload-video', methods=['POST'])
def upload_video():
    file = request.files['videofile']
    filename = 'input.mp4'
    input_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(input_path)

    # Copy original for preview
    preview_path = os.path.join('static', 'uploads', filename)
    os.makedirs('static/uploads', exist_ok=True)
    file.seek(0)
    with open(preview_path, 'wb') as f:
        f.write(file.read())

    return render_template('video_editor.html',
                           video_url=url_for('static', filename='uploads/' + filename),
                           video_filename=filename)


@app.route('/rotate-video', methods=['POST'])
def rotate_video():
    filename = request.form['filename']
    input_path = os.path.join(UPLOAD_FOLDER, filename)
    output_path = os.path.join(EDITED_FOLDER, 'rotated_video.mp4')

    clip = VideoFileClip(input_path).rotate(90)
    clip.write_videofile(output_path, codec='libx264', audio_codec='aac')

    return send_file(output_path, as_attachment=True)

@app.route('/add-subtitles', methods=['POST'])
def add_subtitles():
    video_file = request.files.get('videofile')
    srt_file = request.files.get('srtfile')

    if not video_file:
        return "Please upload a video file", 400

    video_path = os.path.join(UPLOAD_FOLDER, 'input.mp4')
    output_path = os.path.join(EDITED_FOLDER, 'video_with_subs.mp4')
    video_file.save(video_path)

    video = VideoFileClip(video_path)

    # If SRT is present
    if srt_file and srt_file.filename.endswith('.srt'):
        srt_path = os.path.join(UPLOAD_FOLDER, 'subs.srt')
        srt_file.save(srt_path)

        # Detect encoding
        with open(srt_path, 'rb') as f:
            raw_data = f.read()
            encoding = chardet.detect(raw_data)['encoding']

        utf8_path = os.path.join(UPLOAD_FOLDER, 'subs_utf8.srt')
        with open(utf8_path, 'w', encoding='utf-8') as f:
            f.write(raw_data.decode(encoding))

        # Generate subtitle clip
        generator = lambda txt: TextClip(txt, fontsize=24, color='white', stroke_color='black', stroke_width=2)
        subtitles = SubtitlesClip(utf8_path, generator)

        final = CompositeVideoClip([video, subtitles.set_pos(('center', 'bottom'))])
    else:
        final = video

    static_output_path = os.path.join('static', 'edited', 'video_with_subs.mp4')
    final.write_videofile(static_output_path, codec='libx264', audio_codec='aac')
    return render_template('video_editor.html', video_url=url_for('static', filename='edited/video_with_subs.mp4'))

@app.route('/download-video', methods=['POST'])
def download_video():
    filename = request.form['filename']
    path = os.path.join(UPLOAD_FOLDER, filename)
    return send_file(path, as_attachment=True)

if __name__=="__main__":
    app.run(debug=True)
    
