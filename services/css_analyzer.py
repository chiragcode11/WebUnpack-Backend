import re
import cssutils
from typing import Dict, List, Set
import logging

cssutils.log.setLevel(logging.CRITICAL)

class CSSAnalyzer:
    def __init__(self):
        self.layout_properties = ['display', 'position', 'float', 'clear', 'flex', 'grid']
        self.spacing_properties = ['margin', 'padding', 'gap', 'row-gap', 'column-gap']
        self.sizing_properties = ['width', 'height', 'max-width', 'max-height', 'min-width', 'min-height']
        self.typography_properties = ['font-family', 'font-size', 'font-weight', 'line-height', 'letter-spacing']

    def analyze_css(self, css_content: str) -> Dict:
        try:
            sheet = cssutils.parseString(css_content)
        except:
            return self._fallback_analysis(css_content)

        analysis = {
            'layout_patterns': self._analyze_layout_patterns(sheet),
            'spacing_system': self._analyze_spacing_system(sheet),
            'typography_system': self._analyze_typography_system(sheet),
            'color_palette': self._analyze_color_palette(sheet),
            'responsive_breakpoints': self._analyze_responsive_patterns(sheet),
            'component_patterns': self._analyze_component_patterns(sheet)
        }

        return analysis

    def _analyze_layout_patterns(self, sheet) -> Dict:
        layout_patterns = {
            'display_types': set(),
            'positioning': set(),
            'flexbox_usage': [],
            'grid_usage': [],
            'common_layouts': []
        }

        for rule in sheet:
            if rule.type == rule.STYLE_RULE:
                style = rule.style
                
                if 'display' in style:
                    layout_patterns['display_types'].add(style['display'])
                
                if 'position' in style:
                    layout_patterns['positioning'].add(style['position'])
                
                if 'display' in style and 'flex' in style['display']:
                    flex_props = {}
                    for prop in ['flex-direction', 'justify-content', 'align-items', 'flex-wrap']:
                        if prop in style:
                            flex_props[prop] = style[prop]
                    if flex_props:
                        layout_patterns['flexbox_usage'].append(flex_props)
                
                if 'display' in style and 'grid' in style['display']:
                    grid_props = {}
                    for prop in ['grid-template-columns', 'grid-template-rows', 'grid-gap', 'gap']:
                        if prop in style:
                            grid_props[prop] = style[prop]
                    if grid_props:
                        layout_patterns['grid_usage'].append(grid_props)

        layout_patterns['display_types'] = list(layout_patterns['display_types'])
        layout_patterns['positioning'] = list(layout_patterns['positioning'])
        
        return layout_patterns

    def _analyze_spacing_system(self, sheet) -> Dict:
        spacing_values = []
        
        for rule in sheet:
            if rule.type == rule.STYLE_RULE:
                style = rule.style
                
                for prop in self.spacing_properties:
                    if prop in style:
                        value = style[prop]
                        spacing_values.extend(self._extract_numeric_values(value))

        spacing_values = [v for v in spacing_values if v > 0]
        spacing_values = sorted(set(spacing_values))
        
        scale_base = self._detect_scale_base(spacing_values)
        
        return {
            'values': spacing_values[:10],
            'scale_base': scale_base,
            'scale_type': self._detect_scale_type(spacing_values, scale_base),
            'common_values': self._get_most_common_values(spacing_values)
        }

    def _analyze_typography_system(self, sheet) -> Dict:
        font_sizes = []
        font_families = set()
        font_weights = set()
        line_heights = []

        for rule in sheet:
            if rule.type == rule.STYLE_RULE:
                style = rule.style
                
                if 'font-size' in style:
                    size_values = self._extract_numeric_values(style['font-size'])
                    font_sizes.extend(size_values)
                
                if 'font-family' in style:
                    family = style['font-family'].replace('"', '').replace("'", "")
                    font_families.add(family.split(',')[0].strip())
                
                if 'font-weight' in style:
                    font_weights.add(style['font-weight'])
                
                if 'line-height' in style:
                    lh_values = self._extract_numeric_values(style['line-height'])
                    line_heights.extend(lh_values)

        return {
            'font_sizes': sorted(set(font_sizes))[:8],
            'font_families': list(font_families)[:5],
            'font_weights': sorted(list(font_weights)),
            'line_heights': sorted(set(line_heights))[:5],
            'typography_scale': self._calculate_typography_scale(font_sizes)
        }

    def _analyze_color_palette(self, sheet) -> Dict:
        colors = set()
        
        for rule in sheet:
            if rule.type == rule.STYLE_RULE:
                style = rule.style
                
                for prop in style:
                    if 'color' in prop.name or 'background' in prop.name:
                        color_values = self._extract_colors(prop.value)
                        colors.update(color_values)

        return {
            'primary_colors': list(colors)[:10],
            'color_count': len(colors),
            'has_css_variables': '--' in str(sheet)
        }

    def _analyze_responsive_patterns(self, sheet) -> Dict:
        breakpoints = set()
        media_queries = []

        for rule in sheet:
            if rule.type == rule.MEDIA_RULE:
                media_text = rule.media.mediaText
                media_queries.append(media_text)
                
                bp_values = self._extract_numeric_values(media_text)
                breakpoints.update(bp_values)

        return {
            'breakpoints': sorted(list(breakpoints)),
            'media_query_count': len(media_queries),
            'responsive_approach': self._detect_responsive_approach(media_queries)
        }

    def _analyze_component_patterns(self, sheet) -> Dict:
        component_selectors = []
        
        for rule in sheet:
            if rule.type == rule.STYLE_RULE:
                selector = rule.selectorText
                
                if self._is_component_selector(selector):
                    component_selectors.append(selector)

        return {
            'component_selectors': component_selectors[:20],
            'naming_convention': self._detect_naming_convention(component_selectors),
            'component_count': len(component_selectors)
        }

    def _extract_numeric_values(self, value: str) -> List[float]:
        if not value:
            return []
        
        numbers = re.findall(r'(\d+(?:\.\d+)?)', value)
        return [float(n) for n in numbers if float(n) > 0]

    def _extract_colors(self, value: str) -> List[str]:
        colors = []
        
        hex_colors = re.findall(r'#([a-fA-F0-9]{3,6})', value)
        colors.extend([f"#{color}" for color in hex_colors])
        
        rgb_colors = re.findall(r'rgb\([^)]+\)', value)
        colors.extend(rgb_colors)
        
        rgba_colors = re.findall(r'rgba\([^)]+\)', value)
        colors.extend(rgba_colors)
        
        return colors

    def _detect_scale_base(self, values: List[float]) -> int:
        if not values:
            return 8
        
        common_bases = [4, 8, 16]
        for base in common_bases:
            matches = sum(1 for v in values if v % base == 0)
            if matches / len(values) > 0.6:
                return base
        
        return 8

    def _detect_scale_type(self, values: List[float], base: int) -> str:
        if not values or len(values) < 3:
            return 'custom'
        
        arithmetic_check = all(values[i] - values[i-1] == base for i in range(1, min(4, len(values))))
        if arithmetic_check:
            return 'arithmetic'
        
        geometric_ratios = [values[i] / values[i-1] for i in range(1, min(4, len(values))) if values[i-1] > 0]
        if geometric_ratios and all(abs(ratio - geometric_ratios[0]) < 0.1 for ratio in geometric_ratios):
            return 'geometric'
        
        return 'custom'

    def _get_most_common_values(self, values: List[float]) -> List[float]:
        from collections import Counter
        counter = Counter(values)
        return [value for value, _ in counter.most_common(5)]

    def _calculate_typography_scale(self, font_sizes: List[float]) -> Dict:
        if len(font_sizes) < 2:
            return {'type': 'custom', 'ratio': 1.0}
        
        sorted_sizes = sorted(font_sizes)
        ratios = [sorted_sizes[i] / sorted_sizes[i-1] for i in range(1, len(sorted_sizes)) if sorted_sizes[i-1] > 0]
        
        if ratios:
            avg_ratio = sum(ratios) / len(ratios)
            
            known_scales = {
                1.125: 'major_second',
                1.25: 'major_third',
                1.333: 'perfect_fourth',
                1.414: 'augmented_fourth',
                1.5: 'perfect_fifth',
                1.618: 'golden_ratio'
            }
            
            closest_scale = min(known_scales.keys(), key=lambda x: abs(x - avg_ratio))
            if abs(closest_scale - avg_ratio) < 0.05:
                return {'type': known_scales[closest_scale], 'ratio': closest_scale}
        
        return {'type': 'custom', 'ratio': avg_ratio if ratios else 1.0}

    def _detect_responsive_approach(self, media_queries: List[str]) -> str:
        mobile_first = sum(1 for mq in media_queries if 'min-width' in mq)
        desktop_first = sum(1 for mq in media_queries if 'max-width' in mq)
        
        if mobile_first > desktop_first:
            return 'mobile_first'
        elif desktop_first > mobile_first:
            return 'desktop_first'
        else:
            return 'mixed'

    def _is_component_selector(self, selector: str) -> bool:
        component_indicators = [
            '.',  # Class selector
            '[class*=', # Attribute selector for classes
            ':not(', # Complex selectors
        ]
        
        return any(indicator in selector for indicator in component_indicators) and len(selector.split()) <= 3

    def _detect_naming_convention(self, selectors: List[str]) -> str:
        if not selectors:
            return 'unknown'
        
        bem_pattern = re.compile(r'\.[\w-]+__([\w-]+)(--[\w-]+)?')
        utility_pattern = re.compile(r'\.[a-z]+-[a-z0-9-]+')
        camel_case_pattern = re.compile(r'\.([A-Z][a-z0-9]+)+')
        
        bem_count = sum(1 for s in selectors if bem_pattern.search(s))
        utility_count = sum(1 for s in selectors if utility_pattern.search(s))
        camel_count = sum(1 for s in selectors if camel_case_pattern.search(s))
        
        total = len(selectors)
        if bem_count / total > 0.3:
            return 'bem'
        elif utility_count / total > 0.5:
            return 'utility'
        elif camel_count / total > 0.3:
            return 'camelCase'
        else:
            return 'custom'

    def _fallback_analysis(self, css_content: str) -> Dict:
        return {
            'layout_patterns': {'display_types': ['block', 'flex'], 'positioning': ['static', 'relative']},
            'spacing_system': {'values': [8, 16, 24, 32], 'scale_base': 8, 'scale_type': 'arithmetic'},
            'typography_system': {'font_sizes': [14, 16, 18, 24], 'font_families': ['Arial', 'sans-serif']},
            'color_palette': {'primary_colors': [], 'color_count': 0},
            'responsive_breakpoints': {'breakpoints': [768, 1024], 'responsive_approach': 'mobile_first'},
            'component_patterns': {'component_selectors': [], 'naming_convention': 'custom'}
        }
