from bs4 import BeautifulSoup
from scraper.base_spider import BaseSiteSpider

class ReplitSpider(BaseSiteSpider):
    def get_platform_name(self):
        return "Replit"
    
    def remove_platform_badge(self, html_content):
        css_to_inject = """
        <style>
        .replit-badge { display: none !important; }
        [data-replit-badge] { display: none !important; }
        [class*="replit-badge"] { display: none !important; }
        [id*="replit-badge"] { display: none !important; }
        a[href*="replit.com"] { display: none !important; }
        script[src*="replit-badge"] { display: none !important; }
        </style>
        """
        
        if '</head>' in html_content:
            html_content = html_content.replace('</head>', f'{css_to_inject}</head>')
        elif '<body>' in html_content:
            html_content = html_content.replace('<body>', f'<body>{css_to_inject}')
        else:
            html_content = css_to_inject + html_content
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove Replit badge script tags
        replit_scripts = soup.find_all('script', src=lambda x: x and 'replit-badge' in x)
        for script in replit_scripts:
            script.decompose()
        
        badge_selectors = [
            {'class': 'replit-badge'},
            {'attrs': {'data-replit-badge': True}}
        ]
        
        for selector in badge_selectors:
            elements = soup.find_all('div', selector)
            for element in elements:
                element.decompose()
        
        replit_links = soup.find_all('a', href=lambda x: x and 'replit.com' in x)
        for link in replit_links:
            if any(keyword in link.get_text().lower() for keyword in ['replit', 'made', 'run']):
                link.decompose()
        
        return str(soup)
