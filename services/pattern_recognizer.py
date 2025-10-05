from typing import Dict, List, Set, Tuple
from bs4 import BeautifulSoup
import re
from collections import Counter, defaultdict

class PatternRecognizer:
    def __init__(self):
        self.ui_patterns = {
            'hero_section': {
                'indicators': ['hero', 'banner', 'jumbotron', 'splash'],
                'structure': ['heading', 'text', 'button'],
                'position': 'top'
            },
            'card_component': {
                'indicators': ['card', 'item', 'post', 'product'],
                'structure': ['image?', 'heading', 'text', 'link?'],
                'repeating': True
            },
            'navigation_menu': {
                'indicators': ['nav', 'menu', 'navbar', 'navigation'],
                'structure': ['list', 'links'],
                'position': 'top'
            },
            'form_component': {
                'indicators': ['form', 'contact', 'signup', 'login'],
                'structure': ['inputs', 'button'],
                'interactive': True
            },
            'footer_section': {
                'indicators': ['footer', 'bottom', 'copyright'],
                'structure': ['links', 'text', 'social?'],
                'position': 'bottom'
            }
        }

    def recognize_patterns(self, html_content: str, css_analysis: Dict = None) -> Dict:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        patterns = {
            'ui_components': self._identify_ui_components(soup),
            'layout_patterns': self._identify_layout_patterns(soup),
            'content_patterns': self._identify_content_patterns(soup),
            'interaction_patterns': self._identify_interaction_patterns(soup),
            'responsive_patterns': self._identify_responsive_patterns(soup, css_analysis),
            'component_hierarchy': self._build_component_hierarchy(soup)
        }
        
        return patterns

    def _identify_ui_components(self, soup) -> List[Dict]:
        components = []
        
        for pattern_name, pattern_def in self.ui_patterns.items():
            matches = self._find_pattern_matches(soup, pattern_def)
            
            for match in matches:
                component = {
                    'type': pattern_name,
                    'element': {
                        'tag': match.name,
                        'classes': match.get('class', []),
                        'id': match.get('id'),
                        'text_preview': match.get_text(strip=True)[:50]
                    },
                    'confidence': self._calculate_confidence(match, pattern_def),
                    'properties': self._extract_component_properties(match, pattern_name),
                    'children': self._analyze_component_children(match),
                    'variants': self._identify_component_variants(match, matches)
                }
                components.append(component)
        
        components = sorted(components, key=lambda x: x['confidence'], reverse=True)
        return self._deduplicate_components(components)

    def _find_pattern_matches(self, soup, pattern_def: Dict) -> List:
        matches = []
        
        for indicator in pattern_def['indicators']:
            class_matches = soup.find_all(class_=re.compile(indicator, re.I))
            id_matches = soup.find_all(id=re.compile(indicator, re.I))
            matches.extend(class_matches + id_matches)
        
        if pattern_def.get('position') == 'top':
            body = soup.find('body') or soup
            first_sections = body.find_all(recursive=False)[:3]
            for section in first_sections:
                if self._matches_structure(section, pattern_def):
                    matches.append(section)
        
        if pattern_def.get('position') == 'bottom':
            body = soup.find('body') or soup
            last_sections = body.find_all(recursive=False)[-3:]
            for section in last_sections:
                if self._matches_structure(section, pattern_def):
                    matches.append(section)
        
        return list(set(matches))

    def _matches_structure(self, element, pattern_def: Dict) -> bool:
        structure = pattern_def.get('structure', [])
        if not structure:
            return True
        
        required_elements = [s for s in structure if not s.endswith('?')]
        optional_elements = [s.rstrip('?') for s in structure if s.endswith('?')]
        
        found_required = 0
        for req_element in required_elements:
            if self._has_element_type(element, req_element):
                found_required += 1
        
        return found_required >= len(required_elements) * 0.7

    def _has_element_type(self, element, element_type: str) -> bool:
        type_mappings = {
            'heading': ['h1', 'h2', 'h3', 'h4', 'h5', 'h6'],
            'text': ['p', 'span', 'div'],
            'button': ['button', 'a.btn', '.button'],
            'image': ['img', 'figure', 'picture'],
            'link': ['a'],
            'list': ['ul', 'ol', 'nav'],
            'inputs': ['input', 'textarea', 'select']
        }
        
        selectors = type_mappings.get(element_type, [element_type])
        
        for selector in selectors:
            if element.find(selector):
                return True
        
        return False

    def _calculate_confidence(self, element, pattern_def: Dict) -> float:
        confidence = 0.0
        
        classes = ' '.join(element.get('class', [])).lower()
        element_id = element.get('id', '').lower()
        
        for indicator in pattern_def['indicators']:
            if indicator in classes or indicator in element_id:
                confidence += 0.3
        
        structure_match = self._matches_structure(element, pattern_def)
        if structure_match:
            confidence += 0.4
        
        position_match = self._check_position_match(element, pattern_def)
        if position_match:
            confidence += 0.2
        
        size_appropriateness = self._check_size_appropriateness(element, pattern_def)
        confidence += size_appropriateness * 0.1
        
        return min(confidence, 1.0)

    def _check_position_match(self, element, pattern_def: Dict) -> bool:
        expected_position = pattern_def.get('position')
        if not expected_position:
            return True
        
        body = element.find_parent('body') or element.find_parent()
        if not body:
            return False
        
        all_siblings = body.find_all(recursive=False)
        element_index = 0
        
        try:
            element_index = all_siblings.index(element)
        except ValueError:
            return False
        
        total_siblings = len(all_siblings)
        
        if expected_position == 'top':
            return element_index < total_siblings * 0.3
        elif expected_position == 'bottom':
            return element_index > total_siblings * 0.7
        
        return True

    def _check_size_appropriateness(self, element, pattern_def: Dict) -> float:
        child_count = len(element.find_all())
        text_length = len(element.get_text(strip=True))
        
        size_expectations = {
            'hero_section': {'min_children': 2, 'min_text': 50},
            'card_component': {'min_children': 1, 'min_text': 10},
            'navigation_menu': {'min_children': 2, 'min_text': 20},
            'form_component': {'min_children': 1, 'min_text': 0},
            'footer_section': {'min_children': 1, 'min_text': 10}
        }
        
        pattern_name = next((name for name, def_ in self.ui_patterns.items() if def_ == pattern_def), None)
        expectations = size_expectations.get(pattern_name, {'min_children': 1, 'min_text': 0})
        
        children_score = 1.0 if child_count >= expectations['min_children'] else 0.5
        text_score = 1.0 if text_length >= expectations['min_text'] else 0.5
        
        return (children_score + text_score) / 2

    def _extract_component_properties(self, element, component_type: str) -> Dict:
        properties = {
            'tag': element.name,
            'classes': element.get('class', []),
            'id': element.get('id'),
            'children_count': len(element.find_all(recursive=False)),
            'text_content': bool(element.get_text(strip=True)),
            'has_images': bool(element.find_all('img')),
            'has_links': bool(element.find_all('a')),
            'has_forms': bool(element.find_all(['form', 'input', 'button']))
        }
        
        if component_type == 'card_component':
            properties.update({
                'has_title': bool(element.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])),
                'has_description': bool(element.find(['p', '.description', '.excerpt'])),
                'has_cta': bool(element.find(['.btn', '.button', 'button', '.cta']))
            })
        elif component_type == 'navigation_menu':
            links = element.find_all('a')
            properties.update({
                'link_count': len(links),
                'has_dropdown': bool(element.find(['.dropdown', '.submenu', '.subnav'])),
                'orientation': self._detect_nav_orientation(element)
            })
        elif component_type == 'form_component':
            inputs = element.find_all(['input', 'textarea', 'select'])
            properties.update({
                'input_count': len(inputs),
                'input_types': [inp.get('type', 'text') for inp in inputs if inp.name == 'input'],
                'has_validation': bool(element.find(['[required]', '.error', '.invalid']))
            })
        
        return properties

    def _analyze_component_children(self, element) -> List[Dict]:
        children = []
        direct_children = element.find_all(recursive=False)
        
        for child in direct_children[:5]:  # Limit to first 5 children
            child_info = {
                'tag': child.name,
                'classes': child.get('class', []),
                'content_type': self._classify_content_type(child),
                'has_children': bool(child.find_all(recursive=False)),
                'text_length': len(child.get_text(strip=True))
            }
            children.append(child_info)
        
        return children

    def _classify_content_type(self, element) -> str:
        tag_name = element.name
        classes = ' '.join(element.get('class', [])).lower()
        
        content_types = {
            'title': ['h1', 'h2', 'h3', 'h4', 'h5', 'h6'],
            'text': ['p', 'span', 'div'],
            'image': ['img', 'figure', 'picture'],
            'button': ['button', 'a'],
            'list': ['ul', 'ol'],
            'input': ['input', 'textarea', 'select']
        }
        
        for content_type, tags in content_types.items():
            if tag_name in tags:
                return content_type
        
        content_indicators = {
            'title': ['title', 'heading', 'header'],
            'text': ['text', 'content', 'description', 'excerpt'],
            'image': ['image', 'img', 'photo', 'picture'],
            'button': ['btn', 'button', 'cta', 'action'],
            'meta': ['meta', 'info', 'details', 'date']
        }
        
        for content_type, indicators in content_indicators.items():
            if any(indicator in classes for indicator in indicators):
                return content_type
        
        return 'generic'

    def _identify_component_variants(self, element, all_matches: List) -> List[str]:
        if len(all_matches) <= 1:
            return []
        
        base_classes = set(element.get('class', []))
        base_structure = len(element.find_all(recursive=False))
        
        variants = []
        
        for match in all_matches:
            if match == element:
                continue
            
            match_classes = set(match.get('class', []))
            match_structure = len(match.find_all(recursive=False))
            
            class_diff = match_classes - base_classes
            if class_diff:
                variants.extend([f"with_{cls}" for cls in class_diff])
            
            if match_structure != base_structure:
                if match_structure > base_structure:
                    variants.append("extended")
                else:
                    variants.append("minimal")
        
        return list(set(variants))

    def _detect_nav_orientation(self, nav_element) -> str:
        classes = ' '.join(nav_element.get('class', [])).lower()
        
        if 'vertical' in classes or 'sidebar' in classes:
            return 'vertical'
        elif 'horizontal' in classes or 'navbar' in classes:
            return 'horizontal'
        
        links = nav_element.find_all('a')
        if len(links) > 5:
            return 'horizontal'
        
        return 'horizontal'

    def _identify_layout_patterns(self, soup) -> List[Dict]:
        patterns = []
        
        grid_containers = soup.find_all(class_=re.compile(r'grid|row|columns', re.I))
        for container in grid_containers:
            pattern = {
                'type': 'grid_layout',
                'element': {
                    'tag': container.name,
                    'classes': container.get('class', [])
                },
                'columns': self._estimate_columns(container),
                'items': len(container.find_all(recursive=False))
            }
            patterns.append(pattern)
        
        flex_containers = soup.find_all(class_=re.compile(r'flex|flexbox', re.I))
        for container in flex_containers:
            pattern = {
                'type': 'flex_layout',
                'element': {
                    'tag': container.name,
                    'classes': container.get('class', [])
                },
                'direction': self._detect_flex_direction(container),
                'items': len(container.find_all(recursive=False))
            }
            patterns.append(pattern)
        
        return patterns

    def _identify_content_patterns(self, soup) -> List[Dict]:
        patterns = []
        
        repeated_elements = self._find_repeated_content_structures(soup)
        for structure, elements in repeated_elements.items():
            if len(elements) >= 3:
                pattern = {
                    'type': 'repeated_content',
                    'structure': structure,
                    'count': len(elements),
                    'sample_tags': [e.name for e in elements[:3]]
                }
                patterns.append(pattern)
        
        return patterns

    def _build_component_hierarchy(self, soup) -> Dict:
        hierarchy = {
            'root': 'page',
            'children': []
        }
        
        body = soup.find('body') or soup
        main_sections = body.find_all(recursive=False)
        
        for section in main_sections:
            section_info = {
                'type': self._classify_section_type(section),
                'element': section.name,
                'children': self._build_section_children(section)
            }
            hierarchy['children'].append(section_info)
        
        return hierarchy

    def _identify_interaction_patterns(self, soup) -> List[Dict]:
        patterns = []
        
        forms = soup.find_all('form')
        if forms:
            patterns.append({
                'type': 'form_interaction',
                'count': len(forms),
                'complexity': sum(len(form.find_all(['input', 'textarea', 'select'])) for form in forms)
            })
        
        buttons = soup.find_all(['button', '.btn', '.button'])
        if buttons:
            patterns.append({
                'type': 'button_interaction',
                'count': len(buttons),
                'types': list(set([btn.get('type', 'button') for btn in buttons if btn.name == 'button']))
            })
        
        return patterns

    def _identify_responsive_patterns(self, soup, css_analysis: Dict = None) -> List[Dict]:
        patterns = []
        
        if css_analysis and 'responsive_breakpoints' in css_analysis:
            breakpoints = css_analysis['responsive_breakpoints'].get('breakpoints', [])
            if breakpoints:
                patterns.append({
                    'type': 'responsive_design',
                    'breakpoints': breakpoints,
                    'approach': css_analysis['responsive_breakpoints'].get('responsive_approach', 'unknown')
                })
        
        responsive_images = soup.find_all('img', srcset=True)
        if responsive_images:
            patterns.append({
                'type': 'responsive_images',
                'count': len(responsive_images)
            })
        
        return patterns

    def _classify_section_type(self, element) -> str:
        tag_name = element.name
        classes = ' '.join(element.get('class', [])).lower()
        
        section_types = {
            'header': ['header', 'top', 'masthead'],
            'navigation': ['nav', 'menu', 'navbar'],
            'hero': ['hero', 'banner', 'jumbotron'],
            'content': ['content', 'main', 'body'],
            'sidebar': ['sidebar', 'aside', 'secondary'],
            'footer': ['footer', 'bottom', 'copyright']
        }
        
        if tag_name in section_types:
            return tag_name
        
        for section_type, indicators in section_types.items():
            if any(indicator in classes for indicator in indicators):
                return section_type
        
        return 'section'

    def _build_section_children(self, section) -> List[Dict]:
        children = []
        direct_children = section.find_all(recursive=False)
        
        for child in direct_children[:3]:
            child_info = {
                'type': self._classify_content_type(child),
                'tag': child.name,
                'has_children': bool(child.find_all(recursive=False))
            }
            children.append(child_info)
        
        return children

    def _estimate_columns(self, container) -> int:
        direct_children = container.find_all(recursive=False)
        
        if not direct_children:
            return 1
        
        classes = ' '.join(container.get('class', [])).lower()
        
        column_indicators = {
            'col-1': 1, 'col-2': 2, 'col-3': 3, 'col-4': 4, 'col-6': 6,
            'grid-1': 1, 'grid-2': 2, 'grid-3': 3, 'grid-4': 4,
            'columns-1': 1, 'columns-2': 2, 'columns-3': 3, 'columns-4': 4
        }
        
        for indicator, cols in column_indicators.items():
            if indicator in classes:
                return cols
        
        child_count = len(direct_children)
        if child_count <= 2:
            return child_count
        elif child_count <= 4:
            return min(3, child_count)
        else:
            return 4

    def _detect_flex_direction(self, container) -> str:
        classes = ' '.join(container.get('class', [])).lower()
        
        if 'column' in classes or 'vertical' in classes:
            return 'column'
        else:
            return 'row'

    def _find_repeated_content_structures(self, soup) -> Dict[str, List]:
        structure_map = defaultdict(list)
        
        all_elements = soup.find_all()
        
        for element in all_elements:
            if len(element.find_all(recursive=False)) < 2:
                continue
            
            structure_signature = self._create_structure_signature(element)
            if len(structure_signature) > 5:
                structure_map[structure_signature].append(element)
        
        return {sig: elements for sig, elements in structure_map.items() if len(elements) >= 3}

    def _create_structure_signature(self, element) -> str:
        children = element.find_all(recursive=False)
        child_signatures = []
        
        for child in children:
            child_sig = child.name
            if child.get('class'):
                child_sig += f"[{','.join(child.get('class')[:2])}]"
            child_signatures.append(child_sig)
        
        return '->'.join(child_signatures)

    def _deduplicate_components(self, components: List[Dict]) -> List[Dict]:
        seen_elements = set()
        unique_components = []
        
        for component in components:
            element_id = id(component['element'])
            if element_id not in seen_elements:
                seen_elements.add(element_id)
                unique_components.append(component)
        
        return unique_components
