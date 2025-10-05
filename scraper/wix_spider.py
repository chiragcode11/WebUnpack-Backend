from bs4 import BeautifulSoup
from scraper.base_spider import BaseSiteSpider

class WixSpider(BaseSiteSpider):
    def get_platform_name(self):
        return "Wix"
    
    def remove_platform_badge(self, html_content):
        css_to_inject = """
        <style>
        .wix-badge { display: none !important; }
        .wix-banner { display: none !important; }
        a[href*="wix.com"] { display: none !important; }
        [data-wix-id*="badge"] { display: none !important; }
        [class*="wix-badge"] { display: none !important; }
        [id*="wix-badge"] { display: none !important; }
        div[style*="position: fixed"][style*="top"] { display: none !important; }
        body { margin-top: 0 !important; padding-top: 0 !important; }
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
            {'class': 'wix-badge'},
            {'class': 'wix-banner'}
        ]
        
        for selector in badge_selectors:
            elements = soup.find_all('div', selector)
            for element in elements:
                element.decompose()
        
        wix_links = soup.find_all('a', href=lambda x: x and 'wix.com' in x)
        for link in wix_links:
            if any(keyword in link.get_text().lower() for keyword in ['created', 'designed', 'website', 'free', 'build']):
                link.decompose()
        
        return str(soup)
