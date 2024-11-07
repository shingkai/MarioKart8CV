import os
import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, unquote
import time
import hashlib


def create_directory(path):
    """Create directory if it doesn't exist"""
    if not os.path.exists(path):
        os.makedirs(path)


def clean_filename(filename):
    """Clean filename of invalid characters"""
    # Decode URL-encoded characters first
    filename = unquote(filename)
    # Remove or replace invalid characters
    return re.sub(r'[<>:"/\\|?*]', '_', filename)


def get_unique_filename(filepath):
    """Generate unique filename if file already exists"""
    directory = os.path.dirname(filepath)
    filename = os.path.basename(filepath)
    name, ext = os.path.splitext(filename)

    counter = 1
    while os.path.exists(filepath):
        filepath = os.path.join(directory, f"{name}_{counter}{ext}")
        counter += 1

    return filepath


def download_image(url, filepath):
    """Download image from URL"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            with open(filepath, 'wb') as f:
                f.write(response.content)
            return True
        print(f"Failed to download {url} with status code {response.status_code}")
        return False
    except Exception as e:
        print(f"Error downloading {url}: {str(e)}")
        return False


def get_category_from_element(element):
    """Find the nearest category heading for an element"""
    # Look for the nearest h2 or h3 heading above this element
    prev = element.find_previous(['h2', 'h3'])
    if prev:
        # Get text from the span inside the heading (typical wiki structure)
        span = prev.find('span')
        if span:
            return clean_filename(span.get_text().strip())
        return clean_filename(prev.get_text().strip())
    return "uncategorized"


def scrape_mario_wiki_gallery(url):
    """Scrape images from MarioWiki gallery page"""
    try:
        print(f"Fetching content from {url}")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        html_content = response.text

        soup = BeautifulSoup(html_content, 'html.parser')

        # Create base output directory
        base_output_dir = "mario_kart_images"
        create_directory(base_output_dir)

        # Keep track of downloaded URLs to avoid duplicates
        downloaded_urls = set()
        categories = {}

        # Find gallery items
        for gallery_item in soup.find_all(['div', 'li'], class_=['gallerybox', 'gallery']):
            # Get category for this item
            category = get_category_from_element(gallery_item)
            if category not in categories:
                categories[category] = []

            # Find image link
            gallery_link = gallery_item.find('a', class_='image')
            if gallery_link:
                img = gallery_link.find('img')
                if img:
                    # Get the full-size image URL
                    src = img.get('src', '')
                    if src:
                        if src.startswith('//'):
                            src = 'https:' + src
                        elif not src.startswith('http'):
                            src = urljoin(url, src)

                        # Convert thumbnail URL to full-size URL
                        full_size_url = re.sub(r'/thumb/|/\d+px-', '/', src)
                        full_size_url = re.sub(r'/\d+x\d+/', '/', full_size_url)
                        if '/thumb/' in src:
                            full_size_url = '/'.join(full_size_url.split('/')[:-1])

                        # Skip if we've already seen this URL
                        if full_size_url in downloaded_urls:
                            continue

                        downloaded_urls.add(full_size_url)

                        # Get caption from gallery text or image alt
                        caption = None
                        caption_elem = gallery_item.find('div', class_='gallerytext')
                        if caption_elem:
                            caption = caption_elem.get_text().strip()
                        if not caption:
                            caption = img.get('alt', '')

                        categories[category].append({
                            'url': full_size_url,
                            'caption': caption
                        })

        # Download images by category
        total_downloaded = 0
        for category, images in categories.items():
            if images:
                # Create category directory
                category_dir = os.path.join(base_output_dir, category)
                create_directory(category_dir)

                print(f"\nDownloading images for category: {category}")
                for idx, img_data in enumerate(images, 1):
                    # Generate base filename from caption or URL
                    if img_data['caption']:
                        base_filename = clean_filename(img_data['caption'])
                    else:
                        base_filename = f"image_{idx}"

                    # Get extension from URL
                    ext = os.path.splitext(img_data['url'])[1]
                    if not ext:
                        ext = '.png'

                    # Create filepath and ensure it's unique
                    filepath = os.path.join(category_dir, f"{base_filename}{ext}")
                    filepath = get_unique_filename(filepath)

                    print(f"Downloading {idx}/{len(images)}: {os.path.basename(filepath)}")
                    if download_image(img_data['url'], filepath):
                        total_downloaded += 1
                        time.sleep(0.01)

        print(f"\nDownload complete! Downloaded {total_downloaded} images across {len(categories)} categories.")

    except requests.exceptions.RequestException as e:
        print(f"Error fetching the webpage: {str(e)}")
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        raise e


if __name__ == "__main__":
    url = input("Enter the wiki page URL to scrape: ")
    scrape_mario_wiki_gallery(url)