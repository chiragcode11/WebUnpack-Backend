from bs4 import BeautifulSoup, Comment
import re
from typing import Dict, List
import json

class HTMLCleaner:
    def __init__(self):
        self.noise_patterns = [
            r'<!--.*?-->',
            r'<script[^>]*>.*?</script>',
            r'<noscript[^>]*>.*?</noscript>',
            r'<meta[^>]*>',
            r'<link[^>]*rel=["\']stylesheet["\'][^>]*>',
            r'<style[^>]*>.*?</style>',
        ]
        
        self.noise_classes = [
            'gtm-', 'ga-', 'fb-', 'twitter-', 'linkedin-',
            'tracking-', 'analytics-', 'pixel-', 'tag-',
            'ads-', 'advertisement-', 'banner-', 'popup-'
        ]
        
        self.noise_attributes = [
            'data-gtm', 'data-ga', 'data-analytics', 'data-track',
            'data-pixel', 'data-fb', 'onclick', 'onload', 'onerror'
        ]

    def clean_html(self, html_content: str) -> str:
        if not html_content or not html_content.strip():
            return ""
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            self._remove_comments(soup)
            self._remove_noise_elements(soup)
            self._clean_attributes(soup)
            self._remove_empty_elements(soup)
            self._normalize_whitespace(soup)
            
            return str(soup)
        except Exception as e:
            print(f"Error cleaning HTML: {e}")
            return html_content

    def _remove_comments(self, soup):
        try:
            for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
                if comment:
                    comment.extract()
        except Exception:
            pass

    def _remove_noise_elements(self, soup):
        noise_selectors = [
            'script', 'noscript', 'meta', 'link[rel="stylesheet"]',
            'style', 'iframe[src*="google"]', 'iframe[src*="facebook"]',
            '[class*="gtm"]', '[class*="analytics"]', '[class*="tracking"]',
            '[id*="gtm"]', '[id*="analytics"]', '[id*="tracking"]'
        ]
        
        for selector in noise_selectors:
            try:
                for element in soup.select(selector):
                    if element and hasattr(element, 'decompose'):
                        element.decompose()
            except Exception:
                continue

    def _clean_attributes(self, soup):
        try:
            for element in soup.find_all():
                if not element or not hasattr(element, 'attrs'):
                    continue
                
                attrs_to_remove = []
                
                try:
                    for attr_name in list(element.attrs.keys()):
                        if any(noise_attr in attr_name for noise_attr in self.noise_attributes):
                            attrs_to_remove.append(attr_name)
                        elif attr_name in ['style', 'onclick', 'onload', 'onerror']:
                            attrs_to_remove.append(attr_name)
                except (AttributeError, TypeError):
                    continue
                
                for attr in attrs_to_remove:
                    try:
                        if attr in element.attrs:
                            del element.attrs[attr]
                    except (KeyError, TypeError, AttributeError):
                        continue
                
                if 'class' in element.attrs:
                    try:
                        clean_classes = []
                        class_list = element.attrs.get('class', [])
                        
                        if isinstance(class_list, list):
                            for class_name in class_list:
                                if class_name and not any(noise_class in class_name for noise_class in self.noise_classes):
                                    clean_classes.append(class_name)
                        elif isinstance(class_list, str):
                            if class_list and not any(noise_class in class_list for noise_class in self.noise_classes):
                                clean_classes.append(class_list)
                        
                        if clean_classes:
                            element.attrs['class'] = clean_classes
                        else:
                            try:
                                del element.attrs['class']
                            except (KeyError, AttributeError):
                                pass
                    except (AttributeError, TypeError):
                        continue
        except Exception:
            pass

    def _remove_empty_elements(self, soup):
        try:
            iteration_limit = 10
            iteration_count = 0
            
            while iteration_count < iteration_limit:
                empty_elements = []
                
                try:
                    for tag in soup.find_all():
                        if not tag or not hasattr(tag, 'name') or not tag.name:
                            continue
                        
                        if (tag.name not in ['img', 'br', 'hr', 'input', 'meta', 'link'] 
                            and not tag.get_text(strip=True) 
                            and not tag.find_all(['img', 'input', 'button'])):
                            empty_elements.append(tag)
                except Exception:
                    break
                
                if not empty_elements:
                    break
                    
                for element in empty_elements:
                    try:
                        if element and hasattr(element, 'decompose'):
                            element.decompose()
                    except Exception:
                        continue
                
                iteration_count += 1
        except Exception:
            pass

    def _normalize_whitespace(self, soup):
        try:
            for element in soup.find_all(string=True):
                if not element:
                    continue
                    
                try:
                    text_content = str(element)
                    if text_content and text_content.strip():
                        normalized = re.sub(r'\s+', ' ', text_content.strip())
                        element.replace_with(normalized)
                except Exception:
                    continue
        except Exception:
            pass
