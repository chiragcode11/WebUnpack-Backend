from bs4 import BeautifulSoup
from scraper.base_spider import BaseSiteSpider

class RocketSpider(BaseSiteSpider):
    def get_platform_name(self):
        return "Rocket"
    
    def remove_platform_badge(self, html_content):
        css_to_inject = """
        <style>
        .rocket-badge { display: none !important; }
        .made-in-rocket { display: none !important; }
        a[href*="rocket.new"] { display: none !important; }
        [data-rocket-badge] { display: none !important; }
        [class*="rocket-badge"] { display: none !important; }
        [id*="rocket-badge"] { display: none !important; }
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
            {'class': 'rocket-badge'},
            {'class': 'made-in-rocket'}
        ]
        
        for selector in badge_selectors:
            elements = soup.find_all('div', selector)
            for element in elements:
                element.decompose()
        
        rocket_links = soup.find_all('a', href=lambda x: x and 'rocket.new' in x)
        for link in rocket_links:
            if any(keyword in link.get_text().lower() for keyword in ['rocket', 'made', 'built']):
                link.decompose()
        
        return str(soup)
