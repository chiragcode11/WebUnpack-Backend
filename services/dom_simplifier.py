from bs4 import BeautifulSoup, NavigableString
from typing import Dict, List, Set
import json

class DOMSimplifier:
    def __init__(self):
        self.semantic_elements = {
            'header', 'nav', 'main', 'section', 'article', 'aside', 'footer',
            'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'ul', 'ol', 'li',
            'figure', 'figcaption', 'blockquote', 'address'
        }
        
        self.layout_indicators = {
            'container', 'wrapper', 'content', 'sidebar', 'grid', 'row', 'col',
            'flex', 'layout', 'section', 'panel', 'card', 'box'
        }
        
        self.component_indicators = {
            'button', 'btn', 'form', 'input', 'modal', 'dropdown', 'menu',
            'navbar', 'header', 'footer', 'card', 'item', 'list', 'grid'
        }

    def simplify_dom(self, html_content: str) -> Dict:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        structure = self._create_semantic_tree(soup)
        components = self._identify_components(soup)
        patterns = self._identify_patterns(soup)
        
        simplified_html = self._create_simplified_html(soup, structure, components)

        def serialize_structure(obj):
            if hasattr(obj, 'name'):  # BeautifulSoup Tag
                return {
                    'tag': obj.name,
                    'classes': obj.get('class', []),
                    'id': obj.get('id'),
                    'text': obj.get_text(strip=True)[:100]  # Limit text length
                }
            elif isinstance(obj, dict):
                return {k: serialize_structure(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [serialize_structure(item) for item in obj]
            return obj
        
        return {
            'simplified_html': simplified_html,
            'structure': serialize_structure(structure),
            'components': serialize_structure(components),
            'patterns': serialize_structure(patterns),
            'metadata': {
                'total_elements': len(soup.find_all()),
                'semantic_elements': len([e for e in soup.find_all() if e.name in self.semantic_elements]),
                'depth': self._calculate_depth(soup),
                'complexity_score': self._calculate_complexity(soup)
            }
        }

    def _create_semantic_tree(self, soup) -> Dict:
        body = soup.find('body') or soup
        
        structure = {
            'type': 'page',
            'layout': self._detect_page_layout(body),
            'sections': []
        }
        
        main_sections = self._identify_main_sections(body)
        
        for section in main_sections:
            section_info = {
                'type': self._classify_section(section),
                'element': section.name,
                'classes': section.get('class', []),
                'children': self._analyze_children(section),
                'complexity': self._calculate_element_complexity(section)
            }
            structure['sections'].append(section_info)
        
        return structure

    def _identify_components(self, soup) -> List[Dict]:
        components = []
        
        repeated_elements = self._find_repeated_elements(soup)
        
        for pattern, elements in repeated_elements.items():
            if len(elements) >= 2:
                component = {
                    'type': self._classify_component(elements[0]),
                    'pattern': pattern,
                    'occurrences': len(elements),
                    'structure': self._analyze_component_structure(elements[0]),
                    'variations': self._analyze_variations(elements)
                }
                components.append(component)
        
        form_components = self._identify_form_components(soup)
        components.extend(form_components)
        
        navigation_components = self._identify_navigation_components(soup)
        components.extend(navigation_components)
        
        return components

    def _identify_patterns(self, soup) -> Dict:
        patterns = {
            'layout_patterns': self._identify_layout_patterns(soup),
            'content_patterns': self._identify_content_patterns(soup),
            'interaction_patterns': self._identify_interaction_patterns(soup)
        }
        
        return patterns

    def _create_simplified_html(self, soup, structure: Dict, components: List[Dict]) -> str:
        simplified = BeautifulSoup('<html><body></body></html>', 'html.parser')
        body = simplified.body
        
        for section in structure['sections']:
            section_elem = simplified.new_tag('section')
            section_elem['data-type'] = section['type']
            
            if section['type'] == 'navigation':
                nav_elem = simplified.new_tag('nav')
                nav_elem.string = '{{NAVIGATION_COMPONENT}}'
                section_elem.append(nav_elem)
            elif section['type'] == 'hero':
                hero_content = self._create_hero_template(section)
                section_elem.append(BeautifulSoup(hero_content, 'html.parser'))
            elif section['type'] == 'content_grid':
                grid_content = self._create_grid_template(section)
                section_elem.append(BeautifulSoup(grid_content, 'html.parser'))
            elif section['type'] == 'footer':
                footer_elem = simplified.new_tag('footer')
                footer_elem.string = '{{FOOTER_COMPONENT}}'
                section_elem.append(footer_elem)
            else:
                generic_elem = simplified.new_tag('div')
                generic_elem.string = f'{{{{{section["type"].upper()}_CONTENT}}}}'
                section_elem.append(generic_elem)
            
            body.append(section_elem)
        
        return str(simplified)

    def _detect_page_layout(self, body) -> str:
        has_header = bool(body.find(['header', '[role="banner"]']))
        has_nav = bool(body.find(['nav', '[role="navigation"]']))
        has_main = bool(body.find(['main', '[role="main"]']))
        has_aside = bool(body.find(['aside', '[role="complementary"]']))
        has_footer = bool(body.find(['footer', '[role="contentinfo"]']))
        
        if has_header and has_main and has_footer:
            if has_aside:
                return 'header_main_sidebar_footer'
            else:
                return 'header_main_footer'
        elif has_nav and has_main:
            return 'nav_main'
        else:
            return 'single_column'

    def _identify_main_sections(self, body) -> List:
        sections = []
        
        semantic_sections = body.find_all(['header', 'nav', 'main', 'section', 'article', 'aside', 'footer'])
        
        if semantic_sections:
            sections = semantic_sections
        else:
            top_level_divs = [div for div in body.find_all('div', recursive=False) 
                            if self._is_main_section(div)]
            sections = top_level_divs[:5]
        
        return sections

    def _classify_section(self, element) -> str:
        tag_name = element.name
        classes = ' '.join(element.get('class', [])).lower()
        
        if tag_name == 'header' or 'header' in classes:
            return 'header'
        elif tag_name == 'nav' or 'nav' in classes or 'menu' in classes:
            return 'navigation'
        elif tag_name == 'main' or 'main' in classes:
            return 'main'
        elif tag_name == 'footer' or 'footer' in classes:
            return 'footer'
        elif 'hero' in classes or 'banner' in classes:
            return 'hero'
        elif 'grid' in classes or 'cards' in classes:
            return 'content_grid'
        elif tag_name in ['section', 'article']:
            return 'content_section'
        else:
            return 'generic_section'

    def _analyze_children(self, element) -> Dict:
        children = element.find_all(recursive=False)
        
        return {
            'count': len(children),
            'types': list(set([child.name for child in children if child.name])),
            'has_text': bool(element.get_text(strip=True)),
            'has_images': bool(element.find_all('img')),
            'has_links': bool(element.find_all('a')),
            'has_forms': bool(element.find_all(['form', 'input', 'button']))
        }

    def _find_repeated_elements(self, soup) -> Dict[str, List]:
        element_patterns = {}
        
        all_elements = soup.find_all()
        
        for element in all_elements:
            pattern = self._create_element_pattern(element)
            if pattern not in element_patterns:
                element_patterns[pattern] = []
            element_patterns[pattern].append(element)
        
        return {pattern: elements for pattern, elements in element_patterns.items() 
                if len(elements) >= 2 and len(pattern) > 10}

    def _create_element_pattern(self, element) -> str:
        if not element.name:
            return ""
        
        pattern_parts = [element.name]
        
        classes = element.get('class', [])
        if classes:
            pattern_parts.append('class:' + '|'.join(sorted(classes)))
        
        children = [child.name for child in element.find_all(recursive=False) if child.name]
        if children:
            pattern_parts.append('children:' + '|'.join(children))
        
        return '::'.join(pattern_parts)

    def _classify_component(self, element) -> str:
        tag_name = element.name
        classes = ' '.join(element.get('class', [])).lower()
        
        component_types = {
            'card': ['card', 'item', 'post', 'product'],
            'button': ['button', 'btn', 'cta'],
            'form': ['form', 'input', 'field'],
            'navigation': ['nav', 'menu', 'breadcrumb'],
            'media': ['image', 'video', 'figure'],
            'list': ['list', 'grid', 'collection']
        }
        
        for comp_type, indicators in component_types.items():
            if any(indicator in classes for indicator in indicators):
                return comp_type
        
        if tag_name in ['form', 'nav', 'figure']:
            return tag_name
        
        return 'generic'

    def _analyze_component_structure(self, element) -> Dict:
        structure = {
            'tag': element.name,
            'has_image': bool(element.find('img')),
            'has_heading': bool(element.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])),
            'has_text': bool(element.get_text(strip=True)),
            'has_link': bool(element.find('a')),
            'has_button': bool(element.find(['button', '.btn'])),
            'child_count': len(element.find_all(recursive=False)),
            'depth': len(list(element.parents))
        }
        
        return structure

    def _analyze_variations(self, elements) -> List[str]:
        variations = []
        
        base_structure = self._analyze_component_structure(elements[0])
        
        for element in elements[1:]:
            current_structure = self._analyze_component_structure(element)
            
            differences = []
            for key, value in current_structure.items():
                if key in base_structure and base_structure[key] != value:
                    differences.append(f"{key}_different")
            
            if differences:
                variations.extend(differences)
        
        return list(set(variations))

    def _identify_form_components(self, soup) -> List[Dict]:
        forms = soup.find_all('form')
        components = []
        
        for form in forms:
            inputs = form.find_all(['input', 'textarea', 'select'])
            component = {
                'type': 'form',
                'pattern': 'form_component',
                'occurrences': 1,
                'structure': {
                    'input_count': len(inputs),
                    'input_types': [inp.get('type', 'text') for inp in inputs if inp.name == 'input'],
                    'has_submit': bool(form.find(['input[type="submit"]', 'button[type="submit"]'])),
                    'method': form.get('method', 'get').upper()
                },
                'variations': []
            }
            components.append(component)
        
        return components

    def _identify_navigation_components(self, soup) -> List[Dict]:
        navs = soup.find_all(['nav', '.navbar', '.menu', '.navigation'])
        components = []
        
        for nav in navs:
            links = nav.find_all('a')
            component = {
                'type': 'navigation',
                'pattern': 'nav_component',
                'occurrences': 1,
                'structure': {
                    'link_count': len(links),
                    'has_dropdown': bool(nav.find(['.dropdown', '.submenu'])),
                    'layout': 'horizontal' if 'horizontal' in ' '.join(nav.get('class', [])) else 'vertical'
                },
                'variations': []
            }
            components.append(component)
        
        return components

    def _identify_layout_patterns(self, soup) -> List[str]:
        patterns = []
        
        if soup.find_all('.container, .wrapper'):
            patterns.append('container_wrapper')
        
        if soup.find_all('[class*="grid"], [class*="row"], [class*="col"]'):
            patterns.append('grid_system')
        
        if soup.find_all('[class*="flex"]'):
            patterns.append('flexbox_layout')
        
        return patterns

    def _identify_content_patterns(self, soup) -> List[str]:
        patterns = []
        
        cards = soup.find_all(['.card', '.item', '.post'])
        if len(cards) >= 3:
            patterns.append('card_grid')
        
        if soup.find(['aside', '.sidebar']):
            patterns.append('sidebar_layout')
        
        return patterns

    def _identify_interaction_patterns(self, soup) -> List[str]:
        patterns = []
        
        if soup.find_all(['button', '.btn']):
            patterns.append('button_interactions')
        
        if soup.find_all('form'):
            patterns.append('form_interactions')
        
        if soup.find_all(['.modal', '.popup', '.overlay']):
            patterns.append('modal_interactions')
        
        return patterns

    def _create_hero_template(self, section: Dict) -> str:
        return """
        <div class="hero">
            <h1>{{HERO_TITLE}}</h1>
            <p>{{HERO_DESCRIPTION}}</p>
            <button>{{HERO_CTA}}</button>
        </div>
        """

    def _create_grid_template(self, section: Dict) -> str:
        return """
        <div class="grid">
            <div class="grid-item">
                <img src="{{IMAGE_PLACEHOLDER}}" alt="{{ALT_TEXT}}">
                <h3>{{ITEM_TITLE}}</h3>
                <p>{{ITEM_DESCRIPTION}}</p>
                <a href="#">{{ITEM_LINK}}</a>
            </div>
            <div class="grid-repeat">{{REPEAT_PATTERN: 3-6 items}}</div>
        </div>
        """

    def _is_main_section(self, element) -> bool:
        classes = ' '.join(element.get('class', [])).lower()
        
        main_indicators = [
            'section', 'content', 'main', 'container', 'wrapper',
            'hero', 'banner', 'footer', 'header', 'sidebar'
        ]
        
        return any(indicator in classes for indicator in main_indicators) or len(element.find_all()) > 5

    def _calculate_depth(self, soup) -> int:
        max_depth = 0
        for element in soup.find_all():
            depth = len(list(element.parents))
            max_depth = max(max_depth, depth)
        return max_depth

    def _calculate_complexity(self, soup) -> int:
        total_elements = len(soup.find_all())
        unique_tags = len(set(e.name for e in soup.find_all() if e.name))
        total_classes = sum(len(e.get('class', [])) for e in soup.find_all())
        
        return total_elements + unique_tags + (total_classes // 10)

    def _calculate_element_complexity(self, element) -> int:
        children_count = len(element.find_all())
        classes_count = len(element.get('class', []))
        depth = len(list(element.parents))
        
        return children_count + classes_count + depth
