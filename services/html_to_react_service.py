import asyncio
from typing import Dict, List, Optional
import logging
from datetime import datetime
import os
from bs4 import Tag, NavigableString

from services.html_cleaner import HTMLCleaner
from services.content_abstractor import ContentAbstractor
from services.css_analyzer import CSSAnalyzer
from services.dom_simplifier import DOMSimplifier
from services.pattern_recognizer import PatternRecognizer
from services.gemini_ai_service import GeminiAIService
from services.react_code_generator import ReactCodeGenerator
from services.react_optimizer import ReactOptimizer

class HTMLToReactService:
    def __init__(self, gemini_api_key: str):
        self.html_cleaner = HTMLCleaner()
        self.content_abstractor = ContentAbstractor()
        self.css_analyzer = CSSAnalyzer()
        self.dom_simplifier = DOMSimplifier()
        self.pattern_recognizer = PatternRecognizer()
        self.gemini_service = GeminiAIService(gemini_api_key)
        self.react_generator = ReactCodeGenerator()
        self.react_optimizer = ReactOptimizer()
        self.logger = logging.getLogger(__name__)

    async def convert_html_to_react(self, html_content: str, css_content: str, job_id: str) -> Dict:
        try:
            self.logger.info(f"Starting HTML to React conversion for job {job_id}")
            
            preprocessing_result = await self._preprocess_html(html_content, css_content)
            
            ai_analysis_result = await self._analyze_with_ai(preprocessing_result)
            
            react_generation_result = await self._generate_react_code(ai_analysis_result, job_id)
            
            optimization_result = await self._optimize_react_code(react_generation_result)
            
            final_result = await self._finalize_project(optimization_result, job_id)
            
            self.logger.info(f"Successfully completed HTML to React conversion for job {job_id}")
            
            return {
                'success': True,
                'job_id': job_id,
                'preprocessing': preprocessing_result,
                'ai_analysis': ai_analysis_result,
                'react_generation': react_generation_result,
                'optimization': optimization_result,
                'final_project': final_result,
                'conversion_stats': self._generate_conversion_stats(final_result),
                'download_ready': True
            }
            
        except Exception as e:
            self.logger.error(f"HTML to React conversion failed for job {job_id}: {str(e)}")
            return {
                'success': False,
                'job_id': job_id,
                'error': str(e),
                'stage': 'conversion_failed'
            }

    async def _preprocess_html(self, html_content: str, css_content: str) -> Dict:
        self.logger.info("Starting HTML preprocessing")
        
        cleaned_html = self.html_cleaner.clean_html(html_content)
        
        abstraction_result = self.content_abstractor.abstract_content(cleaned_html)
        
        css_analysis = self.css_analyzer.analyze_css(css_content) if css_content else {}
        
        abstracted_html_str = str(abstraction_result['abstracted_html']) if not isinstance(abstraction_result['abstracted_html'], str) else abstraction_result['abstracted_html']
        
        dom_result = self.dom_simplifier.simplify_dom(abstracted_html_str)
        
        patterns = self.pattern_recognizer.recognize_patterns(
            abstracted_html_str, 
            css_analysis
        )

        result = {
            'cleaned_html': str(cleaned_html),
            'abstracted_html': abstraction_result['abstracted_html'],
            'abstractions': abstraction_result['abstractions'],
            'css_analysis': css_analysis,
            'dom_structure': dom_result,
            'patterns': patterns,
            'preprocessing_stats': {
                'original_size': len(html_content),
                'cleaned_size': len(str(cleaned_html)),
                'abstracted_size': len(abstraction_result['abstracted_html']),
                'compression_ratio': f"{(1 - len(abstraction_result['abstracted_html']) / len(html_content)) * 100:.1f}%"
            }
        }

        return self._ensure_json_serializable(result)

    async def _analyze_with_ai(self, preprocessing_result: Dict) -> Dict:
        self.logger.info("Starting AI analysis")
        
        semantic_html = preprocessing_result['abstracted_html']
        patterns = preprocessing_result['patterns']
        css_analysis = preprocessing_result['css_analysis']
        
        component_analysis = await self.gemini_service.analyze_components(
            semantic_html, patterns, css_analysis
        )
        
        typescript_interfaces = await self.gemini_service.generate_typescript_interfaces(
            component_analysis
        )

        def ensure_serializable(obj):
            if hasattr(obj, '__class__') and 'bs4' in str(type(obj)):
                return str(obj)
            elif isinstance(obj, dict):
                return {k: ensure_serializable(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [ensure_serializable(item) for item in obj]
            return obj
        
        return {
            'component_analysis': ensure_serializable(component_analysis),
            'typescript_interfaces': ensure_serializable(typescript_interfaces),
            'ai_confidence': self._calculate_ai_confidence(component_analysis),
            'component_count': len(component_analysis.get('component_hierarchy', [])),
            'reusable_component_count': len(component_analysis.get('reusable_components', []))
        }
    
    async def _generate_react_code(self, ai_analysis: Dict, job_id: str) -> Dict:
        self.logger.info("Generating React code")
        
        component_analysis = ai_analysis['component_analysis']
        design_tokens = component_analysis.get('design_tokens', {})
        
        react_components = await self.gemini_service.generate_react_components(
            component_analysis, design_tokens
        )
        
        project_result = self.react_generator.generate_react_project(react_components, job_id)
        
        return {
            'react_components': react_components,
            'project_generation': project_result,
            'components_generated': len(react_components.get('components', {})),
            'files_created': project_result.get('files_generated', 0)
        }

    async def _optimize_react_code(self, react_generation: Dict) -> Dict:
        self.logger.info("Optimizing React code")
        
        react_components = react_generation['react_components']
        
        optimization_result = self.react_optimizer.optimize_components(react_components)
        
        ai_optimization = await self.gemini_service.optimize_component_structure(
            optimization_result['component_optimizations']
        )
        
        return {
            'optimization_analysis': optimization_result,
            'ai_optimizations': ai_optimization,
            'optimizations_applied': len(optimization_result.get('component_optimizations', {})),
            'performance_improvements': optimization_result.get('optimization_summary', {})
        }

    async def _finalize_project(self, optimization_result: Dict, job_id: str) -> Dict:
        self.logger.info("Finalizing React project")
        
        project_path = f"app/static/{job_id}_react"
        zip_path = f"app/static/{job_id}_react.zip"
        
        if not os.path.exists(zip_path):
            self.logger.warning(f"React project zip not found at {zip_path}")
            return {'error': 'Project zip file not found'}
        
        file_size = os.path.getsize(zip_path) if os.path.exists(zip_path) else 0
        
        return {
            'project_path': project_path,
            'zip_path': zip_path,
            'download_url': f'/download/{job_id}_react',
            'file_size_mb': round(file_size / (1024 * 1024), 2),
            'project_ready': True,
            'completion_time': datetime.now().isoformat()
        }

    def _calculate_ai_confidence(self, component_analysis: Dict) -> float:
        confidence_factors = {
            'has_component_hierarchy': 0.3 if component_analysis.get('component_hierarchy') else 0,
            'has_reusable_components': 0.2 if component_analysis.get('reusable_components') else 0,
            'has_design_tokens': 0.2 if component_analysis.get('design_tokens') else 0,
            'component_count': min(len(component_analysis.get('component_hierarchy', [])) * 0.05, 0.3)
        }
        
        return min(sum(confidence_factors.values()), 1.0)

    def _generate_conversion_stats(self, final_result: Dict) -> Dict:
        return {
            'conversion_completed_at': datetime.now().isoformat(),
            'project_size_mb': final_result.get('file_size_mb', 0),
            'download_ready': final_result.get('project_ready', False),
            'estimated_lines_of_code': final_result.get('file_size_mb', 0) * 50,
            'framework': 'Next.js',
            'language': 'TypeScript',
            'styling': 'CSS Modules + Tailwind CSS'
        }

    async def get_conversion_status(self, job_id: str) -> Dict:
        project_zip = f"app/static/{job_id}_react.zip"
        
        if os.path.exists(project_zip):
            file_size = os.path.getsize(project_zip)
            return {
                'status': 'completed',
                'ready_for_download': True,
                'file_size_mb': round(file_size / (1024 * 1024), 2),
                'download_url': f'/download/{job_id}_react'
            }
        else:
            return {
                'status': 'processing',
                'ready_for_download': False,
                'estimated_completion': '2-3 minutes'
            }
    def _ensure_json_serializable(self, obj):
        """Convert any BeautifulSoup objects to JSON-serializable formats"""
        try:
            if isinstance(obj, (Tag, NavigableString)):
                return str(obj)
            elif isinstance(obj, dict):
                return {k: self._ensure_json_serializable(v) for k, v in obj.items()}
            elif isinstance(obj, (list, tuple)):
                return [self._ensure_json_serializable(item) for item in obj]
            elif hasattr(obj, '__dict__') and not isinstance(obj, (str, int, float, bool, type(None))):
                return str(obj)
            return obj
        except Exception as e:
            self.logger.error(f"Serialization error: {e}")
            return str(obj)
