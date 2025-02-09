#!/usr/bin/env python
import os

from flask import (
    Flask,
    render_template,
    send_from_directory,
    url_for,
    request,
    jsonify,
    send_file
)
import markdown
from utils.utils import get_image

app = Flask(__name__)

FOLDER = os.path.join('lectures')
THUMBNAILS = os.path.join('static', 'thumbnails')

app.config['UPLOAD_FOLDER'] = FOLDER
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 60

extensions = ('.pdf', '.md')

if not os.path.exists(FOLDER):
    os.makedirs(FOLDER)

if not os.path.exists(THUMBNAILS):
    os.makedirs(THUMBNAILS, exist_ok=True)


@app.route('/')
def index():
    files = [f for f in os.listdir(FOLDER) if f.endswith(extensions)]
    return render_template('index.html', files=files)


@app.route('/thumbnail/<filename>')
def get_thumbnail(filename):
    image_path = os.path.join(THUMBNAILS, filename)
    if not os.path.exists(image_path):
        get_image(filename.replace('.png', '.pdf'), FOLDER, THUMBNAILS, 1)
    return send_file(image_path, mimetype="image/png")


@app.route('/file/<filename>')
def serve_file(filename):
    return send_from_directory(FOLDER, filename)


@app.route('/view_pdf/<filename>')
def view_pdf(filename):
    if filename.endswith('.pdf'):
        page = request.args.get('page', default=1, type=int)
        return render_template(
            'view_pdf.html',
            pdf_url=url_for(
                'serve_file',
                filename=filename),
            page=page)
    return "File not found", 404


@app.route('/view_md/<filename>')
def view_md(filename):
    if filename.endswith('.md'):
        with open(os.path.join(FOLDER, filename), "r", encoding="utf-8") as f:
            md_content = f.read()

        return render_template(
            'view_md.html',
            md_url=url_for('serve_file', filename=filename),
            content=markdown.markdown(
                md_content,
                extensions=['fenced_code', 'tables'],
                output_format="html5"))
    return "File not found", 404


@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'success': False,
                        'message': 'File not found.'}), 400

    file = request.files['file']

    if not file.filename:
        return jsonify({'success': False,
                        'message': 'Invalid file name.'}), 400

    if file.filename.endswith(extensions):
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(file_path)
        get_image(file.filename, FOLDER, THUMBNAILS, 1)
        return jsonify({'success': True,
                        'message': 'File uploaded successfully.',
                        'path': file_path}), 201

    return jsonify({'success': False,
                    'message': 'Only PDF files are allowed.'}), 415


if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=True)
