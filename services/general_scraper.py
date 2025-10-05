import asyncio
import aiohttp
import aiofiles
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, quote
from pathlib import Path
import os
import zipfile
from datetime import datetime
import re
import logging
from typing import List, Dict
import hashlib

logger = logging.getLogger(__name__)

class GeneralScraper:
    def __init__(self):
        self.visited_urls = set()
        self.downloaded_files = {}  
        self.base_domain = None
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=60),
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': '*/*',
                'Accept-Language': 'en-US,en;q=0.9',
            }
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    def is_same_domain(self, url: str) -> bool:
        if not self.base_domain:
            return True
        parsed = urlparse(url)
        return parsed.netloc == self.base_domain or parsed.netloc.endswith(f'.{self.base_domain}')

    def clean_filename(self, filename: str) -> str:
        """Create a safe filename"""
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        filename = filename.replace(' ', '_')
        name, ext = os.path.splitext(filename)
        if len(name) > 50:
            name = name[:50]
        return name + ext

    def url_to_filename(self, url: str) -> str:
        """Convert URL to a unique filename"""
        parsed = urlparse(url)
        path = parsed.path
        
        if path and path != '/':
            filename = path.split('/')[-1]
            if not filename:
                filename = 'index'
        else:
            filename = 'index'
        
        if '.' not in filename:
            if 'css' in url.lower():
                filename += '.css'
            elif 'js' in url.lower() or 'javascript' in url.lower():
                filename += '.js'
            elif any(img in url.lower() for img in ['.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp']):
                ext = next((e for e in ['.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp'] if e in url.lower()), '.png')
                filename += ext
        
        url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
        name, ext = os.path.splitext(filename)
        unique_filename = f"{self.clean_filename(name)}_{url_hash}{ext}"
        
        return unique_filename

    def get_file_extension(self, url: str, content_type: str = None) -> str:
        parsed = urlparse(url)
        path = parsed.path
        
        if '.' in path:
            ext = path.split('.')[-1].lower().split('?')[0]  
            valid_exts = ['css', 'js', 'mjs', 'png', 'jpg', 'jpeg', 'gif', 'svg', 'ico', 
                         'woff', 'woff2', 'ttf', 'eot', 'otf', 'webp', 'avif']
            if ext in valid_exts:
                return f'.{ext}'
        
        if content_type:
            content_map = {
                'text/css': '.css',
                'application/javascript': '.js',
                'text/javascript': '.js',
                'application/x-javascript': '.js',
                'image/png': '.png',
                'image/jpeg': '.jpg',
                'image/jpg': '.jpg',
                'image/gif': '.gif',
                'image/svg+xml': '.svg',
                'image/webp': '.webp',
                'image/x-icon': '.ico',
                'font/woff': '.woff',
                'font/woff2': '.woff2',
                'font/ttf': '.ttf',
                'font/otf': '.otf',
                'application/font-woff': '.woff',
                'application/font-woff2': '.woff2',
                'application/x-font-ttf': '.ttf',
                'application/x-font-otf': '.otf',
            }
            return content_map.get(content_type.split(';')[0].strip(), '')
        
        return ''

    async def download_resource(self, url: str, base_path: Path, subfolder: str = "assets") -> str:
        """Download any resource (CSS, JS, images, fonts, etc.)"""
        try:
            if url in self.downloaded_files:
                return self.downloaded_files[url]
            
            if url.startswith('data:'):
                return url
                
            async with self.session.get(url, allow_redirects=True) as response:
                if response.status != 200:
                    logger.warning(f"Failed to download {url}: HTTP {response.status}")
                    return url
                
                content = await response.read()
                content_type = response.headers.get('content-type', '')
                
                ext = self.get_file_extension(url, content_type)
                filename = self.url_to_filename(url)
                
                if not any(filename.endswith(e) for e in ['.css', '.js', '.mjs', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', '.woff', '.woff2', '.ttf', '.eot', '.otf', '.webp']):
                    if ext:
                        filename += ext
                
                if filename.endswith(('.woff', '.woff2', '.ttf', '.eot', '.otf')):
                    relative_path = f"fonts/{filename}"
                elif filename.endswith(('.css',)):
                    relative_path = f"css/{filename}"
                elif filename.endswith(('.js', '.mjs')):
                    relative_path = f"js/{filename}"
                elif filename.endswith(('.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', '.webp', '.avif')):
                    relative_path = f"images/{filename}"
                else:
                    relative_path = f"{subfolder}/{filename}"
                
                file_path = base_path / relative_path
                file_path.parent.mkdir(parents=True, exist_ok=True)
                
                async with aiofiles.open(file_path, 'wb') as f:
                    await f.write(content)
                
                self.downloaded_files[url] = relative_path
                logger.info(f"Downloaded: {url} -> {relative_path}")
                return relative_path
                
        except Exception as e:
            logger.error(f"Failed to download {url}: {e}")
            return url

    async def process_css(self, css_content: str, css_url: str, base_path: Path) -> str:
        """Process CSS and download referenced resources"""
        url_pattern = r'url\(["\']?([^"\')]+)["\']?\)'
        
        async def replace_url_async(url):
            if url.startswith('data:'):
                return url
            
            absolute_url = urljoin(css_url, url)
            
            local_path = await self.download_resource(absolute_url, base_path)
            return local_path
        
        urls = re.findall(url_pattern, css_content)
        
        tasks = [replace_url_async(url) for url in urls]
        local_paths = await asyncio.gather(*tasks)
        
        url_mapping = dict(zip(urls, local_paths))
        
        def replacer(match):
            original_url = match.group(1)
            new_url = url_mapping.get(original_url, original_url)
            if new_url.startswith(('fonts/', 'images/', 'assets/')):
                new_url = f'../{new_url}'
            return f'url("{new_url}")'
        
        return re.sub(url_pattern, replacer, css_content)

    async def discover_pages(self, start_url: str) -> List[Dict[str, str]]:
        parsed_start = urlparse(start_url)
        self.base_domain = parsed_start.netloc
        
        pages = []
        to_visit = [start_url]
        visited = set()
        
        while to_visit and len(pages) < 100:
            url = to_visit.pop(0)
            if url in visited:
                continue
                
            visited.add(url)
            
            try:
                async with self.session.get(url) as response:
                    if response.status != 200:
                        continue
                        
                    if 'text/html' not in response.headers.get('content-type', ''):
                        continue
                    
                    content = await response.text()
                    soup = BeautifulSoup(content, 'html.parser')
                    
                    title = soup.find('title')
                    title_text = title.get_text().strip() if title else urlparse(url).path
                    
                    pages.append({
                        'url': url,
                        'title': title_text,
                        'path': urlparse(url).path or '/'
                    })
                    
                    for link in soup.find_all('a', href=True):
                        href = link['href']
                        absolute_url = urljoin(url, href)
                        
                        if (self.is_same_domain(absolute_url) and 
                            absolute_url not in visited and 
                            absolute_url not in to_visit and
                            not any(ext in absolute_url.lower() for ext in ['.pdf', '.doc', '.zip', '.exe']) and
                            '#' not in absolute_url):
                            to_visit.append(absolute_url)
                            
            except Exception as e:
                logger.error(f"Error discovering pages from {url}: {e}")
                
        return pages

    async def scrape_page(self, url: str, base_path: Path, page_name: str) -> str:
        try:
            async with self.session.get(url) as response:
                if response.status != 200:
                    raise Exception(f"HTTP {response.status}")
                
                content = await response.text()
                soup = BeautifulSoup(content, 'html.parser')

                for link in soup.find_all('link', rel='stylesheet'):
                    if link.get('href'):
                        css_url = urljoin(url, link['href'])
                        css_filename = await self.download_resource(css_url, base_path)

                        if not css_filename.startswith('http'):
                            try:
                                css_path = base_path / css_filename
                                if css_path.exists():
                                    async with aiofiles.open(css_path, 'r', encoding='utf-8') as f:
                                        css_content = await f.read()
                                    
                                    processed_css = await self.process_css(css_content, css_url, base_path)
                                    
                                    async with aiofiles.open(css_path, 'w', encoding='utf-8') as f:
                                        await f.write(processed_css)
                            except Exception as e:
                                logger.error(f"Failed to process CSS {css_url}: {e}")
                        
                        link['href'] = css_filename
                
                for style in soup.find_all('style'):
                    if style.string:
                        processed_style = await self.process_css(style.string, url, base_path)
                        style.string = processed_style
                
                for script in soup.find_all('script', src=True):
                    js_url = urljoin(url, script['src'])
                    js_filename = await self.download_resource(js_url, base_path)
                    script['src'] = js_filename
                
                for img in soup.find_all('img'):
                    if img.get('src'):
                        img_url = urljoin(url, img['src'])
                        img_filename = await self.download_resource(img_url, base_path)
                        img['src'] = img_filename
                    
                    if img.get('srcset'):
                        srcset_parts = []
                        for part in img['srcset'].split(','):
                            part = part.strip()
                            if ' ' in part:
                                img_part, descriptor = part.rsplit(' ', 1)
                                img_url = urljoin(url, img_part)
                                img_filename = await self.download_resource(img_url, base_path)
                                srcset_parts.append(f"{img_filename} {descriptor}")
                            else:
                                img_url = urljoin(url, part)
                                img_filename = await self.download_resource(img_url, base_path)
                                srcset_parts.append(img_filename)
                        img['srcset'] = ', '.join(srcset_parts)
                
                for source in soup.find_all('source'):
                    if source.get('srcset'):
                        src_url = urljoin(url, source['srcset'])
                        src_filename = await self.download_resource(src_url, base_path)
                        source['srcset'] = src_filename
                
                for media in soup.find_all(['video', 'audio', 'source']):
                    for attr in ['src', 'poster']:
                        if media.get(attr):
                            media_url = urljoin(url, media[attr])
                            media_filename = await self.download_resource(media_url, base_path)
                            media[attr] = media_filename
                
                for iframe in soup.find_all('iframe', src=True):
                    iframe_url = urljoin(url, iframe['src'])
                    if self.is_same_domain(iframe_url):
                        iframe_filename = await self.download_resource(iframe_url, base_path)
                        iframe['src'] = iframe_filename
                
                for tag in soup.find_all(style=True):
                    style_content = tag['style']
                    if 'url(' in style_content:
                        processed_style = await self.process_css(style_content, url, base_path)
                        tag['style'] = processed_style

                html_filename = f"{page_name}.html"
                html_path = base_path / html_filename
                
                async with aiofiles.open(html_path, 'w', encoding='utf-8') as f:
                    await f.write(str(soup.prettify()))
                
                return html_filename
                
        except Exception as e:
            logger.error(f"Failed to scrape {url}: {e}")
            raise

    async def scrape_site(self, url: str, scrape_mode: str, selected_pages: List[str] = None, job_id: str = None) -> Dict:
        try:
            if job_id is None:
                job_id = f"job_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(url) % 10000}"
            
            output_dir = Path(f"app/static/{job_id}")
            output_dir.mkdir(parents=True, exist_ok=True)
            
            parsed_url = urlparse(url)
            self.base_domain = parsed_url.netloc
            
            if scrape_mode == 'single_page':
                pages_to_scrape = [{'url': url, 'title': 'Main Page', 'path': '/'}]
            else:
                if selected_pages:
                    if len(selected_pages) > 25:
                        return {
                            'success': False,
                            'message': 'Maximum 25 pages allowed for multi-page scraping'
                        }
                    pages_to_scrape = [{'url': page_url, 'title': f'Page {i+1}', 'path': urlparse(page_url).path} 
                                    for i, page_url in enumerate(selected_pages)]
                else:
                    discovered = await self.discover_pages(url)
                    pages_to_scrape = discovered[:25]
            
            scraped_files = []
            
            for i, page in enumerate(pages_to_scrape):
                page_name = f"page_{i+1}" if len(pages_to_scrape) > 1 else "index"
                if i == 0:
                    page_name = "index"
                
                try:
                    html_file = await self.scrape_page(page['url'], output_dir, page_name)
                    scraped_files.append(html_file)
                    logger.info(f"Scraped page {i+1}/{len(pages_to_scrape)}: {page['url']}")
                except Exception as e:
                    logger.error(f"Failed to scrape page {page['url']}: {e}")

            zip_path = Path(f"app/static/{job_id}.zip")
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(output_dir):
                    for file in files:
                        file_path = Path(root) / file
                        arcname = file_path.relative_to(output_dir)
                        zipf.write(file_path, arcname)

            import shutil
            shutil.rmtree(output_dir, ignore_errors=True)
            
            return {
                'success': True,
                'message': f'Successfully scraped {len(scraped_files)} page(s)',
                'job_id': job_id,
                'file_path': str(zip_path),
                'download_url': f'/download/{job_id}'
            }
            
        except Exception as e:
            logger.error(f"General scraping failed: {e}")
            return {
                'success': False,
                'message': f'Scraping failed: {str(e)}'
            }