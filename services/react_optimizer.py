from typing import Dict, List, Set
import re
import ast
import json

class ReactOptimizer:
    def __init__(self):
        self.optimization_rules = {
            'memo_candidates': self._identify_memo_candidates,
            'callback_optimization': self._identify_callback_optimizations,
            'state_optimization': self._identify_state_optimizations,
            'bundle_optimization': self._identify_bundle_optimizations,
            'accessibility_improvements': self._identify_accessibility_improvements,
            'performance_improvements': self._identify_performance_improvements
        }

    def optimize_components(self, components: Dict) -> Dict:
        optimizations = {}
        
        for component_name, component_code in components.get('components', {}).items():
            component_optimizations = self._analyze_component(component_name, component_code)
            optimized_code = self._apply_optimizations(component_code, component_optimizations)
            
            optimizations[component_name] = {
                'original_code': component_code,
                'optimized_code': optimized_code,
                'optimizations_applied': component_optimizations,
                'performance_impact': self._estimate_performance_impact(component_optimizations)
            }
        
        global_optimizations = self._identify_global_optimizations(components)
        
        return {
            'component_optimizations': optimizations,
            'global_optimizations': global_optimizations,
            'optimization_summary': self._create_optimization_summary(optimizations, global_optimizations)
        }

    def _analyze_component(self, component_name: str, component_code: Dict) -> List[Dict]:
        optimizations = []
        tsx_code = component_code.get('tsx', '')
        
        for rule_name, rule_func in self.optimization_rules.items():
            optimization = rule_func(tsx_code, component_name)
            if optimization:
                optimizations.append({
                    'type': rule_name,
                    'details': optimization,
                    'priority': self._get_optimization_priority(rule_name)
                })
        
        return sorted(optimizations, key=lambda x: x['priority'], reverse=True)

    def _identify_memo_candidates(self, tsx_code: str, component_name: str) -> Dict:
        memo_indicators = [
            'props.children',
            'props.*',
            'complex rendering logic',
            'expensive calculations'
        ]
        
        has_props = 'props' in tsx_code and ': React.FC' in tsx_code
        has_complex_logic = len(tsx_code.split('\n')) > 20
        has_expensive_operations = any(op in tsx_code for op in ['map(', 'filter(', 'reduce(', 'sort('])
        
        if has_props and (has_complex_logic or has_expensive_operations):
            return {
                'should_memo': True,
                'reason': 'Component receives props and has complex rendering logic',
                'implementation': f'export default React.memo({component_name});'
            }
        
        return {}

    def _identify_callback_optimizations(self, tsx_code: str, component_name: str) -> Dict:
        callback_patterns = [
            r'onClick=\{[^}]+\}',
            r'onChange=\{[^}]+\}',
            r'onSubmit=\{[^}]+\}'
        ]
        
        callbacks_found = []
        for pattern in callback_patterns:
            matches = re.findall(pattern, tsx_code)
            callbacks_found.extend(matches)
        
        if callbacks_found and 'useCallback' not in tsx_code:
            return {
                'should_optimize': True,
                'callbacks_count': len(callbacks_found),
                'implementation': 'Wrap event handlers in useCallback with proper dependencies'
            }
        
        return {}

    def _identify_state_optimizations(self, tsx_code: str, component_name: str) -> Dict:
        state_hooks = re.findall(r'useState\([^)]*\)', tsx_code)
        effect_hooks = re.findall(r'useEffect\([^}]+\}', tsx_code)
        
        optimizations = []
        
        if len(state_hooks) > 3:
            optimizations.append({
                'type': 'state_consolidation',
                'suggestion': 'Consider using useReducer for complex state management'
            })
        
        if len(effect_hooks) > 2:
            optimizations.append({
                'type': 'effect_optimization',
                'suggestion': 'Review effect dependencies and consider splitting effects'
            })
        
        expensive_computations = re.findall(r'(map\(|filter\(|reduce\(|sort\()', tsx_code)
        if expensive_computations and 'useMemo' not in tsx_code:
            optimizations.append({
                'type': 'memo_computation',
                'suggestion': 'Wrap expensive computations in useMemo'
            })
        
        return {'optimizations': optimizations} if optimizations else {}

    def _identify_bundle_optimizations(self, tsx_code: str, component_name: str) -> Dict:
        large_imports = re.findall(r'import.*from [\'"]([^\'"]+)[\'"]', tsx_code)
        heavy_libraries = ['lodash', 'moment', 'antd', 'material-ui']
        
        optimization_suggestions = []
        
        for imp in large_imports:
            if any(lib in imp for lib in heavy_libraries):
                optimization_suggestions.append({
                    'type': 'import_optimization',
                    'library': imp,
                    'suggestion': f'Use named imports or tree-shakable alternatives for {imp}'
                })
        
        if 'import React from' in tsx_code and not 'lazy' in tsx_code:
            if len(tsx_code.split('\n')) > 50:
                optimization_suggestions.append({
                    'type': 'code_splitting',
                    'suggestion': 'Consider code splitting for large components'
                })
        
        return {'suggestions': optimization_suggestions} if optimization_suggestions else {}

    def _identify_accessibility_improvements(self, tsx_code: str, component_name: str) -> Dict:
        improvements = []
        
        if '<button' in tsx_code and 'aria-label' not in tsx_code:
            improvements.append({
                'type': 'button_accessibility',
                'suggestion': 'Add aria-label or aria-describedby to buttons'
            })
        
        if '<img' in tsx_code and ('alt=' not in tsx_code or 'alt=""' in tsx_code):
            improvements.append({
                'type': 'image_accessibility',
                'suggestion': 'Ensure all images have descriptive alt text'
            })
        
        if '<form' in tsx_code and 'role=' not in tsx_code:
            improvements.append({
                'type': 'form_accessibility',
                'suggestion': 'Add appropriate ARIA roles to form elements'
            })
        
        if any(heading in tsx_code for heading in ['<h1', '<h2', '<h3']) and 'id=' not in tsx_code:
            improvements.append({
                'type': 'heading_structure',
                'suggestion': 'Add IDs to headings for better navigation'
            })
        
        return {'improvements': improvements} if improvements else {}

    def _identify_performance_improvements(self, tsx_code: str, component_name: str) -> Dict:
        improvements = []
        
        if 'useState(' in tsx_code and 'key=' not in tsx_code and '.map(' in tsx_code:
            improvements.append({
                'type': 'list_key_optimization',
                'suggestion': 'Ensure list items have stable, unique keys'
            })
        
        if '<img' in tsx_code and 'loading=' not in tsx_code:
            improvements.append({
                'type': 'image_loading',
                'suggestion': 'Add loading="lazy" to images below the fold'
            })
        
        if 'fetch(' in tsx_code and 'AbortController' not in tsx_code:
            improvements.append({
                'type': 'request_cancellation',
                'suggestion': 'Implement request cancellation for better performance'
            })
        
        return {'improvements': improvements} if improvements else {}

    def _apply_optimizations(self, component_code: Dict, optimizations: List[Dict]) -> Dict:
        optimized_code = component_code.copy()
        tsx_code = optimized_code.get('tsx', '')
        
        for optimization in optimizations:
            if optimization['type'] == 'memo_candidates' and optimization['details'].get('should_memo'):
                tsx_code = self._apply_memo_optimization(tsx_code, optimization['details'])
            
            elif optimization['type'] == 'callback_optimization' and optimization['details'].get('should_optimize'):
                tsx_code = self._apply_callback_optimization(tsx_code)
            
            elif optimization['type'] == 'state_optimization':
                tsx_code = self._apply_state_optimizations(tsx_code, optimization['details'])
            
            elif optimization['type'] == 'accessibility_improvements':
                tsx_code = self._apply_accessibility_improvements(tsx_code, optimization['details'])
        
        optimized_code['tsx'] = tsx_code
        return optimized_code

    def _apply_memo_optimization(self, tsx_code: str, memo_details: Dict) -> str:
        if 'export default React.memo' not in tsx_code:
            tsx_code = tsx_code.replace(
                'export default ',
                'export default React.memo('
            ).replace(
                ');', 
                '));'
            )
            
            if 'import React' in tsx_code and 'React.memo' not in tsx_code:
                tsx_code = tsx_code.replace(
                    'import React',
                    'import React, { memo }'
                ).replace(
                    'React.memo',
                    'memo'
                )
        
        return tsx_code

    def _apply_callback_optimization(self, tsx_code: str) -> str:
        if 'useCallback' not in tsx_code:
            if 'import React' in tsx_code:
                tsx_code = tsx_code.replace(
                    'import React',
                    'import React, { useCallback }'
                )
            
            callback_patterns = [
                (r'onClick=\{([^}]+)\}', r'onClick={useCallback(\1, [])}'),
                (r'onChange=\{([^}]+)\}', r'onChange={useCallback(\1, [])}'),
                (r'onSubmit=\{([^}]+)\}', r'onSubmit={useCallback(\1, [])}')
            ]
            
            for pattern, replacement in callback_patterns:
                tsx_code = re.sub(pattern, replacement, tsx_code)
        
        return tsx_code

    def _apply_state_optimizations(self, tsx_code: str, state_details: Dict) -> str:
        optimizations = state_details.get('optimizations', [])
        
        for opt in optimizations:
            if opt['type'] == 'memo_computation' and 'useMemo' not in tsx_code:
                if 'import React' in tsx_code:
                    tsx_code = tsx_code.replace(
                        'import React',
                        'import React, { useMemo }'
                    )
        
        return tsx_code

    def _apply_accessibility_improvements(self, tsx_code: str, accessibility_details: Dict) -> str:
        improvements = accessibility_details.get('improvements', [])
        
        for improvement in improvements:
            if improvement['type'] == 'button_accessibility':
                tsx_code = re.sub(
                    r'<button([^>]*?)>',
                    r'<button\1 aria-label="Button">',
                    tsx_code
                )
            
            elif improvement['type'] == 'image_accessibility':
                tsx_code = re.sub(
                    r'<img([^>]*?)alt=""([^>]*?)>',
                    r'<img\1alt="Image description"\2>',
                    tsx_code
                )
        
        return tsx_code

    def _get_optimization_priority(self, rule_name: str) -> int:
        priorities = {
            'accessibility_improvements': 10,
            'performance_improvements': 8,
            'memo_candidates': 6,
            'callback_optimization': 5,
            'state_optimization': 4,
            'bundle_optimization': 3
        }
        return priorities.get(rule_name, 1)

    def _estimate_performance_impact(self, optimizations: List[Dict]) -> Dict:
        total_impact = 0
        impact_breakdown = {}
        
        impact_scores = {
            'memo_candidates': 8,
            'callback_optimization': 6,
            'state_optimization': 7,
            'bundle_optimization': 9,
            'performance_improvements': 5
        }
        
        for opt in optimizations:
            opt_type = opt['type']
            score = impact_scores.get(opt_type, 1)
            total_impact += score
            impact_breakdown[opt_type] = score
        
        return {
            'total_score': min(total_impact, 10),
            'breakdown': impact_breakdown,
            'estimated_improvement': f"{min(total_impact * 2, 100)}%"
        }

    def _identify_global_optimizations(self, components: Dict) -> Dict:
        all_components = components.get('components', {})
        
        global_opts = {
            'shared_utilities': self._identify_shared_utilities(all_components),
            'common_patterns': self._identify_common_patterns(all_components),
            'code_splitting_opportunities': self._identify_code_splitting(all_components),
            'bundle_analysis': self._analyze_bundle_opportunities(all_components)
        }
        
        return global_opts

    def _identify_shared_utilities(self, components: Dict) -> List[str]:
        shared_utilities = []
        
        common_imports = {}
        for comp_name, comp_data in components.items():
            tsx_code = comp_data.get('tsx', '')
            imports = re.findall(r'import.*from [\'"]([^\'"]+)[\'"]', tsx_code)
            
            for imp in imports:
                if imp not in common_imports:
                    common_imports[imp] = []
                common_imports[imp].append(comp_name)
        
        for imp, components_using in common_imports.items():
            if len(components_using) > 2:
                shared_utilities.append(f"Create shared utility for {imp}")
        
        return shared_utilities

    def _identify_common_patterns(self, components: Dict) -> List[str]:
        patterns = []
        
        common_hooks = ['useState', 'useEffect', 'useCallback', 'useMemo']
        hook_usage = {hook: 0 for hook in common_hooks}
        
        for comp_data in components.values():
            tsx_code = comp_data.get('tsx', '')
            for hook in common_hooks:
                if hook in tsx_code:
                    hook_usage[hook] += 1
        
        for hook, count in hook_usage.items():
            if count > 3:
                patterns.append(f"Consider creating custom hook for {hook} pattern")
        
        return patterns

    def _identify_code_splitting(self, components: Dict) -> List[str]:
        splitting_opportunities = []
        
        large_components = []
        for comp_name, comp_data in components.items():
            tsx_code = comp_data.get('tsx', '')
            line_count = len(tsx_code.split('\n'))
            
            if line_count > 50:
                large_components.append(comp_name)
        
        if large_components:
            splitting_opportunities.append(f"Consider code splitting for: {', '.join(large_components)}")
        
        return splitting_opportunities

    def _analyze_bundle_opportunities(self, components: Dict) -> Dict:
        total_size_estimate = 0
        large_imports = []
        
        for comp_data in components.values():
            tsx_code = comp_data.get('tsx', '')
            total_size_estimate += len(tsx_code)
            
            imports = re.findall(r'import.*from [\'"]([^\'"]+)[\'"]', tsx_code)
            heavy_libs = ['lodash', 'moment', 'chart.js', 'three']
            
            for imp in imports:
                if any(lib in imp for lib in heavy_libs):
                    large_imports.append(imp)
        
        return {
            'estimated_size_kb': total_size_estimate // 1024,
            'large_dependencies': list(set(large_imports)),
            'optimization_potential': 'High' if total_size_estimate > 50000 else 'Medium'
        }

    def _create_optimization_summary(self, component_optimizations: Dict, global_optimizations: Dict) -> Dict:
        total_components = len(component_optimizations)
        optimized_components = sum(1 for comp in component_optimizations.values() 
                                 if comp['optimizations_applied'])
        
        return {
            'total_components_analyzed': total_components,
            'components_optimized': optimized_components,
            'optimization_coverage': f"{(optimized_components / max(total_components, 1)) * 100:.1f}%",
            'top_optimizations': self._get_top_optimizations(component_optimizations),
            'global_recommendations': len(global_optimizations.get('shared_utilities', [])),
            'estimated_performance_gain': f"{min(optimized_components * 15, 100)}%"
        }

    def _get_top_optimizations(self, component_optimizations: Dict) -> List[str]:
        optimization_counts = {}
        
        for comp_data in component_optimizations.values():
            for opt in comp_data.get('optimizations_applied', []):
                opt_type = opt.get('type', 'unknown')
                optimization_counts[opt_type] = optimization_counts.get(opt_type, 0) + 1
        
        sorted_opts = sorted(optimization_counts.items(), key=lambda x: x[1], reverse=True)
        return [opt_type for opt_type, _ in sorted_opts[:5]]
