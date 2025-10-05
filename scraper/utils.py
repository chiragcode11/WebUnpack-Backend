import os
import re
from urllib.parse import urljoin, urlparse

def get_page_name(url):
    parsed = urlparse(url)
    path = parsed.path.strip('/')
    if not path:
        return 'index'
    return path.replace('/', '_').replace('.', '_')

def is_internal_link(link, current_url):
    if not link:
        return False
    if link.startswith(('mailto:', 'tel:', '#', 'javascript:')):
        return False
    if link.startswith('http'):
        current_domain = urlparse(current_url).netloc
        link_domain = urlparse(link).netloc
        return current_domain == link_domain
    return True

def process_html_content(html, base_url):
    domain = urlparse(base_url).netloc
    html = re.sub(rf'https?://{re.escape(domain)}/', './', html)
    html = re.sub(rf'https?://{re.escape(domain)}', '.', html)
    return html

def clean_asset_path(asset_path):
    if asset_path.startswith('//'):
        asset_path = 'https:' + asset_path
    return asset_path.lstrip('/')

def ensure_dir(file_path):
    directory = os.path.dirname(file_path)
    if directory:
        os.makedirs(directory, exist_ok=True)
