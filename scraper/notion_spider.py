from bs4 import BeautifulSoup
from scraper.base_spider import BaseSiteSpider

class NotionSpider(BaseSiteSpider):
    def get_platform_name(self):
        return "Notion"
    
    def remove_platform_badge(self, html_content):
        css_to_inject = """
        <style>
        .notion-badge { display: none !important; }
        .made-with-notion { display: none !important; }
        a[href*="notion.so"] { display: none !important; }
        a[href*="notion.site"] { display: none !important; }
        [data-notion-badge] { display: none !important; }
        [class*="notion-badge"] { display: none !important; }
        [id*="notion-badge"] { display: none !important; }
        </style>
        """
        
        if '</head>' in html_content:
            html_content = html_content.replace('</head>', f'{css_to_inject}</head>')
        elif '<body>' in html_content:
            html_content = html_content.replace('<body>', f'<body>{css_to_inject}')
        else:
            html_content = css_to_inject + html_content
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        badge_selectors = [
            {'class': 'notion-badge'},
            {'class': 'made-with-notion'}
        ]
        
        for selector in badge_selectors:
            elements = soup.find_all('div', selector)
            for element in elements:
                element.decompose()
        
        notion_links = soup.find_all('a', href=lambda x: x and ('notion.so' in x or 'notion.site' in x))
        for link in notion_links:
            if any(keyword in link.get_text().lower() for keyword in ['notion', 'made', 'powered']):
                link.decompose()
        
        return str(soup)
