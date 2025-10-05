from bs4 import BeautifulSoup
from scraper.base_spider import BaseSiteSpider

class FramerSpider(BaseSiteSpider):
    def get_platform_name(self):
        return "Framer"
    
    def remove_platform_badge(self, html_content):
        css_to_inject = """
        <style>
        #__framer-badge-container { display: none !important; }
        [data-framer-name="Made with Framer"] { display: none !important; }
        .framer-badge { display: none !important; }
        a[href*="framer.com"][target="_blank"] { display: none !important; }
        /* Target the "Edit template" badge specifically */
        a[href*="framer.com/templates"] { display: none !important; }
        [data-framer-name*="Edit template"] { display: none !important; }
        [class*="edit-template"] { display: none !important; }
        [class*="template-badge"] { display: none !important; }
        button:contains("Edit template") { display: none !important; }
        div:has(a[href*="templates"]) { display: none !important; }
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
            {'id': '__framer-badge-container'},
            {'attrs': {'data-framer-name': 'Made with Framer'}},
            {'class': 'framer-badge'},
            {'class': 'edit-template'},
            {'class': 'template-badge'}
        ]
        
        for selector in badge_selectors:
            elements = soup.find_all('div', selector)
            for element in elements:
                element.decompose()

        for element in soup.find_all(['a', 'button', 'div', 'span']):
            element_text = element.get_text(strip=True).lower()
            if 'edit template' in element_text and len(element_text) < 50:
                print(f"Removing edit template badge: {element_text}")
                element.decompose()

        framer_links = soup.find_all('a', href=lambda x: x and 'framer.com' in x)
        for link in framer_links:
            link_text = link.get_text().lower()
            if any(keyword in link_text for keyword in ['made', 'framer', 'built', 'edit', 'template', 'free']):
                print(f"Removing framer link: {link_text}")
                link.decompose()
        
        return str(soup)
