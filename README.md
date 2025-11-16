
# Vector Store Demo

## Features

- Minimal, clean 3-column UI:
  1. **Raw Data** (dark grey): Folder path, file list, and Vectorize button
  2. **File Preview** (medium grey): Formatted JSON of selected file
  3. **Chat** (light): Minimal chat with reset
- File selection from a folder
- Weaviate backend integration

## Usage

1. Set up your `.env` in `config/.env` (see `config/.env-example`).
2. Run the Streamlit app:
	```sh
	streamlit run app.py
	```
3. Use the UI:
	- Select a folder and file in the left column
	- View file JSON in the center column
	- Use the chat in the right column (resettable)

## Requirements

- Python 3.9+
- See `requirements.txt`
