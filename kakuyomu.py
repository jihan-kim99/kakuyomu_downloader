import requests
from bs4 import BeautifulSoup
import json
import argparse
from typing import Optional, List
from pathlib import Path
import random
from ebooklib import epub

class KakuyomuApp:
    def __init__(self, book_id: Optional[str] = None):
        print("Initializing Kakuyomu App...")
        self.book_id = book_id
        if book_id is None:
            print("Book ID not found")
        else:
            print(f"Book ID: {book_id}")

    def get_base_url(self, book_id: Optional[str] = None) -> Optional[str]:
        """Generate base URL for the book."""
        book_id = book_id or self.book_id
        if not book_id:
            print("Book id doesn't set.")
            return None
        return f"https://kakuyomu.jp/works/{book_id}"

    def download(self, user_agents: List[str], book_id: Optional[str] = None) -> bool:
        """Download all episodes of a book and save as an EPUB file."""
        book_id = book_id or self.book_id
        if not book_id:
            print("Book id doesn't set.")
            return False

        base_url = self.get_base_url(book_id)
        print(f"[INFO] base_url: {base_url}")

        # Randomly select a user agent
        user_agent = random.choice(user_agents)
        print(f"[INFO] Use userAgent: {user_agent}")

        headers = {'User-Agent': user_agent}

        # Get first page
        response = requests.get(base_url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')

        # Get title
        title_element = soup.select_one("#app > div.DefaultTemplate_fixed__DLjCr.DefaultTemplate_isWeb__QRPlB.DefaultTemplate_fixedGlobalFooter___dZog > div > div > main > div.NewBox_box__45ont.NewBox_padding-px-4l__Kx_xT.NewBox_padding-pt-7l__Czm59 > div > div.Gap_size-2l__HWqrr.Gap_direction-y__Ee6Qv > div.Gap_size-3s__fjxCP.Gap_direction-y__Ee6Qv > h1 > span > a")
        if not title_element:
            print("[ERROR] Could not find title")
            return False
            
        title = title_element.text
        print(f"[INFO] title: {title}")

        # Create an EPUB book
        book = epub.EpubBook()
        book.set_identifier(book_id)
        book.set_title(title)
        book.set_language('ja')

        # Add a default author
        book.add_author("Unknown Author")

        # Get first episode link
        print("[LOG] start getting url...")
        first_link = soup.select_one("#app > div.DefaultTemplate_fixed__DLjCr.DefaultTemplate_isWeb__QRPlB.DefaultTemplate_fixedGlobalFooter___dZog > div > div > main > div.NewBox_box__45ont.NewBox_padding-px-4l__Kx_xT.NewBox_padding-pt-7l__Czm59 > div > div.Gap_size-2l__HWqrr.Gap_direction-y__Ee6Qv > div.Gap_size-m__thYv4.Gap_direction-y__Ee6Qv > div > a")
        
        if not first_link:
            print("[ERROR] Could not find first episode link")
            return self.download(user_agents)

        first_url = f"https://kakuyomu.jp{first_link['href']}"
        print(f"[INFO] First url: {first_url}")

        # Download all episodes
        current_url = first_url
        chapters = []
        episode_num = 1

        while True:
            print(f"[LOG] Downloading episode {episode_num}")
            
            response = requests.get(current_url, headers=headers)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Get episode title
            episode_title_element = soup.select_one(".widget-episodeTitle.js-vertical-composition-item")
            episode_title = episode_title_element.text.strip() if episode_title_element else f"Episode {episode_num}"

            # Get episode content
            episode_content = soup.select_one(".widget-episodeBody.js-episode-body")
            if episode_content:
                # Create a chapter
                chapter = epub.EpubHtml(title=episode_title, file_name=f'chapter_{episode_num}.xhtml', lang='ja')
                chapter.content = f"<h3>{episode_title}</h3>{episode_content.prettify()}"
                book.add_item(chapter)
                chapters.append(chapter)  # Collect chapters for navigation
            
            # Get next episode link
            next_link = soup.select_one("#contentMain-readNextEpisode")
            if not next_link:
                print("[LOG] No more episodes found")
                break
                
            current_url = f"https://kakuyomu.jp{next_link['href']}"
            episode_num += 1

        # Add chapters to the Table of Contents
        book.toc = tuple(epub.Link(chapter.file_name, chapter.title, chapter.file_name) for chapter in chapters)

        # Add navigation files
        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())

        # Define spine (reading order)
        book.spine = ['nav'] + chapters

        # Save the book
        # make or check epub folder
        epub_folder = Path("epub")
        epub_folder.mkdir(exist_ok=True)
        epub_path = epub_folder / f"{title}.epub"
        epub.write_epub(epub_path, book)
        print(f"[INFO] Successfully saved to {epub_path}")
        return True

def main():
    parser = argparse.ArgumentParser(description='Download stories from Kakuyomu')
    parser.add_argument('mode', nargs='?', help='Operation mode (install)')
    parser.add_argument('book_id', nargs='?', help='Kakuyomu book ID')
    args = parser.parse_args()

    # Load user agents
    with open('userAgents.json', 'r') as f:
        user_agents = json.load(f)

    # Get book ID from arguments or input
    book_id = None
    if args.mode == 'install' and args.book_id:
        book_id = args.book_id
    else:
        book_id = input("Enter Kakuyomu book id: ").strip()

    print(f"Book ID: {book_id}")

    # Initialize and run
    app = KakuyomuApp(book_id=book_id)
    app.download(user_agents=user_agents)

if __name__ == "__main__":
    main()