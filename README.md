# YouTube Video & Playlist Downloader (Streamlit App)

This Streamlit application allows users to download videos or entire playlists from YouTube. It uses `yt-dlp` as the backend downloader.

## Features

-   **Download Single Videos:** Enter a YouTube video URL to download it.
-   **Download Playlists:** Enter a YouTube playlist URL to fetch all videos in the playlist.
-   **Individual Downloads for Playlist Videos:** Each video in a playlist is listed with its own download button.
-   **Numbered Playlist Files:** Videos downloaded from a playlist are automatically prefixed with their playlist index (e.g., `1 - Video Title.mp4`).
-   **Server-Side Download First:** Videos are first downloaded to the server where the Streamlit app is running.
-   **Client-Side Download:** After server-side download, a button appears to download the file to your local computer.
-   **Directory Cleanup:** Option to clean the server-side download directory.

## Prerequisites

Before running this application, ensure you have the following installed:

1.  **Python:** Version 3.7 or higher.
2.  **`yt-dlp`:** This is the core command-line tool used for downloading. It must be installed and accessible in your system's PATH.
    -   Installation: `pip install yt-dlp` or refer to the [official yt-dlp installation guide](https://github.com/yt-dlp/yt-dlp#installation).
3.  **`ffmpeg` (Highly Recommended):** `yt-dlp` often requires `ffmpeg` for merging video and audio streams, especially for higher quality downloads or specific formats. Ensure `ffmpeg` is installed and accessible in your system's PATH.
    -   Download `ffmpeg` from [ffmpeg.org](https://ffmpeg.org/download.html).

## Setup

1.  **Clone the repository or download the files:**
    If this app is part of a repository:
    ```bash
    git clone <repository-url>
    cd <repository-directory>
    ```
    Otherwise, ensure you have the application script (e.g., `youtube_downloader_app.py`) and the `requirements.txt` file.

2.  **Create a virtual environment (recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install Python dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## How to Run

1.  **Navigate to the directory** containing the application script (e.g., `youtube_downloader_app.py`).

2.  **Run the Streamlit app:**
    ```bash
    streamlit run youtube_downloader_app.py
    ```
    (Replace `youtube_downloader_app.py` with the actual name of your Python script if it's different.)

3.  **Open your web browser:** Streamlit will typically open the app automatically in your default browser. If not, it will display a local URL (usually `http://localhost:8501`) that you can navigate to.

## Usage

1.  **Enter URL:** Paste a YouTube video URL or a YouTube playlist URL into the input field.
2.  **Fetch Info:** Click the "🔗 Fetch Video(s) Info" button.
    -   The app will display a list of videos found.
3.  **Start Download (to Server):** For each video you want to download, click the "▶️ Start Download" button.
    -   The video will be downloaded to a temporary directory (default: `yt_dlp_downloads`) on the server where the Streamlit app is running.
    -   You'll see a "⏳ Processing..." status.
4.  **Download File (to Local PC):** Once the server-side download is complete, the button will change to "✅ Download File". Click this to download the video to your computer.
5.  **Clean Up (Optional):** Use the "🧹 Clean Server Download Directory" button in the sidebar to remove all files from the server's temporary download folder.

## File Naming Convention

-   **Single Videos:** `Video Title.extension`
-   **Playlist Videos:** `PlaylistIndex - Video Title.extension` (e.g., `1 - My First Video.mp4`)

## Troubleshooting

-   **`yt-dlp` not found:** Ensure `yt-dlp` is installed and its location is in your system's PATH environment variable.
-   **`ffmpeg` not found:** If downloads fail or you get errors about merging formats, ensure `ffmpeg` is installed and in your PATH.
-   **Download timeouts:** For very large videos or slow connections, the download process might time out. The script has timeouts set, which might need adjustment for extreme cases.
-   **Playlist issues:** Private or region-restricted playlists/videos may not be accessible.
-   **Permissions:** Ensure the Streamlit application has write permissions to the `DOWNLOAD_DIR` (default: `yt_dlp_downloads`) on the server.

## Disclaimer

Downloading copyrighted material without permission may be illegal in your country. Please respect copyright laws and use this tool responsibly.
