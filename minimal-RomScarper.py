""" mininmal Firmware Rom scarper from https://firmwarefile.com/ database (we are scarpping in legal way only downloadable roms) 
  maybe we gonna enhance this piece to include more firmware websites to create bulk link exifliration and integrate it with ffdm & devtical core later 
"""
import requests
from bs4 import BeautifulSoup
import argparse
import os
import re
import time
import sys
from urllib.parse import urljoin

class ROMScraper:
    def __init__(self, base_delay=1):
        self.session = requests.Session()
        self.base_delay = base_delay
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def intelligent_delay(self):
        """Add delay to be respectful to the server"""
        time.sleep(self.base_delay)
    
    def get_max_page(self, brand):
        """Extract maximum page number from pagination"""
        url = f"https://firmwarefile.com/?s={brand}"
        try:
            response = self.session.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            last_page_element = soup.find('a', {'aria-label': 'Last Page'})
            if last_page_element and 'href' in last_page_element.attrs:
                last_page_url = last_page_element['href']
                page_match = re.search(r'/page/(\d+)\?s=', last_page_url)
                if page_match:
                    return int(page_match.group(1))
            
            page_links = soup.select('a.page.larger, a.page')
            page_numbers = []
            for link in page_links:
                if 'href' in link.attrs:
                    page_match = re.search(r'/page/(\d+)\?s=', link['href'])
                    if page_match:
                        page_numbers.append(int(page_match.group(1)))
            
            return max(page_numbers) if page_numbers else 1
            
        except Exception as e:
            print(f"Error getting max page for {brand}: {e}")
            return 1
    
    def extract_device_links(self, url):
        """Extract all device links from a search results page"""
        device_links = []
        try:
            response = self.session.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            device_elements = soup.select('div.fa-grid-post-column-bg h3.fa-grid-post-heading a')
            
            for element in device_elements:
                if 'href' in element.attrs:
                    device_links.append({
                        'url': element['href'],
                        'name': element.get_text(strip=True)
                    })
            
            return device_links
            
        except Exception as e:
            print(f"Error extracting device links from {url}: {e}")
            return []
    
    def extract_download_links(self, device_url):
        """Extract Google Drive, MediaFire, and Mega.nz download links from device page"""
        try:
            response = self.session.get(device_url)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            download_links = []
            all_links = soup.find_all('a', href=True)
            
            for link in all_links:
                href = link['href']
                
                # Google Drive links
                if 'drive.google.com' in href and '/file/d/' in href:
                    file_id_match = re.search(r'/file/d/([a-zA-Z0-9_-]+)', href)
                    if file_id_match:
                        file_id = file_id_match.group(1)
                        direct_download = f"https://drive.google.com/uc?export=download&id={file_id}"
                        
                        file_name = self.extract_file_name(soup, link)
                        
                        download_links.append({
                            'view_url': href,
                            'download_url': direct_download,
                            'file_name': file_name,
                            'source': device_url,
                            'type': 'google_drive'
                        })
                        
                        print(f"URL: {href}")
                
                # MediaFire links
                elif 'mediafire.com' in href:
                    file_name = self.extract_file_name(soup, link)
                    
                    download_links.append({
                        'view_url': href,
                        'download_url': href,  # MediaFire requires special handling
                        'file_name': file_name,
                        'source': device_url,
                        'type': 'mediafire'
                    })
                    
                    print(f"URL: {href}")
                
                # Mega.nz links
                elif 'mega.nz' in href or 'mega.co.nz' in href:
                    file_name = self.extract_file_name(soup, link)
                    
                    download_links.append({
                        'view_url': href,
                        'download_url': href,  # Mega.nz requires special handling
                        'file_name': file_name,
                        'source': device_url,
                        'type': 'mega_nz'
                    })
                    
                    print(f"URL: {href}")
            
            return download_links
            
        except Exception as e:
            print(f"Error extracting download links from {device_url}: {e}")
            return []
    
    def extract_mediafire_direct_url(self, mediafire_url):
        """Extract direct download URL from MediaFire page"""
        try:
            response = self.session.get(mediafire_url)
            response.raise_for_status()
            
            # Updated pattern for MediaFire HTML structure
            download_patterns = [
                r'<a class="input popsok" aria-label="Download file" href="([^"]+)"',
                r'download_link.*?href="([^"]+)"',
                r'href="(https://download[^"]+mediafire.com[^"]+)"'
            ]
            
            for pattern in download_patterns:
                match = re.search(pattern, response.text, re.IGNORECASE)
                if match:
                    return match.group(1)
            
            # Alternative approach using BeautifulSoup
            soup = BeautifulSoup(response.content, 'html.parser')
            download_button = soup.find('a', {'aria-label': 'Download file'})
            if download_button and download_button.get('href'):
                return download_button['href']
                
            print(f"Could not find direct download URL for MediaFire link: {mediafire_url}")
            return None
            
        except Exception as e:
            print(f"Error extracting MediaFire direct URL: {e}")
            return None
    
    def extract_file_name(self, soup, download_link):
        """Extract appropriate filename from the page content"""
        try:
            article_block = soup.find('div', id='article-block')
            if article_block:
                file_name_elements = article_block.find_all(['h2', 'strong'])
                for element in file_name_elements:
                    text = element.get_text(strip=True)
                    if 'Stock Firmware' in text or 'Flash File' in text:
                        clean_name = re.sub(r'[<>:"/\\|?*]', '_', text)
                        return f"{clean_name}.zip"
            
            title = soup.find('title')
            if title:
                clean_name = re.sub(r'[<>:"/\\|?*]', '_', title.get_text(strip=True))
                return f"{clean_name}.zip"
                
            return "firmware_download.zip"
            
        except Exception as e:
            print(f"Error extracting filename: {e}")
            return "firmware_download.zip"
    
    def download_file(self, download_info, output_dir):
        """Download a file based on its type"""
        try:
            os.makedirs(output_dir, exist_ok=True)
            file_path = os.path.join(output_dir, download_info['file_name'])
            
            if os.path.exists(file_path):
                print(f"File already exists: {download_info['file_name']}")
                return True
            
            print(f"Downloading: {download_info['file_name']}")
            
            # Handle different download types
            if download_info['type'] == 'google_drive':
                return self.download_google_drive(download_info, file_path)
            elif download_info['type'] == 'mediafire':
                return self.download_mediafire(download_info, file_path)
            elif download_info['type'] == 'mega_nz':
                print(f"Mega.nz download requires manual handling: {download_info['view_url']}")
                return False
            else:
                print(f"Unknown download type: {download_info['type']}")
                return False
                
        except Exception as e:
            print(f"Error downloading {download_info['file_name']}: {e}")
            return False
    
    def download_google_drive(self, download_info, file_path):
        """Download from Google Drive"""
        try:
            response = self.session.get(download_info['download_url'], stream=True)
            response.raise_for_status()
            
            # Handle Google Drive virus scan warning
            content = response.content
            if b"Google Drive - Virus scan warning" in content:
                warning_soup = BeautifulSoup(content, 'html.parser')
                form = warning_soup.find('form')
                if form and 'action' in form.attrs:
                    confirm_url = urljoin(download_info['download_url'], form['action'])
                    response = self.session.get(confirm_url, stream=True)
                    response.raise_for_status()
            
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            print(f"Successfully downloaded: {download_info['file_name']}")
            return True
            
        except Exception as e:
            print(f"Error downloading Google Drive file: {e}")
            return False
    
    def download_mediafire(self, download_info, file_path):
        """Download from MediaFire"""
        try:
            # Get direct download URL first
            direct_url = self.extract_mediafire_direct_url(download_info['view_url'])
            if not direct_url:
                return False
            
            response = self.session.get(direct_url, stream=True)
            response.raise_for_status()
            
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            print(f"Successfully downloaded: {download_info['file_name']}")
            return True
            
        except Exception as e:
            print(f"Error downloading MediaFire file: {e}")
            return False
    
    def scrape_brand(self, brand, output_dir="downloads", max_pages=None):
        """Main method to scrape all ROMs for a brand"""
        all_devices = []
        all_downloads = []
        
        if max_pages is None:
            max_pages = self.get_max_page(brand)
        
        print(f"Scraping {brand}, found {max_pages} pages")
        
        for page in range(1, max_pages + 1):
            if page == 1:
                url = f"https://firmwarefile.com/?s={brand}"
            else:
                url = f"https://firmwarefile.com/page/{page}?s={brand}"
            
            print(f"Scraping page {page}: {url}")
            devices = self.extract_device_links(url)
            all_devices.extend(devices)
            self.intelligent_delay()
        
        print(f"Found {len(all_devices)} devices, extracting download links...")
        
        for device in all_devices:
            print(f"Processing: {device['name']}")
            downloads = self.extract_download_links(device['url'])
            all_downloads.extend(downloads)
            self.intelligent_delay()
        
        print(f"Found {len(all_downloads)} download links, starting downloads...")
        
        successful_downloads = 0
        for download in all_downloads:
            if self.download_file(download, output_dir):
                successful_downloads += 1
            self.intelligent_delay()
        
        print(f"Download completed: {successful_downloads}/{len(all_downloads)} files successful")
        
        return {
            'devices_found': len(all_devices),
            'downloads_found': len(all_downloads),
            'successful_downloads': successful_downloads
        }

def main():
    parser = argparse.ArgumentParser(description='ROM File Auto-Downloader')
    parser.add_argument('brand', help='Device brand to search for (e.g., realme)')
    parser.add_argument('-o', '--output', default='downloads', 
                       help='Output directory for downloads')
    parser.add_argument('-p', '--pages', type=int, 
                       help='Maximum pages to scrape (auto-detected if not specified)')
    parser.add_argument('-d', '--delay', type=float, default=1,
                       help='Delay between requests in seconds')
    
    args = parser.parse_args()
    
    scraper = ROMScraper(base_delay=args.delay)
    results = scraper.scrape_brand(args.brand, args.output, args.pages)
    
    print("\n=== Summary ===")
    print(f"Brand: {args.brand}")
    print(f"Devices found: {results['devices_found']}")
    print(f"Download links found: {results['downloads_found']}")
    print(f"Successful downloads: {results['successful_downloads']}")
    print(f"Files saved to: {args.output}")

if __name__ == "__main__":
    main()
