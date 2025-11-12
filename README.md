# Kakuyomu Downloader

A tool to download novels from [Kakuyomu](https://kakuyomu.jp/) and convert them to EPUB format. This project includes both a command-line interface and a graphical user interface.

## Features

- Download complete novels from Kakuyomu by their book ID
- Automatically converts to EPUB format for convenient reading on e-readers
- Simple command-line interface for scripting
- User-friendly GUI for desktop use
- Random user-agent rotation to avoid rate limiting

## Requirements

- Python 3.6 or higher
- Required Python packages:
  - requests
  - beautifulsoup4
  - ebooklib
  - tkinter (included with most Python installations)

## Installation

1. Clone this repository or download the ZIP file:

   ```
   git clone https://github.com/yourusername/kakuyomu_downloader.git
   cd kakuyomu_downloader
   ```

2. Install required dependencies:

   ```
   pip install requests beautifulsoup4 ebooklib
   ```

3. (Optional) Create a `userAgents.json` file in the project directory with a list of user agents:
   ```json
   [
     "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
     "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Firefox/89.0",
     "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
   ]
   ```

## Usage

### Command-Line Interface

Run the script with a book ID as an argument:

```
python kakuyomu.py install 16816700427572694145
```

Or run without arguments to be prompted for input:

```
python kakuyomu.py
```

The downloaded EPUB files will be saved in the `epub` folder in the current directory.

### Graphical User Interface

Run the GUI version:

```
python kakuyomu_gui.py
```

1. Enter the book ID in the "Book ID" field
2. (Optional) Change the output directory using the "Browse" button
3. Click "Download" to start the download
4. Check the progress in the log area

## Finding Book IDs

Book IDs can be found in the URL of the Kakuyomu novels. For example, in the URL:
[物語の黒幕に転生して～進化する魔剣とゲーム知識ですべてをねじ伏せる～（Web 版）`](https://kakuyomu.jp/works/16816700427572694145)

The book ID is `16816700427572694145`.

## Example

To download the novel "物語の黒幕に転生して～進化する魔剣とゲーム知識ですべてをねじ伏せる～（Web 版）":

```
python kakuyomu.py install 16816700427572694145
```

Or using the GUI, just enter `16816700427572694145` in the Book ID field and click "Download".

## Building Windows Executables

Use [PyInstaller](https://pyinstaller.org/en/stable/) with the provided spec files to produce standalone `.exe` launchers:

```
pyinstaller kakuyomu_gui.spec
pyinstaller narou_gui.spec
```

The resulting executables will be placed inside the `dist/` folder. The specs bundle `userAgents.json` automatically, so keep that file next to the spec when running the command.

## Troubleshooting

- If downloads fail, try again as it might be due to network issues or server-side rate limiting.
- If the selector patterns don't work, the website structure might have changed. Please open an issue.
- Make sure you have proper internet connectivity when downloading books.

## License

[MIT License](LICENSE)
