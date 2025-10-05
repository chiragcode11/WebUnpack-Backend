from bs4 import BeautifulSoup
from scraper.base_spider import BaseSiteSpider

class GumroadSpider(BaseSiteSpider):
    def get_platform_name(self):
        return "Gumroad"
    
    def remove_platform_badge(self, html_content):
        css_to_inject = """
        <style>
        .gumroad-badge { display: none !important; }
        .powered-by-gumroad { display: none !important; }
        a[href*="gumroad.com"] { display: none !important; }
        [data-gumroad-badge] { display: none !important; }
        [class*="gumroad-badge"] { display: none !important; }
        [id*="gumroad-badge"] { display: none !important; }
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
            {'class': 'gumroad-badge'},
            {'class': 'powered-by-gumroad'}
        ]
        
        for selector in badge_selectors:
            elements = soup.find_all('div', selector)
            for element in elements:
                element.decompose()
        
        gumroad_links = soup.find_all('a', href=lambda x: x and 'gumroad.com' in x)
        for link in gumroad_links:
            if any(keyword in link.get_text().lower() for keyword in ['powered', 'gumroad', 'made']):
                link.decompose()
        
        return str(soup)
