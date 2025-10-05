from bs4 import BeautifulSoup
from scraper.base_spider import BaseSiteSpider

class WordPressSpider(BaseSiteSpider):
    def get_platform_name(self):
        return "WordPress"
    
    def remove_platform_badge(self, html_content):
        css_to_inject = """
        <style>
        .wp-badge { display: none !important; }
        .wordpress-badge { display: none !important; }
        .powered-by { display: none !important; }
        a[href*="wordpress.org"] { display: none !important; }
        a[href*="wordpress.com"] { display: none !important; }
        .site-info a[href*="wordpress"] { display: none !important; }
        .footer-credits a[href*="wordpress"] { display: none !important; }
        [class*="wp-badge"] { display: none !important; }
        [id*="wp-badge"] { display: none !important; }
        </style>
        """
        
        if '</head>' in html_content:
            html_content = html_content.replace('</head>', f'{css_to_inject}</head>')
        elif '<body>' in html_content:
            html_content = html_content.replace('<body>', f'<body>{css_to_inject}')
        else:
            html_content = css_to_inject + html_content
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove meta generator tags
        meta_tags = soup.find_all('meta', attrs={'name': 'generator'})
        for meta in meta_tags:
            if 'wordpress' in meta.get('content', '').lower():
                meta.decompose()
        
        badge_selectors = [
            {'class': 'wp-badge'},
            {'class': 'wordpress-badge'},
            {'class': 'powered-by'}
        ]
        
        for selector in badge_selectors:
            elements = soup.find_all('div', selector)
            for element in elements:
                element.decompose()
        
        wordpress_links = soup.find_all('a', href=lambda x: x and ('wordpress.org' in x or 'wordpress.com' in x))
        for link in wordpress_links:
            if any(keyword in link.get_text().lower() for keyword in ['powered', 'wordpress', 'built', 'made']):
                link.decompose()
        
        return str(soup)
