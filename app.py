from flask import Flask, render_template, request, jsonify, send_file, url_for
from pytube import YouTube
from pydub import AudioSegment
from youtubesearchpython import VideosSearch
import os
import zipfile
import threading
import requests
from datetime import datetime

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

# Start Render Index page
@app.route('/')
def index():
    global stop_download, song_queue, song_status, total_users
    with open('counter.txt', 'r') as file:
        counter = file.read()
        total_users = totalUsers()
    return render_template('index.html', total_users=total_users, counter=counter)
# End Render Index page

# Start Update counter
def updateCounter():
    # Define the file path
    file_path = 'counter.txt'

    # Read the current counter value
    with open(file_path, 'r') as file:
        counter = int(file.read().strip())

    # Increment the counter
    counter += 1

    # Write the updated counter value back to the file
    with open(file_path, 'w') as file:
        file.write(str(counter))
# End Update counter


# Start Clean download directory
@app.route('/clean_download_directory_ajax')
def clean_download_directory_ajax():
    if os.path.exists(downloads_path):
        for file in os.listdir(downloads_path):
            os.remove(os.path.join(downloads_path, file))
    else:
        os.makedirs(downloads_path)
        
    return jsonify({
        "success": True,
        "message": 'Directory Cleaned'
    })
# End Clean download directory


# Start Search song on youtube and return youtube link if found
def search_youtube(query):
    videos_search = VideosSearch(query, limit=1)
    result = videos_search.result()
    return result['result'][0]['link'] if result['result'] else None
# End Search song on youtube and return youtube link if found


# Start Download song from youtube and convert it into mp3
def download_youtube_as_mp3(url, song_name):
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
        mp3_file = os.path.join(downloads_path, song_name + '.mp3')
        mp3_file_name = os.path.join(song_name + '.mp3')        
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
        return mp3_file_name
    except Exception as e:
        print(f"An error occurred: {e}")
        song_status[current_song] = f"error: {str(e)}"
        return None
# End Download song from youtube and convert it into mp3


# Start Create Zip file of downloaded songs
@app.route('/create_zip', methods=['POST'])
def create_zip_file_for_songs():
    data = request.get_json()  # Parse JSON data
    songs_list = data.get('songs_list')  # Get songs list
    if not songs_list:
        updateUserInfo('Creating Zip', 'error: No songs provided to zip', 'songs.zip')
        return jsonify({
            "success": False,
            "message": 'No songs provided to zip'
        })
    file_paths = songs_list.split(',')
    zip_file_path = os.path.join('static', 'songs.zip')  # Example path
    try:
        with zipfile.ZipFile(zip_file_path, 'w') as zip_file:
            for file in file_paths:
                file = os.path.join('downloads', file)
                if os.path.isfile(file):  # Check if the file exists
                    zip_file.write(file, os.path.basename(file))
                else:
                    return jsonify({
                        "success": False,
                        "message": f'File not found: {file}'
                    })
        updateUserInfo('Creating Zip', 'Zip has been created', 'songs.zip')
        return jsonify({
            "success": True,
            "message": f"Zip has been created.",
            "zip_file_url": url_for('static', filename='songs.zip')  # Generate URL
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f'Unable to create zip file: {str(e)}'
        })
# Eng Create Zip file of downloaded songs





# Start Search song on youtube and download it and convert it into mp3
@app.route('/download_song/<song_name>')
def download_song(song_name):
    global song_status
    try:
        youtube_url = search_youtube(song_name.strip())
        if youtube_url:
            mp3_file = download_youtube_as_mp3(youtube_url, song_name)
            if mp3_file:   
                updateCounter()
                updateUserInfo('Download Song', 'success', song_name)             
                return jsonify({
                    "success": True,
                    "message": f"Successfully downloaded {song_name}",
                    "downloaded_file": mp3_file
                })
            else:
                song_status[song_name] = "error: Download failed."
                updateUserInfo('Download Song', 'error: Download failed', song_name)
                return jsonify({
                    "success": False,
                    "message": "Download failed. Please provide more lyrics to identify the song"
                })
        else:
            song_status[song_name] = "error: Song not found."
            updateUserInfo('Download Song', 'error: Song not found', song_name)
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
# End Search song on youtube and download it and convert it into mp3


# Start Get user IP address
def get_public_ip():
    """
    Fetches the public IP address of the user using an external service.
    
    :return: str, public IP address
    """
    try:
        response = requests.get('https://api.ipify.org?format=text')
        response.raise_for_status()  # Raise an error for bad status codes
        return response.text
    except requests.RequestException as e:
        print(f"Failed to get public IP address: {e}")
        return None
# End Get user IP address

# Start Create a file for the user with his IP Address
def create_ip_file():
    """
    Creates a file named after the user's public IP address if it does not exist.
    
    :return: str, path to the created file or None if failed
    """
    ip_address = get_public_ip()
    if ip_address is None:
        return None  # Exit if IP address could not be fetched

    file_path = f"users/{ip_address}.txt"
    
    if not os.path.exists(file_path):
        with open(file_path, 'w') as file:
            file.write(f"IP Address: {ip_address}\n")
        print(f"File created with IP address: {ip_address}")
    else:
        print(f"File already exists: {file_path}")
    
    return file_path
# End Create a file for the user with his IP Address

# Start Add Data to the user's file
def append_to_file(file_path, data):
    """
    Appends data to the specified file.
    
    :param file_path: str, path to the file
    :param data: str, data to be appended to the file
    """
    with open(file_path, 'a') as file:
        file.write(data + "\n")
    print(f"Data appended to file: {data}")
# Start Add Data to the user's file
# Start UserInfo Updater
def updateUserInfo(action, status, data_to_append):
    file_path = create_ip_file()
    if file_path:
        current_time = datetime.now().strftime("%d-%B-%Y %I:%M %p")
        formatted_data = f"{current_time} | Action: {action} | Status: {status} | -- {data_to_append}"
        append_to_file(file_path, formatted_data)
# End UserInfo Updater

# Start Get total users count
def totalUsers():
    # Initialize a counter
    total_files = 0

    # Iterate through all files in the directory
    for root, dirs, files in os.walk('users'):
        total_files += len(files)

    return total_files
# End Get total users count


if __name__ == "__main__":
    app.run(debug=True)
