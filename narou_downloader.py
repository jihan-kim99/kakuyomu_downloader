import requests
from bs4 import BeautifulSoup
import json
import argparse
from typing import Optional, List, Callable
from pathlib import Path
import random
from ebooklib import epub
import bs4

class NarouDownloader:
    def __init__(
        self,
        novel_id: Optional[str] = None,
        log: Optional[Callable[[str], None]] = None,
        output_dir: Optional[Path] = None,
    ):
        self.log = log or print
        self.novel_id = novel_id
        self.output_dir = Path(output_dir) if output_dir else Path("epub")

        self.log("Initializing Narou Downloader...")
        if novel_id is None:
            self.log("Novel ID not found")
        else:
            self.log(f"Novel ID: {novel_id}")

    def get_first_episode_url(self, novel_id: Optional[str] = None) -> Optional[str]:
        novel_id = novel_id or self.novel_id
        if not novel_id:
            self.log("Novel id not set.")
            return None
        return f"https://ncode.syosetu.com/{novel_id}/1/"

    def download(
        self,
        user_agents: List[str],
        novel_id: Optional[str] = None,
        output_dir: Optional[Path] = None,
    ) -> bool:
        novel_id = novel_id or self.novel_id
        if not novel_id:
            self.log("Novel id not set.")
            return False

        current_url = self.get_first_episode_url(novel_id)
        self.log(f"[INFO] First episode URL: {current_url}")

        user_agent = random.choice(user_agents)
        self.log(f"[INFO] Using User-Agent: {user_agent}")
        headers = {'User-Agent': user_agent}

        chapters = []
        episode_num = 1
        novel_title = None
        book = epub.EpubBook()
        book.set_identifier(novel_id)
        book.set_language('ja')
        book.add_author("Unknown Author")

        while current_url:
            self.log(f"[LOG] Downloading episode {episode_num}: {current_url}")
            try:
                response = requests.get(current_url, headers=headers, timeout=30)
                response.raise_for_status()
            except requests.exceptions.RequestException as exc:
                self.log(f"[ERROR] Request failed for {current_url}: {exc}")
                return False

            soup = BeautifulSoup(response.text, 'html.parser')

            # Get novel title from the first episode only
            if episode_num == 1:
                title_tag = soup.find('title')
                if title_tag and title_tag.text:
                    novel_title_candidate = title_tag.text.strip()
                    if ' - ' in novel_title_candidate:
                        novel_title_candidate = novel_title_candidate.split(' - ')[0]
                    self.log(f"[INFO] Novel title: {novel_title_candidate}")
                    novel_title = novel_title_candidate
                else:
                    self.log("[ERROR] Could not find novel title")
                    return False
                book.set_title(novel_title)

            # Get episode title
            episode_title_elem = soup.select_one('body > div.l-container > main > article > h1')
            if not episode_title_elem:
                episode_title_elem = soup.select_one('h1')
            episode_title = episode_title_elem.text.strip() if episode_title_elem else f"Episode {episode_num}"

            # Get episode content (list of <p> tags)
            content_div = soup.select_one('body > div.l-container > main > article > div.p-novel__body')
            if not content_div:
                content_div = soup.find('div', class_='novel_view')
            if not content_div:
                self.log(f"[ERROR] Could not find content for episode {episode_num}")
                break
            if isinstance(content_div, bs4.element.Tag):
                paragraphs = content_div.find_all('p')
                content_html = ''.join([f'<p>{p.text}</p>' for p in paragraphs])
            else:
                self.log(f"[ERROR] content_div is not a Tag for episode {episode_num}")
                content_html = str(content_div)

            # Create a chapter
            chapter = epub.EpubHtml(title=episode_title, file_name=f'chapter_{episode_num}.xhtml', lang='ja')
            chapter.content = f"<h3>{episode_title}</h3>{content_html}"
            book.add_item(chapter)
            chapters.append(chapter)

            # Find next episode link
            next_link = None
            if episode_num == 1:
                next_link = soup.select_one('body > div.l-container > main > article > div:nth-of-type(1) > a:nth-of-type(2)')
                self.log("[DEBUG] First episode: trying next button a:nth-of-type(2)")
            else:
                next_link = soup.select_one('body > div.l-container > main > article > div:nth-of-type(1) > a:nth-of-type(3)')
                self.log("[DEBUG] Subsequent episode: trying next button a:nth-of-type(3)")
                if not next_link:
                    self.log("[DEBUG] Fallback: trying next button a:nth-of-type(2)")
                    next_link = soup.select_one('body > div.l-container > main > article > div:nth-of-type(1) > a:nth-of-type(2)')
            if not next_link or not next_link.get('href'):
                self.log("[LOG] No more episodes found")
                break
            next_href = str(next_link['href'])
            if next_href.startswith('http'):
                current_url = next_href
            else:
                current_url = f"https://ncode.syosetu.com{next_href}"
            episode_num += 1

        # Add chapters to the Table of Contents
        book.toc = [epub.Link(chapter.file_name, chapter.title, chapter.file_name) for chapter in chapters]
        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())
        book.spine = ['nav'] + chapters

        # Save the book
        target_dir = Path(output_dir) if output_dir else self.output_dir
        target_dir.mkdir(parents=True, exist_ok=True)
        safe_title = novel_title or novel_id
        epub_path = target_dir / f"{safe_title}.epub"
        epub.write_epub(str(epub_path), book)
        self.log(f"[INFO] Successfully saved to {epub_path}")
        return True

def main():
    parser = argparse.ArgumentParser(description='Download stories from Syosetu (Narou)')
    parser.add_argument('mode', nargs='?', help='Operation mode (install)')
    parser.add_argument('novel_id', nargs='?', help='Syosetu novel ID (e.g., n5511kh)')
    args = parser.parse_args()

    # Load user agents
    with open('userAgents.json', 'r') as f:
        user_agents = json.load(f)

    # Get novel ID from arguments or input
    novel_id = None
    if args.mode == 'install' and args.novel_id:
        novel_id = args.novel_id
    else:
        novel_id = input("Enter Syosetu novel id: ").strip()

    print(f"Novel ID: {novel_id}")

    # Initialize and run
    app = NarouDownloader(novel_id=novel_id, log=print)
    app.download(user_agents=user_agents)

if __name__ == "__main__":
    main()
