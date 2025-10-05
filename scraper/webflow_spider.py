from bs4 import BeautifulSoup
from scraper.base_spider import BaseSiteSpider

class WebflowSpider(BaseSiteSpider):
    def get_platform_name(self):
        return "Webflow"
    
    def remove_platform_badge(self, html_content):
        css_to_inject = """
        <style>
        .w-webflow-badge { display: none !important; }
        .webflow-badge { display: none !important; }
        .w-badge { display: none !important; }
        .buy-badge.w-inline-block { display: none !important; }
        a[href*="webflow.com"] { display: none !important; }
        a[href*="webflow.io"] { display: none !important; }
        a[href*="webflow.com/template/"] { display: none !important; }
        a[href*="webflow.io/template/"] { display: none !important; }
        [data-w-id*="badge"] { display: none !important; }
        [data-w-id*="webflow"] { display: none !important; }
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
            {'class': 'w-webflow-badge'},
            {'class': 'webflow-badge'},
            {'class': 'buy-badge.w-inline-block'},
            {'class': 'w-badge'}
        ]
        
        for selector in badge_selectors:
            elements = soup.find_all('div', selector)
            for element in elements:
                element.decompose()

        webflow_links = soup.find_all('a', href=lambda x: x and ('webflow.com' in x or 'webflow.io' in x))
        for link in webflow_links:
            if any(keyword in link.get_text().lower() for keyword in ['made', 'webflow', 'built', 'template', 'free']):
                link.decompose()
        
        return str(soup)
