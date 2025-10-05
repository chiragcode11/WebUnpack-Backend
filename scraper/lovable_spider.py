from bs4 import BeautifulSoup
from scraper.base_spider import BaseSiteSpider

class LovableSpider(BaseSiteSpider):
    def get_platform_name(self):
        return "Lovable"
    
    def remove_platform_badge(self, html_content):
        css_to_inject = """
        <style>
        .lovable-badge { display: none !important; }
        .edit-with-lovable { display: none !important; }
        a[href*="lovable.dev"] { display: none !important; }
        [data-lovable-badge] { display: none !important; }
        [class*="lovable-badge"] { display: none !important; }
        [id*="lovable-badge"] { display: none !important; }
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
            {'class': 'lovable-badge'},
            {'class': 'edit-with-lovable'},
            {'attrs': {'data-lovable-badge': True}}
        ]
        
        for selector in badge_selectors:
            elements = soup.find_all('div', selector)
            for element in elements:
                element.decompose()
        
        lovable_links = soup.find_all('a', href=lambda x: x and 'lovable.dev' in x)
        for link in lovable_links:
            if any(keyword in link.get_text().lower() for keyword in ['edit', 'lovable', 'made']):
                link.decompose()
        
        return str(soup)
