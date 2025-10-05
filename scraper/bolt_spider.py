from bs4 import BeautifulSoup
from scraper.base_spider import BaseSiteSpider

class BoltSpider(BaseSiteSpider):
    def get_platform_name(self):
        return "Bolt"
    
    def remove_platform_badge(self, html_content):
        css_to_inject = """
        <style>
        .bolt-badge { display: none !important; }
        .made-in-bolt { display: none !important; }
        a[href*="bolt.new"] { display: none !important; }
        [data-bolt-badge] { display: none !important; }
        [class*="bolt-badge"] { display: none !important; }
        [id*="bolt-badge"] { display: none !important; }
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
            {'class': 'bolt-badge'},
            {'class': 'made-in-bolt'},
            {'attrs': {'data-bolt-badge': True}}
        ]
        
        for selector in badge_selectors:
            elements = soup.find_all(['div', 'span', 'a'], selector)
            for element in elements:
                print(f"Removing Bolt badge element: {element.get('class', element.get('id', 'unknown'))}")
                element.decompose()
        
        for element in soup.find_all(['div', 'a', 'span', 'p']):
            element_text = element.get_text(strip=True)
            if element_text and 'made in bolt' in element_text.lower():
                if len(element_text) < 50:
                    print(f"Removing Bolt text badge: {element_text}")
                    element.decompose()

        bolt_links = soup.find_all('a', href=lambda x: x and ('bolt.new' in x or 'bolt.host' in x))
        for link in bolt_links:
            link_text = link.get_text().strip()
            if any(keyword in link_text.lower() for keyword in ['made', 'bolt', 'built', 'powered', 'created']):
                print(f"Removing Bolt promotional link: {link_text}")
                link.decompose()
        
        return str(soup)
