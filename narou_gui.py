import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
from pathlib import Path
from typing import List
import threading
import os
import sys

from narou_downloader import NarouDownloader


class NarouGUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Narou Downloader")
        self.root.geometry("600x400")

        main_frame = ttk.Frame(root, padding="10")
        main_frame.grid(row=0, column=0, sticky="nsew")

        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)

        input_frame = ttk.Frame(main_frame)
        input_frame.grid(row=0, column=0, columnspan=2, sticky="we", pady=5)
        input_frame.columnconfigure(1, weight=1)

        ttk.Label(input_frame, text="Novel ID:").grid(row=0, column=0, padx=(0, 5))
        self.novel_id_var = tk.StringVar()
        self.novel_id_entry = ttk.Entry(input_frame, textvariable=self.novel_id_var)
        self.novel_id_entry.grid(row=0, column=1, sticky="we")

        dir_frame = ttk.Frame(main_frame)
        dir_frame.grid(row=1, column=0, columnspan=2, sticky="we", pady=5)
        dir_frame.columnconfigure(1, weight=1)

        ttk.Label(dir_frame, text="Save to:").grid(row=0, column=0, padx=(0, 5))
        self.output_dir_var = tk.StringVar(value=str(Path.cwd() / "epub"))
        self.output_dir_entry = ttk.Entry(dir_frame, textvariable=self.output_dir_var)
        self.output_dir_entry.grid(row=0, column=1, sticky="we")
        ttk.Button(dir_frame, text="Browse", command=self.browse_output_dir).grid(row=0, column=2, padx=(5, 0))

        self.download_button = ttk.Button(main_frame, text="Download", command=self.start_download)
        self.download_button.grid(row=2, column=0, columnspan=2, pady=10)

        self.progress_var = tk.StringVar(value="Ready")
        ttk.Label(main_frame, textvariable=self.progress_var).grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=5)

        self.log_text = tk.Text(main_frame, height=15, width=60)
        self.log_text.grid(row=4, column=0, sticky="nsew", pady=10)

        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=self.log_text.yview)
        scrollbar.grid(row=4, column=1, sticky="ns")
        self.log_text.configure(yscrollcommand=scrollbar.set)

        self.user_agents = self.load_user_agents()

        if getattr(sys, 'frozen', False):
            sys.stdout = open(os.devnull, 'w')
            sys.stderr = open(os.devnull, 'w')

    def browse_output_dir(self) -> None:
        dir_path = filedialog.askdirectory(initialdir=self.output_dir_var.get())
        if dir_path:
            self.output_dir_var.set(dir_path)

    def load_user_agents(self) -> List[str]:
        default_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Firefox/89.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        ]

        try:
            if getattr(sys, 'frozen', False):
                base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
            else:
                base_path = os.path.dirname(os.path.abspath(__file__))

            user_agents_path = os.path.join(base_path, 'userAgents.json')

            if os.path.exists(user_agents_path):
                with open(user_agents_path, 'r', encoding='utf-8') as file:
                    return json.load(file)
            return default_agents
        except Exception as exc:
            self.log(f"Warning: Could not load user agents file, using defaults. Error: {exc}")
            return default_agents

    def log(self, message: str) -> None:
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()

    def start_download(self) -> None:
        novel_id = self.novel_id_var.get().strip()
        if not novel_id:
            messagebox.showerror("Error", "Please enter a novel ID")
            return

        output_dir = Path(self.output_dir_var.get())
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
        except Exception as exc:
            messagebox.showerror("Error", f"Could not create output directory: {exc}")
            return

        self.download_button.configure(state='disabled')
        self.progress_var.set("Downloading...")

        thread = threading.Thread(target=self.download_book, args=(novel_id, output_dir))
        thread.daemon = True
        thread.start()

    def download_book(self, novel_id: str, output_dir: Path) -> None:
        try:
            downloader = NarouDownloader(novel_id=novel_id, log=self.log, output_dir=output_dir)
            success = downloader.download(self.user_agents)

            if success:
                self.progress_var.set("Download completed!")
                messagebox.showinfo("Success", "Novel downloaded successfully!")
            else:
                self.progress_var.set("Download failed")
                messagebox.showerror("Error", "Failed to download novel")
        except Exception as exc:
            self.progress_var.set("Error occurred")
            messagebox.showerror("Error", f"An error occurred: {exc}")
        finally:
            self.root.after(0, lambda: self.download_button.configure(state='normal'))


def main() -> None:
    root = tk.Tk()
    app = NarouGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
