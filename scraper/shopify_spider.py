from bs4 import BeautifulSoup
from scraper.base_spider import BaseSiteSpider

class ShopifySpider(BaseSiteSpider):
    def get_platform_name(self):
        return "Shopify"
    
    def remove_platform_badge(self, html_content):
        css_to_inject = """
        <style>
        .shopify-badge { display: none !important; }
        .powered-by-shopify { display: none !important; }
        .shopify-credits { display: none !important; }
        a[href*="shopify.com"] { display: none !important; }
        .site-footer a[href*="shopify"] { display: none !important; }
        .footer a[href*="shopify"] { display: none !important; }
        [class*="shopify-badge"] { display: none !important; }
        [id*="shopify-badge"] { display: none !important; }
        [class*="powered-by"] { display: none !important; }
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
            {'class': 'shopify-badge'},
            {'class': 'powered-by-shopify'},
            {'class': 'shopify-credits'}
        ]
        
        for selector in badge_selectors:
            elements = soup.find_all('div', selector)
            for element in elements:
                element.decompose()
        
        # Remove footer elements containing "powered by shopify"
        footer_elements = soup.find_all(['footer', 'div'], class_=lambda x: x and 'footer' in ' '.join(x).lower())
        for footer in footer_elements:
            links = footer.find_all('a')
            for link in links:
                text = link.get_text(strip=True).lower()
                if 'powered by' in text and 'shopify' in text:
                    link.decompose()
        
        shopify_links = soup.find_all('a', href=lambda x: x and 'shopify.com' in x)
        for link in shopify_links:
            if any(keyword in link.get_text().lower() for keyword in ['powered', 'shopify', 'built', 'made']):
                link.decompose()
        
        return str(soup)
