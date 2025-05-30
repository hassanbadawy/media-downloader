import streamlit as st
import subprocess
import json
import os
import re # Though yt-dlp handles most sanitization

# --- Configuration ---
DOWNLOAD_DIR = "yt_dlp_downloads"  # Directory to store downloads on the server

# --- Helper Functions ---

def is_playlist(url):
    """Checks if the URL is likely a YouTube playlist."""
    # More robust playlist detection regex
    playlist_patterns = [
        r"(?:https?:\/\/)?(?:www\.)?youtube\.com\/playlist\?list=([a-zA-Z0-9_-]+)",
        r"(?:https?:\/\/)?(?:www\.)?youtube\.com\/watch\?v=([a-zA-Z0-9_-]+)&list=([a-zA-Z0-9_-]+)",
    ]
    for pattern in playlist_patterns:
        if re.search(pattern, url):
            return True
    return "list=" in url # Fallback for simpler cases


def get_playlist_info(playlist_url):
    """
    Uses yt-dlp to get information about all videos in a playlist.
    Returns a list of dictionaries, where each dictionary contains
    info about a video (id, title, url, filename_playlist_index).
    """
    command = [
        "yt-dlp",
        "--flat-playlist",    # Don't extract info from video pages, just list them
        "--print-json",       # Output info as JSON
        playlist_url
    ]
    st.info(f"Fetching playlist info with command: {' '.join(command)}")
    try:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8')
        stdout, stderr = process.communicate(timeout=60) # Added timeout

        if process.returncode != 0:
            st.error(f"Error fetching playlist info (yt-dlp exited with {process.returncode}):")
            if stderr: st.error(f"stderr: {stderr}")
            if stdout: st.warning(f"stdout: {stdout}") # Sometimes errors are on stdout
            return []

        videos_info = []
        if not stdout.strip():
            st.warning("No output from yt-dlp for playlist info. The playlist might be empty or private.")
            return []

        for i, line in enumerate(stdout.strip().split('\n')):
            if line:
                try:
                    video_data = json.loads(line)
                    # Use yt-dlp's playlist_index if available, otherwise use enumeration (1-based)
                    # yt-dlp's playlist_index is usually 1-based.
                    actual_playlist_index_for_naming = video_data.get("playlist_index")
                    if actual_playlist_index_for_naming is None:
                        actual_playlist_index_for_naming = i + 1 # Fallback to 1-based enumeration

                    videos_info.append({
                        "id": video_data.get("id"),
                        "title": video_data.get("title", f"Untitled Video {actual_playlist_index_for_naming}"),
                        "url": f"https://www.youtube.com/watch?v={video_data.get('id')}", # Construct direct video URL
                        "filename_playlist_index": actual_playlist_index_for_naming
                    })
                except json.JSONDecodeError as e:
                    st.warning(f"Could not parse video info line: {line}. Error: {e}")
        return videos_info
    except subprocess.TimeoutExpired:
        st.error("Fetching playlist info timed out. The playlist might be very large or there could be network issues.")
        return []
    except Exception as e:
        st.error(f"An exception occurred while fetching playlist info: {str(e)}")
        return []

def get_single_video_info(video_url):
    """
    Uses yt-dlp to get information about a single video.
    Returns a dictionary with video info (id, title, url).
    """
    command = [
        "yt-dlp",
        "--print-json",
        video_url
    ]
    st.info(f"Fetching single video info with command: {' '.join(command)}")
    try:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8')
        stdout, stderr = process.communicate(timeout=30) # Added timeout

        if process.returncode != 0:
            st.error(f"Error fetching video info (yt-dlp exited with {process.returncode}):")
            if stderr: st.error(f"stderr: {stderr}")
            if stdout: st.warning(f"stdout: {stdout}")
            return None

        if not stdout.strip():
            st.warning("No output from yt-dlp for single video info.")
            return None
        video_data = json.loads(stdout)
        return {
            "id": video_data.get("id"),
            "title": video_data.get("title", "Untitled Video"),
            "url": video_url # Original URL is fine here
        }
    except subprocess.TimeoutExpired:
        st.error("Fetching single video info timed out.")
        return None
    except json.JSONDecodeError as e:
        st.error(f"Could not parse single video JSON: {stdout}. Error: {e}")
        return None
    except Exception as e:
        st.error(f"An exception occurred while fetching single video info: {str(e)}")
        return None

def download_video_yt_dlp(video_url, download_path=".", playlist_index_for_filename=None):
    """
    Downloads a single video using yt-dlp to the specified download_path on the server.
    Returns the full path to the downloaded file or None if download failed.
    """
    if not os.path.exists(download_path):
        try:
            os.makedirs(download_path)
        except OSError as e:
            st.error(f"Failed to create download directory {download_path}: {e}")
            return None

    # Construct the output template for yt-dlp
    # yt-dlp handles sanitization of %(title)s and determines %(ext)s
    if playlist_index_for_filename is not None:
        # Format: "1 - Video Title.mp4"
        output_template_str = f"{playlist_index_for_filename} - %(title)s.%(ext)s"
    else:
        # Format: "Video Title.mp4"
        output_template_str = "%(title)s.%(ext)s"

    # Full path for the output template
    full_output_template = os.path.join(download_path, output_template_str)

    command = [
        "yt-dlp",
        "-o", full_output_template, # Output template (path + filename format)
        "--no-simulate",            # Ensure it actually downloads
        "--print", "filename",      # Print the final filename to stdout
        # "--progress",             # Optional: show progress in console (not easily captured by Streamlit live)
        # "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best", # Example format selection
        video_url
    ]

    st.info(f"Attempting to download: {video_url}")
    st.caption(f"yt-dlp command: {' '.join(command)}") # For debugging

    try:
        # Using text=True for easier stdout/stderr handling
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8')
        # Stream output for better feedback (optional, more complex for live UI updates)
        stdout_lines = []
        stderr_lines = []

        # Read stdout line by line
        for line in iter(process.stdout.readline, ''):
            line = line.strip()
            if line:
                stdout_lines.append(line)
                # st.write(f"dl out: {line}") # For live debug, can be noisy
        process.stdout.close()

        # Read stderr
        for line in iter(process.stderr.readline, ''):
            line = line.strip()
            if line:
                stderr_lines.append(line)
                # st.write(f"dl err: {line}") # For live debug
        process.stderr.close()

        process.wait(timeout=600) # Wait for the download to complete (e.g., 10 minutes timeout)
        
        stdout_full = "\n".join(stdout_lines)
        stderr_full = "\n".join(stderr_lines)

        if process.returncode == 0 and stdout_lines:
            # yt-dlp --print filename might output other info if remuxing.
            # The actual filename is usually the last non-empty line of stdout.
            downloaded_file_path = stdout_lines[-1]
            if os.path.exists(downloaded_file_path):
                st.success(f"Server download complete: {os.path.basename(downloaded_file_path)}")
                return downloaded_file_path
            else:
                st.error(f"yt-dlp reported success, but file not found: {downloaded_file_path}")
                if stdout_full: st.info(f"yt-dlp stdout:\n{stdout_full}")
                if stderr_full: st.warning(f"yt-dlp stderr:\n{stderr_full}")
                return None
        else:
            st.error(f"Download failed for {video_url} (yt-dlp exit code: {process.returncode}).")
            if stdout_full: st.info(f"yt-dlp stdout:\n{stdout_full}")
            if stderr_full: st.warning(f"yt-dlp stderr:\n{stderr_full}")
            return None
    except subprocess.TimeoutExpired:
        st.error(f"Download timed out for {video_url}. The video might be too large or network slow.")
        # Attempt to kill the process if it's still running
        if process.poll() is None: # Check if process is still running
            process.kill()
            st.warning("yt-dlp process was killed due to timeout.")
        return None
    except Exception as e:
        st.error(f"An unexpected error occurred during download: {str(e)}")
        return None

# --- Streamlit App UI ---

st.set_page_config(page_title="YouTube Downloader", layout="wide", initial_sidebar_state="collapsed")
st.title("🎬 YouTube Video & Playlist Downloader")
st.markdown(f"""
Enter a YouTube video URL or a playlist URL. Videos will be downloaded to the server
first (into a temporary folder `{DOWNLOAD_DIR}`), then you can download them to your PC.
""")
st.markdown("---")

# Initialize session state variables
if 'url_input' not in st.session_state:
    st.session_state.url_input = ""
if 'videos_to_process' not in st.session_state:
    st.session_state.videos_to_process = [] # List of video dicts
if 'download_status' not in st.session_state:
    # Stores {video_id: {"status": "pending/processing/completed/failed", "path": "filepath_or_error_msg"}}
    st.session_state.download_status = {}

# Input URL
current_url_input = st.text_input("YouTube URL (Video or Playlist):", value=st.session_state.url_input, key="url_text_input")

if st.button("🔗 Fetch Video(s) Info", key="fetch_button") or \
   (current_url_input and current_url_input != st.session_state.url_input):

    st.session_state.url_input = current_url_input
    st.session_state.videos_to_process = [] # Reset for new URL
    st.session_state.download_status = {}   # Reset statuses

    if not st.session_state.url_input:
        st.warning("Please enter a URL.")
    else:
        with st.spinner("Fetching video(s) information... 🕵️‍♂️ This might take a moment."):
            if is_playlist(st.session_state.url_input):
                st.info("Playlist URL detected. Fetching video list...")
                videos = get_playlist_info(st.session_state.url_input)
                if videos:
                    st.session_state.videos_to_process = videos
                    st.success(f"Found {len(videos)} videos in the playlist.")
                else:
                    st.warning("Could not retrieve videos from the playlist, or the playlist is empty/private.")
            else:
                st.info("Single video URL detected. Fetching video information...")
                video_info = get_single_video_info(st.session_state.url_input)
                if video_info:
                    # For consistency, treat single videos as a list of one
                    st.session_state.videos_to_process = [video_info]
                    st.success("Video information fetched.")
                else:
                    st.warning("Could not retrieve video information.")

# Display videos and download buttons
if st.session_state.videos_to_process:
    st.markdown("---")
    st.subheader(f"📋 Videos Found ({len(st.session_state.videos_to_process)}):")

    for index, video_data in enumerate(st.session_state.videos_to_process):
        video_id = video_data.get("id", f"video_{index}")
        video_title = video_data.get("title", f"Video {index+1}")
        video_display_url = video_data.get("url", "N/A")
        
        # Determine the playlist index for display (if applicable)
        display_prefix = ""
        if is_playlist(st.session_state.url_input) and "filename_playlist_index" in video_data:
            display_prefix = f"{video_data['filename_playlist_index']}. "

        st.markdown(f"**{display_prefix}{video_title}**")
        st.caption(f"ID: {video_id} | URL: {video_display_url}")

        video_status_info = st.session_state.download_status.get(video_id, {"status": "pending"})
        status = video_status_info.get("status")
        file_path_or_msg = video_status_info.get("path")

        button_col, status_col = st.columns([1, 3]) # Adjusted column ratio for potentially longer button text

        with button_col:
            if status == "pending":
                if st.button(f"▶️ Start Download", key=f"start_dl_{video_id}_{index}"): # Changed button text and key
                    st.session_state.download_status[video_id] = {"status": "processing"}
                    st.experimental_rerun()
            elif status == "completed" and file_path_or_msg and os.path.exists(file_path_or_msg):
                with open(file_path_or_msg, "rb") as fp:
                    st.download_button(
                        label="✅ Download File",
                        data=fp,
                        file_name=os.path.basename(file_path_or_msg), # Use the actual filename from server
                        mime="application/octet-stream", # Generic binary file
                        key=f"serve_{video_id}_{index}"
                    )
            elif status == "processing":
                st.button("⏳ Processing...", disabled=True, key=f"proc_{video_id}_{index}")


        with status_col:
            if status == "processing":
                # This block will execute when rerun after "Start Download" is clicked
                with st.spinner(f"Downloading '{video_title}' to server... Please wait."):
                    playlist_idx_for_file = video_data.get('filename_playlist_index') if is_playlist(st.session_state.url_input) else None
                    
                    downloaded_file_server_path = download_video_yt_dlp(
                        video_data.get('url'),
                        download_path=DOWNLOAD_DIR,
                        playlist_index_for_filename=playlist_idx_for_file
                    )
                    if downloaded_file_server_path and os.path.exists(downloaded_file_server_path):
                        st.session_state.download_status[video_id] = {"status": "completed", "path": downloaded_file_server_path}
                    else:
                        st.session_state.download_status[video_id] = {"status": "failed", "path": "Server download failed."}
                    st.experimental_rerun() # Rerun to update button to "Download File" or show error
            elif status == "failed":
                st.error(f"Failed: {file_path_or_msg or 'Unknown error'}")
            elif status == "completed" and not (file_path_or_msg and os.path.exists(file_path_or_msg)):
                 st.error(f"Download was marked complete, but file is missing: {file_path_or_msg}")


        st.markdown("---") # Separator for each video entry

# Optional: Cleanup old files
st.sidebar.title("Server Options")
if st.sidebar.button("🧹 Clean Server Download Directory", key="clean_dir"):
    if os.path.exists(DOWNLOAD_DIR):
        cleaned_count = 0
        error_count = 0
        with st.spinner(f"Cleaning up `{DOWNLOAD_DIR}` on the server..."):
            for item_name in os.listdir(DOWNLOAD_DIR):
                item_path = os.path.join(DOWNLOAD_DIR, item_name)
                try:
                    if os.path.isfile(item_path) or os.path.islink(item_path):
                        os.unlink(item_path)
                        cleaned_count += 1
                    # Add shutil.rmtree(item_path) if you want to remove subdirectories too
                except Exception as e:
                    st.sidebar.error(f"Failed to delete {item_path}: {e}")
                    error_count +=1
        if cleaned_count > 0:
            st.sidebar.success(f"Cleaned {cleaned_count} item(s) from `{DOWNLOAD_DIR}`.")
        if error_count == 0 and cleaned_count == 0:
            st.sidebar.info(f"`{DOWNLOAD_DIR}` is already empty or no files to clean.")
        # Reset download statuses as files are gone
        st.session_state.download_status = {}
        st.experimental_rerun()
    else:
        st.sidebar.info(f"Directory `{DOWNLOAD_DIR}` does not exist on the server.")

st.markdown(f"<div style='text-align: center; margin-top: 30px;'>App by Your Friendly AI Assistant</div>", unsafe_allow_html=True)
