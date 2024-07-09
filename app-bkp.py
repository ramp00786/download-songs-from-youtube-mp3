from flask import Flask, render_template, request, jsonify, send_file
from pytube import YouTube
from pydub import AudioSegment
from youtubesearchpython import VideosSearch
import os
import zipfile
import threading

app = Flask(__name__)

downloads_path = "downloads"
zip_file_path = "downloaded_songs.zip"
stop_download = False
current_song = ""
song_queue = []
song_status = {}
song_progress = {}
total_users = 0
total_songs = 0

@app.route('/', methods=['GET', 'POST'])
def index():
    global stop_download, song_queue, song_status, total_users
    if request.method == 'POST':
        song_names = request.form.get('song_names')
        song_queue = song_names.split(',')
        stop_download = False
        song_status = {song: "pending" for song in song_queue}
        total_users += 1

        threading.Thread(target=start_download).start()
        return render_template('index.html', song_queue=song_queue, song_status=song_status)
    
    return render_template('index.html', song_queue=song_queue, song_status=song_status)

def start_download():
    clean_download_directory()
    downloaded_files = download_songs(song_queue)
    
    if downloaded_files:
        create_zip_file(downloaded_files)

def clean_download_directory():
    if os.path.exists(downloads_path):
        for file in os.listdir(downloads_path):
            os.remove(os.path.join(downloads_path, file))
    else:
        os.makedirs(downloads_path)

def search_youtube(query):
    videos_search = VideosSearch(query, limit=1)
    result = videos_search.result()
    return result['result'][0]['link'] if result['result'] else None

def download_youtube_as_mp3(url):
    global stop_download, current_song, song_status, total_songs, song_progress, song_queue
    try:
        if stop_download:
            return None
        
        yt = YouTube(url)
        video = yt.streams.filter(only_audio=True).first()
        current_song = yt.title
        song_status[current_song] = "downloading"
        song_progress[current_song] = 0

        # Download video
        video.download(output_path=downloads_path)
        
        # Convert to MP3
        base, ext = os.path.splitext(video.default_filename)
        video_file = os.path.join(downloads_path, video.default_filename)
        mp3_file = os.path.join(downloads_path, base + '.mp3')
        
        audio = AudioSegment.from_file(video_file)
        audio.export(mp3_file, format="mp3")
        
        # Clean up video file
        os.remove(video_file)

        song_status[current_song] = "finished"
        song_progress[current_song] = 100
        total_songs += 1
        
        # Remove song from queue once downloaded
        if current_song in song_queue:
            song_queue.remove(current_song)
        
        return mp3_file
    except Exception as e:
        print(f"An error occurred: {e}")
        song_status[current_song] = f"error: {str(e)}"
        return None

def download_songs(song_list):
    downloaded_files = []
    
    for song_name in song_list:
        youtube_url = search_youtube(song_name.strip())
        if youtube_url:
            mp3_file = download_youtube_as_mp3(youtube_url)
            if mp3_file:
                downloaded_files.append(mp3_file)
    
    return downloaded_files

def create_zip_file(file_paths):
    with zipfile.ZipFile(zip_file_path, 'w') as zip_file:
        for file in file_paths:
            zip_file.write(file, os.path.basename(file))
    
    return zip_file_path

@app.route('/progress')
def progress():
    overall_progress = calculate_overall_progress()
    return jsonify({
        "song_status": song_status,
        "song_progress": song_progress,
        "current_song": current_song,
        "overall_progress": overall_progress
    })

def calculate_overall_progress():
    if not song_queue:
        return 0
    finished_count = sum(1 for status in song_status.values() if status == 'finished')
    return finished_count / len(song_queue) * 100

@app.route('/statistics')
def statistics():
    return jsonify({
        "total_users": total_users,
        "total_songs_downloaded_yet": total_songs
    })

@app.route('/stop', methods=['POST'])
def stop():
    global stop_download
    stop_download = True
    return jsonify(message="Downloading stopped. You can download the ZIP file now.")

@app.route('/download_zip')
def download_zip():
    if not os.path.exists(zip_file_path):
        return jsonify(message="No songs downloaded."), 400
    if total_songs == 0:
        return jsonify(message="No songs downloaded yet."), 400
    return send_file(zip_file_path, as_attachment=True)

@app.route('/download_song/<song_name>', methods=['GET'])
def download_song(song_name):
    global song_status, total_songs, song_progress, song_queue
    try:
        youtube_url = search_youtube(song_name.strip())
        if youtube_url:
            mp3_file = download_youtube_as_mp3(youtube_url)
            if mp3_file:
                total_songs += 1
                song_progress[song_name] = 100
                song_status[song_name] = "finished"
                song_queue.remove(song_name)
                return jsonify({
                    "success": True,
                    "message": f"Successfully downloaded {song_name}"
                })
            else:
                song_status[song_name] = "error: Download failed."
                return jsonify({
                    "success": False,
                    "message": "Download failed."
                })
        else:
            song_status[song_name] = "error: Song not found."
            return jsonify({
                "success": False,
                "message": "Song not found."
            })
    except Exception as e:
        print(f"Error downloading {song_name}: {str(e)}")
        song_status[song_name] = f"error: {str(e)}"
        return jsonify({
            "success": False,
            "message": f"Error downloading {song_name}: {str(e)}"
        }), 500

@app.route('/clear_data', methods=['POST'])
def clear_data():
    global song_queue, song_status, song_progress, stop_download, current_song
    song_queue = []
    song_status = {}
    song_progress = {}
    stop_download = True
    current_song = ""
    return jsonify(message="Data cleared except statistics.")

if __name__ == "__main__":
    app.run(debug=True)
