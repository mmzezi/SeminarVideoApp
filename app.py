from flask import Flask, request, send_file, render_template, jsonify, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from datetime import datetime
import os
import subprocess
import time
import shutil
import yt_dlp


app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads/'
app.config['PROCESSED_FOLDER'] = 'processed/'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///videos.db'
db = SQLAlchemy(app)

## TABELE
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    videos = db.relationship('Video', backref='user', lazy=True)

class Video(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(150), nullable=False)
    processed_filename = db.Column(db.String(150), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class VideoLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False)
    video_url = db.Column(db.String(255), nullable=False)
    format_type = db.Column(db.String(20), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<VideoLog {self.username} - {self.video_url}>'

with app.app_context():
    db.create_all()

app.secret_key = 'e62e7f0b8b3b9c1929af1298d3ec4a77a4d874a032d814b1ec6b8132039dfd7a'  #SPREMENI PRED ODDAJO

@app.route('/set_username', methods=['POST'])
def set_username():
    username = request.form.get('username')  # Get the username from the form
    if not username:
        return jsonify({'error': 'Username is required'}), 400

    user = User.query.filter_by(username=username).first()
    if not user:
        user = User(username=username)
        db.session.add(user)
        db.session.commit()

    session['username'] = username
    return redirect(url_for('index'))  # Redirect to index after setting username


def get_current_user():
    username = session.get('username')
    if not username:
        return None
    return User.query.filter_by(username=username).first()

def generate_unique_filename(filename, prefix):
    base, ext = os.path.splitext(filename)
    timestamp = int(time.time())
    return f"{prefix}_{base}_{timestamp}{ext}"

def convert_video(input_path, output_path, codec):
    command = ['ffmpeg', '-i', input_path, '-c:v', codec, output_path]
    subprocess.run(command, check=True)

def change_resolution(input_path, output_path, resolution):
    command = ['ffmpeg', '-i', input_path, '-vf', f'scale={resolution}', output_path]
    subprocess.run(command, check=True)

def boost_audio(input_path, output_path, volume):
    command = ['ffmpeg', '-i', input_path, '-filter:a', f'volume={volume}dB', output_path]
    subprocess.run(command, check=True)

@app.route('/')
def index():
    username = session.get('username')
    if not username:
        return redirect(url_for('login'))  # Redirect to login if no username is found
    return render_template('index.html', username=username)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        if username:
            session['username'] = username
            return redirect(url_for('index'))  # Redirect to the main page after login
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)  # Remove username from session
    return redirect(url_for('login'))

@app.route('/upload', methods=['POST'])
def upload_file():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'You must set a username first.'}), 403

    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    # Check for duplicates
    existing_video = Video.query.filter_by(filename=filename, user_id=user.id).first()
    if existing_video:
        return jsonify({'error': 'Duplicate video detected. This video is already uploaded.'}), 400

    video = Video(filename=filename, user_id=user.id)
    db.session.add(video)
    db.session.commit()
    return jsonify({'video_id': video.id}), 200


@app.route('/process/<int:video_id>', methods=['POST'])
def process_video(video_id):
    video = Video.query.get(video_id)
    if not video:
        return jsonify({'error': 'Video not found'}), 404
    input_path = os.path.join(app.config['UPLOAD_FOLDER'], video.filename)

    # Generate unique filenames for temporary, processed, and final processed videos
    temp_filename = generate_unique_filename(video.filename, "temp")
    temp_path = os.path.join(app.config['PROCESSED_FOLDER'], temp_filename)
    processed_filename = generate_unique_filename(video.filename, "processed")
    processed_path = os.path.join(app.config['PROCESSED_FOLDER'], processed_filename)
    final_processed_filename = generate_unique_filename(video.filename, "final_processed")
    final_processed_path = os.path.join(app.config['PROCESSED_FOLDER'], final_processed_filename)

    data = request.json
    codec = data.get('codec', 'libx265')
    resolution = data.get('resolution', '-2:480')
    volume = data.get('volume', '5')
    bitrate = data.get('bitrate', '1000')
    crf = data.get('crf', '28')  # Default CRF value
    strip_metadata = data.get('strip_metadata', False)

    # Temporary processing step to avoid in-place editing
    change_resolution(input_path, temp_path, resolution)
    convert_video(temp_path, processed_path, codec)

    # Apply audio boost to the processed video
    boost_audio(processed_path, final_processed_path, volume)

    # Generate a new unique filename for the final encoded video
    final_encoded_filename = generate_unique_filename(video.filename, "final_encoded")
    final_encoded_path = os.path.join(app.config['PROCESSED_FOLDER'], final_encoded_filename)

    # Encode the processed video to the selected bitrate and apply CRF
    command = ['ffmpeg', '-i', final_processed_path, '-c:v', codec, '-b:v', f'{bitrate}k', '-crf', crf, final_encoded_path]

    # Optionally strip metadata
    if strip_metadata:
        command.extend(['-map_metadata', '-1'])

    subprocess.run(command, check=True)

    video.processed_filename = final_encoded_filename
    db.session.commit()
    return jsonify({'processed_filename': final_encoded_filename}), 200


@app.route('/download/<int:video_id>', methods=['GET'])
def download_file(video_id):
    video = Video.query.get(video_id)
    if not video or not video.processed_filename:
        return jsonify({'error': 'Processed video not found'}), 404
    filepath = os.path.join(app.config['PROCESSED_FOLDER'], video.processed_filename)
    response = send_file(filepath, as_attachment=True)
    # Delete upload and processed folders after download
    os.remove(filepath)  # Remove only the downloaded file instead of deleting the entire folder
    return response


@app.route('/youtube_download', methods=['POST'])
def youtube_download():
    data = request.get_json()
    url = data.get('url')
    format_type = data.get('format', 'video')  # 'video' or 'audio'

    if not url:
        return jsonify({'message': 'URL is required'}), 400

    # Ensure the username is in the session
    username = session.get('username')
    if not username:
        return jsonify({'message': 'Username required'}), 400

    # Log the username with the download action
    print(f"User '{username}' is downloading a video from {url} as {format_type}")

    # Create a temporary directory to save the file
    temp_folder = 'temp_downloads'
    os.makedirs(temp_folder, exist_ok=True)

    # Set the download options based on the requested format
    if format_type == 'audio':
        ydl_opts = {
            'outtmpl': f'{temp_folder}/%(title)s.%(ext)s',
            'format': 'bestaudio',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
            }],
            'noplaylist': True,  # Disable playlist download
            'quiet': False,  # Enable output for debugging
        }
    else:
        ydl_opts = {
            'outtmpl': f'{temp_folder}/%(title)s.%(ext)s',
            'format': 'bestvideo+bestaudio',
            'noplaylist': True,  # Disable playlist download
            'quiet': False,  # Enable output for debugging
            'merge_output_format': 'mp4',  # Ensure video/audio merge as mp4
        }

    try:
        # Run yt-dlp with the provided URL and format
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

            # If audio, adjust file extension
            if format_type == 'audio':
                filename = filename.rsplit('.', 1)[0] + '.mp3'

        # Log the download success with the username
        print(f"User '{username}' completed the download for {url}")

        # Return the download link
        download_link = f'/download_temp/{os.path.basename(filename)}'
        return jsonify({'message': 'Download ready', 'download_link': download_link}), 200

    except yt_dlp.utils.DownloadError as e:
        # Catch yt-dlp specific errors
        return jsonify({'message': 'Failed to download video', 'error': str(e)}), 500
    except Exception as e:
        # Catch all other exceptions
        return jsonify({'message': 'An unexpected error occurred', 'error': str(e)}), 500
    
@app.route('/download_temp/<filename>', methods=['GET'])
def download_temp(filename):
    temp_folder = 'temp_downloads'
    filepath = os.path.join(temp_folder, filename)

    if not os.path.exists(filepath):
        return jsonify({'message': 'File not found'}), 404

    return send_file(filepath, as_attachment=True)

@app.route('/cleanup_temp', methods=['POST'])
def cleanup_temp():
    temp_folder = 'temp_downloads'
    if os.path.exists(temp_folder):
        shutil.rmtree(temp_folder)
        os.makedirs(temp_folder)
    return jsonify({'message': 'Temporary files cleaned up'}), 200


if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['PROCESSED_FOLDER'], exist_ok=True)
    app.run(debug=True)
