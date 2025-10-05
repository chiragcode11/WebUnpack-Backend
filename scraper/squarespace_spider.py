from bs4 import BeautifulSoup
from scraper.base_spider import BaseSiteSpider

class SquarespaceSpider(BaseSiteSpider):
    def get_platform_name(self):
        return "Squarespace"
    
    def remove_platform_badge(self, html_content):
        css_to_inject = """
        <style>
        .squarespace-badge { display: none !important; }
        .powered-by-link { display: none !important; }
        .sqs-svg-logo--wordmark { display: none !important; }
        .sqs-svg-logo--glyph { display: none !important; }
        a[href*="squarespace.com"] { display: none !important; }
        [data-squarespace-badge] { display: none !important; }
        [class*="squarespace-badge"] { display: none !important; }
        [id*="squarespace-badge"] { display: none !important; }
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
            {'class': 'squarespace-badge'},
            {'class': 'powered-by-link'}
        ]
        
        for selector in badge_selectors:
            elements = soup.find_all('div', selector)
            for element in elements:
                element.decompose()
        
        squarespace_links = soup.find_all('a', href=lambda x: x and 'squarespace.com' in x)
        for link in squarespace_links:
            if any(keyword in link.get_text().lower() for keyword in ['powered', 'squarespace', 'made']):
                link.decompose()
        
        return str(soup)
