# YouTube to MP3 Downloader

This is a Flask web application that allows users to input a list of song names, searches YouTube for the first result of each song, downloads the video, converts it to MP3, and provides a ZIP file with all the MP3 files for download.

## Features

- Search for songs on YouTube based on user input.
- Download the first YouTube result as an MP3 file.
- Create a ZIP file containing all downloaded MP3 files.
- Simple web interface for user interaction.

## Requirements

- Python 3.x
- Flask
- pytube
- pydub
- youtube-search-python

## Installation

1. Clone the repository:

    ```bash
    git clone https://github.com/yourusername/your-repo-name.git
    cd your-repo-name
    ```

2. Install the required libraries:

    ```bash
    pip install flask pytube pydub youtube-search-python
    ```

3. Ensure you have FFmpeg installed on your system. You can download it from [FFmpeg official website](https://ffmpeg.org/download.html).

## Directory Structure

    ```
    your_project_folder/
    ├── app.py
    └── templates/
        ├── index.html
        └── download.html
    ```

## Usage

1. Run the Flask application:

    ```bash
    python app.py
    ```

2. Open your web browser and go to `http://127.0.0.1:5000`.

3. Enter the song names separated by commas in the text area and click "Download Songs".

4. After processing, a link to download the ZIP file with the MP3 files will be provided.

## Contributing

1. Fork the repository.
2. Create your feature branch (`git checkout -b feature/your-feature`).
3. Commit your changes (`git commit -m 'Add some feature'`).
4. Push to the branch (`git push origin feature/your-feature`).
5. Open a pull request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- This project uses [pytube](https://github.com/nficano/pytube) for downloading YouTube videos.
- The [pydub](https://github.com/jiaaro/pydub) library is used for audio manipulation.
- [youtube-search-python](https://github.com/alexmercerind/youtube-search-python) is used for searching YouTube videos.
