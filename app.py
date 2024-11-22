from flask import Flask, render_template, request, send_file
import os
import yt_dlp as youtube_dl
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
import time
import json

app = Flask(__name__)

# Temporary paths
TEMP_DOWNLOAD_PATH = os.path.join(os.getcwd(), "downloads")
if not os.path.exists(TEMP_DOWNLOAD_PATH):
    os.makedirs(TEMP_DOWNLOAD_PATH)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download', methods=['POST'])
def download():
    video_url = request.form['url']
    file_type = request.form['file_type']

    # Get cookies using Selenium
    cookies_path = os.path.join(os.getcwd(), "cookies.txt")
    get_youtube_cookies(cookies_path)

    # yt-dlp options
    ydl_opts = {
        'outtmpl': os.path.join(TEMP_DOWNLOAD_PATH, '%(title)s.%(ext)s'),
        'quiet': True,
        'cookies': cookies_path,  # Automatically use cookies fetched by Selenium
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

    try:
        # Download the video/audio
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])

        # Find the most recent file in the download folder
        downloaded_files = os.listdir(TEMP_DOWNLOAD_PATH)
        downloaded_file = max(downloaded_files, key=lambda f: os.path.getctime(os.path.join(TEMP_DOWNLOAD_PATH, f)))
        file_path = os.path.join(TEMP_DOWNLOAD_PATH, downloaded_file)

        return send_file(file_path, as_attachment=True)

    except Exception as e:
        return f"Error downloading video: {str(e)}"

def get_youtube_cookies(output_path):
    """
    Use Selenium to log in and fetch YouTube cookies.
    """
    # Configure Selenium
    options = Options()
    options.add_argument("--headless")  # Run browser in headless mode
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    try:
        # Open YouTube
        driver.get("https://www.youtube.com")
        time.sleep(5)  # Wait for the page to load completely

        # Export cookies
        cookies = driver.get_cookies()
        with open(output_path, 'w') as f:
            for cookie in cookies:
                expiry = cookie.get('expiry', '0')  # Default to '0' if 'expiry' doesn't exist
                f.write(f"{cookie['domain']}\tTRUE\t{cookie['path']}\tFALSE\t{expiry}\t{cookie['name']}\t{cookie['value']}\n")

    finally:
        driver.quit()

if __name__ == '__main__':
    app.run(debug=True)
