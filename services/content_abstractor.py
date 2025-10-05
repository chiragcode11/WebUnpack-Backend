from bs4 import BeautifulSoup
import re
from typing import Dict, List
import hashlib

class ContentAbstractor:
    def __init__(self):
        self.content_placeholders = {}
        self.placeholder_counter = 0

    def abstract_content(self, html_content: str) -> Dict:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        text_abstractions = self._abstract_text_content(soup)
        image_abstractions = self._abstract_images(soup)
        media_abstractions = self._abstract_media(soup)
        form_abstractions = self._abstract_forms(soup)
        list_abstractions = self._abstract_lists(soup)

        abstracted_html = str(soup)
        
        return {
            'abstracted_html': abstracted_html,
            'abstractions': {
                'text': text_abstractions,
                'images': image_abstractions,
                'media': media_abstractions,
                'forms': form_abstractions,
                'lists': list_abstractions
            }
        }
    def _create_placeholder(self, content_type: str, metadata: Dict = None) -> str:
        self.placeholder_counter += 1
        placeholder = f"{{{{{content_type}_{self.placeholder_counter}}}}}"
        
        if metadata:
            self.content_placeholders[placeholder] = metadata
            
        return placeholder

    def _abstract_text_content(self, soup) -> List[Dict]:
        text_abstractions = []
        
        headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        for heading in headings:
            if not heading or not hasattr(heading, 'name'):
                continue
                
            original_text = heading.get_text(strip=True)
            if original_text:
                placeholder = self._create_placeholder('HEADING', {
                    'level': heading.name,
                    'length': len(original_text),
                    'original': original_text[:50] + '...' if len(original_text) > 50 else original_text
                })
                heading.string = placeholder
                text_abstractions.append({
                    'type': 'heading',
                    'element': heading.name,
                    'placeholder': placeholder,
                    'metadata': self.content_placeholders[placeholder]
                })

        paragraphs = soup.find_all(['p', 'span', 'div'], string=True)
        for paragraph in paragraphs:
            if not paragraph or not hasattr(paragraph, 'parent') or not paragraph.parent:
                continue
                
            parent_name = getattr(paragraph.parent, 'name', None)
            if parent_name not in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                text_content = paragraph.get_text(strip=True)
                if text_content and len(text_content) > 10:
                    placeholder = self._create_placeholder('TEXT', {
                        'length': len(text_content),
                        'word_count': len(text_content.split()),
                        'type': 'paragraph' if getattr(paragraph, 'name', None) == 'p' else 'text'
                    })
                    paragraph.string = placeholder
                    text_abstractions.append({
                        'type': 'text',
                        'element': getattr(paragraph, 'name', 'unknown'),
                        'placeholder': placeholder,
                        'metadata': self.content_placeholders[placeholder]
                    })

        return text_abstractions

    def _abstract_images(self, soup) -> List[Dict]:
        image_abstractions = []
        
        images = soup.find_all('img')
        for img in images:
            src = img.get('src', '')
            alt = img.get('alt', '')
            width = img.get('width', 'auto')
            height = img.get('height', 'auto')
            
            placeholder = self._create_placeholder('IMAGE', {
                'alt': alt,
                'dimensions': f"{width}x{height}",
                'src_type': 'external' if src.startswith('http') else 'local'
            })
            
            img['src'] = placeholder
            if alt:
                img['alt'] = f"{{ALT_TEXT_{len(image_abstractions) + 1}}}"
            
            image_abstractions.append({
                'type': 'image',
                'placeholder': placeholder,
                'metadata': self.content_placeholders[placeholder]
            })

        return image_abstractions

    def _abstract_media(self, soup) -> List[Dict]:
        media_abstractions = []
        
        videos = soup.find_all(['video', 'iframe'])
        for video in videos:
            if video.name == 'iframe' and 'youtube.com' not in video.get('src', ''):
                continue
                
            placeholder = self._create_placeholder('VIDEO', {
                'type': 'youtube' if video.name == 'iframe' else 'local',
                'width': video.get('width', 'auto'),
                'height': video.get('height', 'auto')
            })
            
            if video.name == 'iframe':
                video['src'] = placeholder
            else:
                video['src'] = placeholder
                
            media_abstractions.append({
                'type': 'video',
                'element': video.name,
                'placeholder': placeholder,
                'metadata': self.content_placeholders[placeholder]
            })

        return media_abstractions

    def _abstract_forms(self, soup) -> List[Dict]:
        form_abstractions = []
        
        forms = soup.find_all('form')
        for form in forms:
            inputs = form.find_all(['input', 'textarea', 'select'])
            input_types = []
            
            for input_elem in inputs:
                input_type = input_elem.get('type', 'text') if input_elem.name == 'input' else input_elem.name
                input_types.append(input_type)
                
                if input_elem.get('placeholder'):
                    placeholder = self._create_placeholder('FORM_PLACEHOLDER')
                    input_elem['placeholder'] = placeholder

            form_abstractions.append({
                'type': 'form',
                'input_count': len(inputs),
                'input_types': input_types,
                'has_submit': bool(form.find(['input[type="submit"]', 'button[type="submit"]']))
            })

        return form_abstractions

    def _abstract_lists(self, soup) -> List[Dict]:
        list_abstractions = []
        
        lists = soup.find_all(['ul', 'ol'])
        for list_elem in lists:
            items = list_elem.find_all('li')
            
            if len(items) > 3:
                for i, item in enumerate(items[2:], 3):
                    if i < len(items) - 1:
                        item.decompose()
                
                remaining_count = len(items) - 2
                if remaining_count > 0:
                    placeholder_li = soup.new_tag('li')
                    placeholder_li.string = f"{{{{LIST_ITEMS_REMAINING: {remaining_count}}}}}"
                    list_elem.append(placeholder_li)

            for item in list_elem.find_all('li')[:2]:
                text_content = item.get_text(strip=True)
                if text_content:
                    placeholder = self._create_placeholder('LIST_ITEM')
                    item.string = placeholder

            list_abstractions.append({
                'type': 'list',
                'list_type': list_elem.name,
                'item_count': len(items),
                'abstracted_count': min(2, len(items))
            })

        return list_abstractions
