import asyncio
from typing import Dict, List, Optional
import logging
from datetime import datetime
import uuid
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

from .general_scraper import GeneralScraper
from .html_to_react_service import HTMLToReactService

class ReactifyService:
    def __init__(self, gemini_api_key: str):
        self.html_to_react_service = HTMLToReactService(gemini_api_key)
        self.logger = logging.getLogger(__name__)

    async def discover_pages_for_reactify(self, url: str) -> Dict:
        try:
            async with GeneralScraper() as scraper:
                pages = await scraper.discover_pages(url)
                
                enhanced_pages = []
                for page in pages[:20]:
                    enhanced_page = {
                        'url': page['url'],
                        'title': page['title'],
                        'path': page['path'],
                        'preview_image': await self._generate_preview_placeholder(page['url']),
                        'complexity_score': self._estimate_page_complexity(page),
                        'conversion_time_estimate': self._estimate_conversion_time(page)
                    }
                    enhanced_pages.append(enhanced_page)
                
                return {
                    'success': True,
                    'pages': enhanced_pages,
                    'total_discovered': len(pages),
                    'recommended_pages': self._get_recommended_pages(enhanced_pages)
                }
        except Exception as e:
            self.logger.error(f"Page discovery failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'pages': []
            }

    async def convert_page_to_react(self, page_url: str, conversion_options: Dict, job_id: str = None) -> Dict:
        if not job_id:
            job_id = f"reactify_{uuid.uuid4().hex[:12]}"
        
        try:
            self.logger.info(f"Starting React conversion for {page_url} with job {job_id}")
            
            page_content = await self._scrape_single_page(page_url)
            
            conversion_result = await self.html_to_react_service.convert_html_to_react(
                page_content['html'],
                page_content['css'],
                job_id
            )
            
            if conversion_result['success']:
                return {
                    'success': True,
                    'job_id': job_id,
                    'conversion_result': conversion_result,
                    'download_info': {
                        'ready': True,
                        'download_url': f'/download/{job_id}_react',
                        'file_size_mb': conversion_result['final_project'].get('file_size_mb', 0),
                        'components_generated': conversion_result['ai_analysis'].get('component_count', 0)
                    }
                }
            else:
                return conversion_result
                
        except Exception as e:
            self.logger.error(f"React conversion failed for {page_url}: {e}")
            return {
                'success': False,
                'job_id': job_id,
                'error': str(e)
            }

    async def get_conversion_status(self, job_id: str) -> Dict:
        return await self.html_to_react_service.get_conversion_status(job_id)

    async def _scrape_single_page(self, page_url: str) -> Dict:
        async with GeneralScraper() as scraper:
            parsed_url = urlparse(page_url)
            scraper.base_domain = parsed_url.netloc
            
            async with scraper.session.get(page_url) as response:
                if response.status != 200:
                    raise Exception(f"Failed to fetch page: HTTP {response.status}")
                
                html_content = await response.text()
                
                css_content = ""
                soup = BeautifulSoup(html_content, 'html.parser')
                
                for link in soup.find_all('link', rel='stylesheet'):
                    if link.get('href'):
                        css_url = urljoin(page_url, link['href'])
                        if scraper.is_same_domain(css_url):
                            try:
                                async with scraper.session.get(css_url) as css_response:
                                    if css_response.status == 200:
                                        css_chunk = await css_response.text()
                                        css_content += f"\n/* {css_url} */\n{css_chunk}"
                            except Exception:
                                continue
                
                return {
                    'html': html_content,
                    'css': css_content,
                    'url': page_url
                }

    async def _generate_preview_placeholder(self, url: str) -> str:
        return f"https://api.screenshotmachine.com/capture?url={url}&dimension=300x200"

    def _estimate_page_complexity(self, page: Dict) -> int:
        title_length = len(page.get('title', ''))
        path_segments = len(page.get('path', '/').split('/'))
        
        complexity = min(title_length // 10 + path_segments, 10)
        return max(complexity, 1)

    def _estimate_conversion_time(self, page: Dict) -> str:
        complexity = self._estimate_page_complexity(page)
        
        if complexity <= 3:
            return "1-2 minutes"
        elif complexity <= 6:
            return "2-4 minutes"
        else:
            return "4-6 minutes"

    def _get_recommended_pages(self, pages: List[Dict]) -> List[Dict]:
        sorted_pages = sorted(pages, key=lambda p: p['complexity_score'])
        return sorted_pages[:3]
