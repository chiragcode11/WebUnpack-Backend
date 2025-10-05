import asyncio
import aiohttp
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import os
import re
import logging

logger = logging.getLogger(__name__)

class BaseSiteSpider:
    def __init__(self, url, output_dir, scrape_mode="multi_page", selected_pages=None):
        self.start_url = url
        self.output_dir = output_dir
        self.scrape_mode = scrape_mode
        self.selected_pages = set(selected_pages) if selected_pages else None
        self.visited_pages = set()
        self.assets = set()
        self.base_domain = urlparse(url).netloc
        self.page_mapping = {}
        self.discovered_pages = []
    
    async def discover_pages(self):
        try:
            async with aiohttp.ClientSession() as session:
                await self.discover_page_links(session, self.start_url)
            return self.discovered_pages
        except Exception as e:
            logger.error(f"Failed to discover pages: {e}", exc_info=True)
            raise
    
    async def discover_page_links(self, session, url, depth=0):
        if url in self.visited_pages or depth > 3:
            return
        
        self.visited_pages.add(url)
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
            
            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status != 200:
                    logger.warning(f"Non-200 status for {url}: {response.status}")
                    return
                
                html_content = await response.text()
                soup = BeautifulSoup(html_content, 'html.parser')

                title_tag = soup.find('title')
                page_title = title_tag.get_text().strip() if title_tag else self.get_page_name_from_url(url)

                self.discovered_pages.append({
                    'url': url,
                    'title': page_title,
                    'path': self.get_clean_path(url)
                })

                internal_links = []
                for a in soup.find_all('a', href=True):
                    href = a.get('href')
                    if self.is_internal_link(href, url):
                        full_url = urljoin(url, href)
                        clean_url = full_url.split('#')[0].split('?')[0]
                        if clean_url not in internal_links and clean_url != url:
                            internal_links.append(clean_url)

                for link_url in internal_links[:10]:
                    if link_url not in self.visited_pages:
                        await self.discover_page_links(session, link_url, depth + 1)
        
        except asyncio.TimeoutError:
            logger.error(f"Timeout while discovering links on {url}")
        except aiohttp.ClientError as e:
            logger.error(f"Client error discovering links on {url}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error discovering links on {url}: {e}", exc_info=True)
    
    async def scrape(self):
        try:
            async with aiohttp.ClientSession() as session:
                if self.scrape_mode == "single_page":
                    await self.scrape_page(session, self.start_url)
                else:
                    if self.selected_pages:
                        for page_url in self.selected_pages:
                            await self.scrape_page(session, page_url)
                    else:
                        await self.scrape_page(session, self.start_url)
        except Exception as e:
            logger.error(f"Scraping failed: {e}", exc_info=True)
            raise
    
    async def scrape_page(self, session, url):
        if url in self.visited_pages:
            return

        if self.scrape_mode == "single_page" and url != self.start_url:
            return

        if self.selected_pages and url not in self.selected_pages:
            return

        if len(self.visited_pages) >= 150:
            logger.warning(f"Reached page limit (150), stopping scrape")
            return
        
        self.visited_pages.add(url)
        logger.info(f"Scraping page: {url} ({len(self.visited_pages)}/150)")
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
            
            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status != 200:
                    logger.warning(f"Failed to load {url}: Status {response.status}")
                    return
                
                html_content = await response.text()
                soup = BeautifulSoup(html_content, 'html.parser')
                
                relative_path = self.get_clean_path(url)
                full_file_path = os.path.join(self.output_dir, relative_path)
                
                os.makedirs(os.path.dirname(full_file_path), exist_ok=True)
                
                self.page_mapping[url] = relative_path
                
                processed_html = self.process_html_content(html_content, url)
                processed_html = self.remove_platform_badge(processed_html)
                
                with open(full_file_path, 'w', encoding='utf-8') as f:
                    f.write(processed_html)
                
                logger.info(f"Saved HTML: {relative_path} ({self.get_platform_name()} processing)")

                await self.download_assets(session, soup, url)
                
                if self.scrape_mode == "multi_page" and not self.selected_pages:
                    await self.scrape_internal_links(session, soup, url)
        
        except asyncio.TimeoutError:
            logger.error(f"Timeout while scraping {url}")
        except aiohttp.ClientError as e:
            logger.error(f"Client error scraping {url}: {e}")
        except IOError as e:
            logger.error(f"File IO error for {url}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error scraping {url}: {e}", exc_info=True)
    
    def get_page_name_from_url(self, url):
        try:
            parsed = urlparse(url)
            path = parsed.path.strip('/')
            
            if not path:
                return "Home"
            
            segments = path.split('/')
            last_segment = segments[-1] if segments else "Page"
            
            name = last_segment.replace('-', ' ').replace('_', ' ')
            return name.title()
        except Exception as e:
            logger.error(f"Error getting page name from {url}: {e}")
            return "Page"
    
    def get_clean_path(self, url):
        try:
            parsed = urlparse(url)
            path = parsed.path.strip('/')
            
            if not path:
                return 'index.html'
            
            segments = [seg for seg in path.split('/') if seg]
            
            if not segments:
                return 'index.html'
            
            if '.' in segments[-1] and not segments[-1].endswith('.html'):
                segments[-1] = segments[-1].split('.')[0] + '.html'
            elif not segments[-1].endswith('.html'):
                segments[-1] = segments[-1] + '.html'
            
            if len(segments) == 1:
                return segments[0]
            else:
                folder_path = '/'.join(segments[:-1])
                file_name = segments[-1]
                return f"{folder_path}/{file_name}"
        except Exception as e:
            logger.error(f"Error getting clean path for {url}: {e}")
            return 'index.html'
    
    async def download_assets(self, session, soup, base_url):
        try:
            css_links = [link.get('href') for link in soup.find_all('link', rel='stylesheet') if link.get('href')]
            js_links = [script.get('src') for script in soup.find_all('script', src=True)]
            img_links = [img.get('src') for img in soup.find_all('img', src=True)]
            
            style_tags = soup.find_all('style')
            font_urls = []
            for style in style_tags:
                if style.string:
                    font_urls.extend(re.findall(r'url\(["\']?([^"\']+\.(?:woff2?|ttf|eot|otf))["\']?\)', style.string))
            
            all_assets = css_links + js_links + img_links + font_urls
            
            for asset_url in all_assets:
                if asset_url and asset_url not in self.assets:
                    self.assets.add(asset_url)
                    await self.download_asset(session, asset_url, base_url)
        except Exception as e:
            logger.error(f"Error downloading assets from {base_url}: {e}", exc_info=True)
    
    async def scrape_internal_links(self, session, soup, base_url):
        try:
            internal_links = []
            for a in soup.find_all('a', href=True):
                href = a.get('href')
                if self.is_internal_link(href, base_url):
                    full_url = urljoin(base_url, href)
                    clean_url = full_url.split('#')[0].split('?')[0]
                    if clean_url not in internal_links:
                        internal_links.append(clean_url)
            
            logger.info(f"Found {len(internal_links)} internal links to scrape")
            
            for link_url in internal_links:
                if link_url not in self.visited_pages:
                    await self.scrape_page(session, link_url)
        except Exception as e:
            logger.error(f"Error scraping internal links from {base_url}: {e}", exc_info=True)
    
    async def download_asset(self, session, asset_url, base_url):
        try:
            if asset_url.startswith('//'):
                full_url = 'https:' + asset_url
            elif asset_url.startswith('/'):
                full_url = f"https://{self.base_domain}{asset_url}"
            elif asset_url.startswith('http'):
                full_url = asset_url
            else:
                full_url = urljoin(base_url, asset_url)
            
            async with session.get(full_url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status == 200:
                    content = await response.read()
                    
                    if asset_url.startswith('//'):
                        local_path = asset_url[2:]
                    elif asset_url.startswith('/'):
                        local_path = asset_url[1:]
                    elif asset_url.startswith('http'):
                        parsed = urlparse(asset_url)
                        local_path = f"{parsed.netloc}{parsed.path}"
                    else:
                        local_path = asset_url
                    
                    full_local_path = os.path.join(self.output_dir, local_path)
                    os.makedirs(os.path.dirname(full_local_path), exist_ok=True)
                    
                    with open(full_local_path, 'wb') as f:
                        f.write(content)
                    
                    logger.debug(f"Saved asset: {local_path}")
                else:
                    logger.warning(f"Failed to download asset {asset_url}: Status {response.status}")
        
        except asyncio.TimeoutError:
            logger.error(f"Timeout downloading asset {asset_url}")
        except aiohttp.ClientError as e:
            logger.error(f"Client error downloading asset {asset_url}: {e}")
        except IOError as e:
            logger.error(f"File IO error saving asset {asset_url}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error downloading asset {asset_url}: {e}", exc_info=True)
    
    def is_internal_link(self, link, current_url):
        try:
            if not link or link.startswith(('mailto:', 'tel:', '#', 'javascript:')):
                return False
            
            external_domains = ['facebook.com', 'twitter.com', 'instagram.com', 'linkedin.com', 
                               'youtube.com', 'google.com', 'maps.google.com']
            
            if link.startswith('http'):
                current_domain = urlparse(current_url).netloc
                link_domain = urlparse(link).netloc
                
                if any(domain in link_domain for domain in external_domains):
                    return False
                    
                return current_domain == link_domain
            return True
        except Exception as e:
            logger.error(f"Error checking if link is internal {link}: {e}")
            return False
    
    def get_relative_path(self, from_path, to_path):
        try:
            from_dir = os.path.dirname(from_path)
            to_dir = os.path.dirname(to_path)
            
            if from_dir == to_dir:
                return os.path.basename(to_path)
            
            from_parts = from_dir.split('/') if from_dir else []
            to_parts = to_dir.split('/') if to_dir else []
            
            common_length = 0
            for i in range(min(len(from_parts), len(to_parts))):
                if from_parts[i] == to_parts[i]:
                    common_length += 1
                else:
                    break
            
            up_levels = len(from_parts) - common_length
            down_path = '/'.join(to_parts[common_length:])
            
            relative_parts = ['..'] * up_levels
            if down_path:
                relative_parts.append(down_path)
            relative_parts.append(os.path.basename(to_path))
            
            return '/'.join(relative_parts) if relative_parts else os.path.basename(to_path)
        except Exception as e:
            logger.error(f"Error calculating relative path from {from_path} to {to_path}: {e}")
            return to_path
    
    def process_html_content(self, html, base_url):
        try:
            domain = urlparse(base_url).netloc
            html = re.sub(rf'https?://{re.escape(domain)}/', './', html)
            html = re.sub(rf'https?://{re.escape(domain)}', '.', html)
            
            soup = BeautifulSoup(html, 'html.parser')
            current_page_path = self.get_clean_path(base_url)
            
            for link in soup.find_all('a', href=True):
                href = link['href']
                
                if href.startswith(('mailto:', 'tel:', 'javascript:')):
                    continue
                
                if href.startswith('#'):
                    continue

                if href.startswith('/'):
                    if href == '/' or href == '':
                        link['href'] = self.get_relative_path(current_page_path, 'index.html')
                    else:
                        target_url = urljoin(base_url, href)
                        target_path = self.get_clean_path(target_url)
                        link['href'] = self.get_relative_path(current_page_path, target_path)
                
                elif href.startswith(('http://', 'https://')):
                    link_domain = urlparse(href).netloc
                    base_domain = urlparse(base_url).netloc
                    
                    if link_domain == base_domain:
                        target_path = self.get_clean_path(href)
                        link['href'] = self.get_relative_path(current_page_path, target_path)
            
            return str(soup)
        except Exception as e:
            logger.error(f"Error processing HTML content for {base_url}: {e}", exc_info=True)
            return html
    
    def remove_platform_badge(self, html_content):
        raise NotImplementedError("Subclasses must implement remove_platform_badge")
    
    def get_platform_name(self):
        raise NotImplementedError("Subclasses must implement get_platform_name")