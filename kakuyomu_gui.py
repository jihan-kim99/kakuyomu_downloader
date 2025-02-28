import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import requests
from bs4 import BeautifulSoup
import json
from typing import Optional, List
from pathlib import Path
import random
from ebooklib import epub
import threading
import os
import sys

class KakuyomuGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Kakuyomu Downloader")
        self.root.geometry("600x400")
        
        # Create main frame
        main_frame = ttk.Frame(root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        
        # Book ID input frame
        input_frame = ttk.Frame(main_frame)
        input_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        input_frame.columnconfigure(1, weight=1)
        
        ttk.Label(input_frame, text="Book ID:").grid(row=0, column=0, padx=(0, 5))
        self.book_id_var = tk.StringVar()
        self.book_id_entry = ttk.Entry(input_frame, textvariable=self.book_id_var)
        self.book_id_entry.grid(row=0, column=1, sticky=(tk.W, tk.E))
        
        # Output directory selection
        dir_frame = ttk.Frame(main_frame)
        dir_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        dir_frame.columnconfigure(1, weight=1)
        
        ttk.Label(dir_frame, text="Save to:").grid(row=0, column=0, padx=(0, 5))
        self.output_dir_var = tk.StringVar(value=str(Path.cwd() / "epub"))
        self.output_dir_entry = ttk.Entry(dir_frame, textvariable=self.output_dir_var)
        self.output_dir_entry.grid(row=0, column=1, sticky=(tk.W, tk.E))
        ttk.Button(dir_frame, text="Browse", command=self.browse_output_dir).grid(row=0, column=2, padx=(5, 0))
        
        # Download button
        self.download_button = ttk.Button(main_frame, text="Download", command=self.start_download)
        self.download_button.grid(row=2, column=0, columnspan=2, pady=10)
        
        # Progress label
        self.progress_var = tk.StringVar(value="Ready")
        ttk.Label(main_frame, textvariable=self.progress_var).grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        # Log text area
        self.log_text = tk.Text(main_frame, height=15, width=60)
        self.log_text.grid(row=4, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        
        # Scrollbar for log
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=self.log_text.yview)
        scrollbar.grid(row=4, column=1, sticky=(tk.N, tk.S))
        self.log_text.configure(yscrollcommand=scrollbar.set)
        
        # Load user agents
        self.user_agents = self.load_user_agents()
        
        # Error handling for frozen executables
        if getattr(sys, 'frozen', False):
            sys.stdout = open(os.devnull, 'w')
            sys.stderr = open(os.devnull, 'w')

    def browse_output_dir(self):
        """Open directory browser dialog."""
        dir_path = filedialog.askdirectory(initialdir=self.output_dir_var.get())
        if dir_path:
            self.output_dir_var.set(dir_path)

    def load_user_agents(self):
        """Load user agents from JSON file or return default list if file not found."""
        default_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Firefox/89.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        ]
        
        try:
            if getattr(sys, 'frozen', False):
                # If running as compiled executable
                base_path = sys._MEIPASS
            else:
                # If running as script
                base_path = os.path.dirname(os.path.abspath(__file__))
                
            user_agents_path = os.path.join(base_path, 'userAgents.json')
            
            if os.path.exists(user_agents_path):
                with open(user_agents_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return default_agents
        except Exception as e:
            self.log(f"Warning: Could not load user agents file, using defaults. Error: {str(e)}")
            return default_agents

    def log(self, message):
        """Add message to log text area."""
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()

    def start_download(self):
        """Start download in a separate thread."""
        book_id = self.book_id_var.get().strip()
        if not book_id:
            messagebox.showerror("Error", "Please enter a book ID")
            return
        
        output_dir = Path(self.output_dir_var.get())
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            messagebox.showerror("Error", f"Could not create output directory: {str(e)}")
            return
        
        self.download_button.configure(state='disabled')
        self.progress_var.set("Downloading...")
        
        # Start download in a separate thread
        thread = threading.Thread(target=self.download_book, args=(book_id, output_dir))
        thread.daemon = True
        thread.start()

    def download_book(self, book_id, output_dir):
        """Download the book."""
        try:
            downloader = KakuyomuDownloader(book_id, self.log, output_dir)
            success = downloader.download(self.user_agents)
            
            if success:
                self.progress_var.set("Download completed!")
                messagebox.showinfo("Success", "Book downloaded successfully!")
            else:
                self.progress_var.set("Download failed")
                messagebox.showerror("Error", "Failed to download book")
        except Exception as e:
            self.progress_var.set("Error occurred")
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
        finally:
            self.root.after(0, lambda: self.download_button.configure(state='normal'))

class KakuyomuDownloader:
    def __init__(self, book_id: str, log_callback, output_dir: Path):
        self.book_id = book_id
        self.log = log_callback
        self.output_dir = output_dir

    def get_base_url(self) -> str:
        return f"https://kakuyomu.jp/works/{self.book_id}"

    def download(self, user_agents: List[str]) -> bool:
        base_url = self.get_base_url()
        self.log(f"Base URL: {base_url}")

        user_agent = random.choice(user_agents)
        self.log(f"Using User Agent: {user_agent}")

        headers = {'User-Agent': user_agent}

        try:
            # Get first page
            response = requests.get(base_url, headers=headers, timeout=30)
            response.raise_for_status()  # Raise exception for bad status codes
            soup = BeautifulSoup(response.text, 'html.parser')

            # Get title
            title_element = soup.select_one("#app > div.DefaultTemplate_fixed__DLjCr.DefaultTemplate_isWeb__QRPlB.DefaultTemplate_fixedGlobalFooter___dZog > div > div > main > div.NewBox_box__45ont.NewBox_padding-px-4l__Kx_xT.NewBox_padding-pt-7l__Czm59 > div > div.Gap_size-2l__HWqrr.Gap_direction-y__Ee6Qv > div.Gap_size-3s__fjxCP.Gap_direction-y__Ee6Qv > h1 > span > a")
            if not title_element:
                self.log("Could not find title")
                return False
                
            title = title_element.text
            self.log(f"Title: {title}")

            # Create EPUB book
            book = epub.EpubBook()
            book.set_identifier(self.book_id)
            book.set_title(title)
            book.set_language('ja')
            book.add_author("Unknown Author")

            # Get first episode link
            first_link = soup.select_one("#app > div.DefaultTemplate_fixed__DLjCr.DefaultTemplate_isWeb__QRPlB.DefaultTemplate_fixedGlobalFooter___dZog > div > div > main > div.NewBox_box__45ont.NewBox_padding-px-4l__Kx_xT.NewBox_padding-pt-7l__Czm59 > div > div.Gap_size-2l__HWqrr.Gap_direction-y__Ee6Qv > div.Gap_size-m__thYv4.Gap_direction-y__Ee6Qv > div > a")
            
            if not first_link:
                self.log("Could not find first episode link")
                return False

            first_url = f"https://kakuyomu.jp{first_link['href']}"
            self.log(f"First URL: {first_url}")

            # Download all episodes
            current_url = first_url
            chapters = []
            episode_num = 1

            while True:
                self.log(f"Downloading episode {episode_num}")
                
                response = requests.get(current_url, headers=headers, timeout=30)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, 'html.parser')
                
                episode_title_element = soup.select_one(".widget-episodeTitle.js-vertical-composition-item")
                episode_title = episode_title_element.text.strip() if episode_title_element else f"Episode {episode_num}"

                episode_content = soup.select_one(".widget-episodeBody.js-episode-body")
                if episode_content:
                    chapter = epub.EpubHtml(title=episode_title, file_name=f'chapter_{episode_num}.xhtml', lang='ja')
                    chapter.content = f"<h3>{episode_title}</h3>{episode_content.prettify()}"
                    book.add_item(chapter)
                    chapters.append(chapter)
                
                next_link = soup.select_one("#contentMain-readNextEpisode")
                if not next_link:
                    self.log("No more episodes found")
                    break
                    
                current_url = f"https://kakuyomu.jp{next_link['href']}"
                episode_num += 1

            # Finalize EPUB
            book.toc = tuple(epub.Link(chapter.file_name, chapter.title, chapter.file_name) for chapter in chapters)
            book.add_item(epub.EpubNcx())
            book.add_item(epub.EpubNav())
            book.spine = ['nav'] + chapters

            # Save the book
            epub_path = self.output_dir / f"{title}.epub"
            epub.write_epub(str(epub_path), book)
            self.log(f"Successfully saved to {epub_path}")
            return True
            
        except requests.exceptions.RequestException as e:
            self.log(f"Network error: {str(e)}")
            return False
        except Exception as e:
            self.log(f"Error: {str(e)}")
            return False

def main():
    root = tk.Tk()
    app = KakuyomuGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()