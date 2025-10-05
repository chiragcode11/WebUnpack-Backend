import uuid
import os
from scraper.framer_spider import FramerSpider
from scraper.webflow_spider import WebflowSpider
from scraper.wordpress_spider import WordPressSpider
from scraper.wix_spider import WixSpider
from scraper.shopify_spider import ShopifySpider
from scraper.bolt_spider import BoltSpider
from scraper.lovable_spider import LovableSpider
from scraper.gumroad_spider import GumroadSpider
from scraper.replit_spider import ReplitSpider
from scraper.squarespace_spider import SquarespaceSpider
from scraper.notion_spider import NotionSpider
from scraper.rocket_spider import RocketSpider
from services.general_scraper import GeneralScraper
from services.file_service import FileService


class ScraperService:
    def __init__(self):
        self.file_service = FileService()
        self.file_service.ensure_static_dir()
    
    async def discover_pages(self, url: str, site_type: str) -> dict:
        print(f"Discovering pages for URL: {url} (Site type: {site_type})")
        
        try:
            if site_type == "general":
                async with GeneralScraper() as scraper:
                    pages = await scraper.discover_pages(url)
                    return {
                        "success": True,
                        "message": f"Found {len(pages)} pages",
                        "pages": pages
                    }
            
            spider_map = {
                "framer": FramerSpider,
                "webflow": WebflowSpider,
                "wordpress": WordPressSpider,
                "wix": WixSpider,
                "shopify": ShopifySpider,
                "bolt": BoltSpider,
                "lovable": LovableSpider,
                "gumroad": GumroadSpider,
                "replit": ReplitSpider,
                "squarespace": SquarespaceSpider,
                "notion": NotionSpider,
                "rocket": RocketSpider
            }
            
            if site_type not in spider_map:
                raise ValueError(f"Unsupported site type: {site_type}")
            
            spider_class = spider_map[site_type]
            spider = spider_class(url, "", "multi_page")  
            
            discovered_pages = await spider.discover_pages()

            return {
                "success": True,
                "message": f"Found {len(discovered_pages)} pages",
                "pages": discovered_pages
            }
        
        except Exception as e:
            return {
                "success": False,
                "message": f"Page discovery failed: {str(e)}",
                "pages": []
            }
    
    async def scrape_site(self, url: str, site_type: str, scrape_mode: str = "multi_page", selected_pages: list = None, job_id: str = None) -> dict:
        if job_id is None:
            job_id = str(uuid.uuid4())
        
        output_dir = f"app/static/{job_id}"
        os.makedirs(output_dir, exist_ok=True)
        
        try:
            if site_type == "general":
                async with GeneralScraper() as scraper:
                    scraper.job_id = job_id
                    result = await scraper.scrape_site(url, scrape_mode, selected_pages, job_id)
                    if result.get("success"):
                        page_count = len(selected_pages) if selected_pages else "all"
                        mode_text = "single page" if scrape_mode == "single_page" else f"{page_count} pages"
                        
                        return {
                            "success": True,
                            "message": f"Successfully scraped {mode_text} from general website",
                            "download_url": f"/download/{job_id}",
                            "file_path": f"app/static/{job_id}.zip",
                            "job_id": job_id
                        }
                    else:
                        return result

            spider_map = {
                "framer": FramerSpider,
                "webflow": WebflowSpider,
                "wordpress": WordPressSpider,
                "wix": WixSpider,
                "shopify": ShopifySpider,
                "bolt": BoltSpider,
                "lovable": LovableSpider,
                "gumroad": GumroadSpider,
                "replit": ReplitSpider,
                "squarespace": SquarespaceSpider,
                "notion": NotionSpider,
                "rocket": RocketSpider
            }
            
            if site_type not in spider_map:
                raise ValueError(f"Unsupported site type: {site_type}")
            
            spider_class = spider_map[site_type]
            spider = spider_class(url, output_dir, scrape_mode, selected_pages)
            
            await spider.scrape()
            
            zip_path = f"app/static/{job_id}.zip"
            if self.file_service.create_zip(output_dir, zip_path):
                self.file_service.cleanup_directory(output_dir)
                
                page_count = len(selected_pages) if selected_pages else "all"
                mode_text = "single page" if scrape_mode == "single_page" else f"{page_count} pages"

                return {
                    "success": True,
                    "message": f"Successfully scraped {mode_text} from {site_type} site",
                    "download_url": f"/download/{job_id}",
                    "file_path": zip_path,
                    "job_id": job_id
                }
            else:
                return {
                    "success": False,
                    "message": "Failed to create zip file"
                }
        except Exception as e:
            self.file_service.cleanup_directory(output_dir)
            return {
                "success": False,
                "message": f"Scraping failed: {str(e)}"
            }