from flask import Flask, render_template, request, send_file
import os
import yt_dlp as youtube_dl
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Temporary download path (set a specific folder for saving)
TEMP_DOWNLOAD_PATH = os.path.join(os.getcwd(), "downloads")

# Ensure download path exists
if not os.path.exists(TEMP_DOWNLOAD_PATH):
    os.makedirs(TEMP_DOWNLOAD_PATH)

# Path to your exported cookies file
COOKIES_FILE_PATH = os.path.join(os.getcwd(), "cookies", "cookies.txt")  # Adjust path  # Replace with the actual path to your cookies file

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download', methods=['POST'])
def download():
    video_url = request.form['url']
    file_type = request.form['file_type']
    
    # Set download folder (for temporary saving)
    download_folder = TEMP_DOWNLOAD_PATH
    
    # Download options for yt-dlp
    ydl_opts = {
        'outtmpl': os.path.join(download_folder, '%(title)s.%(ext)s'),
        'cookies': COOKIES_FILE_PATH,  # Adding cookies to yt-dlp options
    }

    if file_type == 'audio':
        audio_quality = request.form['audio_quality']
        ydl_opts.update({
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': audio_quality.split("k")[0],
            }]
        })
    elif file_type == 'video':
        video_quality = request.form['video_quality']
        ydl_opts.update({
            'format': f'bestvideo[height<={video_quality.split("p")[0]}]+bestaudio/best',
        })

    # Download the video/audio
    try:
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])

        # Get the latest file from the download folder
        downloaded_files = os.listdir(download_folder)
        downloaded_file = max(downloaded_files, key=lambda f: os.path.getctime(os.path.join(download_folder, f)))
        
        # Send the downloaded file
        return send_file(os.path.join(download_folder, downloaded_file), as_attachment=True)
        
    except Exception as e:
        return f"Error downloading video: {e}"

if __name__ == '__main__':
    app.run(debug=True)
