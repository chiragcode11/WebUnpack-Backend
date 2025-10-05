import google.generativeai as genai
import json
import re
from typing import Dict, List, Optional
import logging
import asyncio
from datetime import datetime

class GeminiAIService:
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        # Configure with timeout and generation settings
        self.generation_config = {
            "temperature": 0.7,
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 8192,
        }
        self.model = genai.GenerativeModel(
            'gemini-2.0-flash-exp',
            generation_config=self.generation_config
        )
        self.logger = logging.getLogger(__name__)
        self.timeout = 120  # 2 minutes timeout

    async def analyze_components(self, semantic_html: str, patterns: Dict, css_analysis: Dict) -> Dict:
        # Truncate large inputs to avoid timeouts
        semantic_html = self._truncate_html(semantic_html, max_chars=15000)
        
        prompt = self._build_component_analysis_prompt(semantic_html, patterns, css_analysis)
        
        try:
            response = await self._generate_content_with_timeout(prompt, timeout=90)
            return self._parse_component_analysis(response.text)
        except asyncio.TimeoutError:
            self.logger.error("Component analysis timed out, using fallback")
            return self._fallback_component_analysis()
        except Exception as e:
            self.logger.error(f"Component analysis failed: {e}")
            return self._fallback_component_analysis()

    async def generate_react_components(self, component_analysis: Dict, design_tokens: Dict) -> Dict:
        prompt = self._build_react_generation_prompt(component_analysis, design_tokens)
        
        try:
            response = await self._generate_content_with_timeout(prompt, timeout=120)
            return self._parse_react_components(response.text)
        except asyncio.TimeoutError:
            self.logger.error("React generation timed out, using fallback")
            return self._fallback_react_generation()
        except Exception as e:
            self.logger.error(f"React generation failed: {e}")
            return self._fallback_react_generation()

    async def optimize_component_structure(self, components: Dict) -> Dict:
        prompt = self._build_optimization_prompt(components)
        
        try:
            response = await self._generate_content_with_timeout(prompt, timeout=90)
            return self._parse_optimizations(response.text)
        except Exception as e:
            self.logger.error(f"Optimization failed: {e}")
            return components

    async def generate_typescript_interfaces(self, components: Dict) -> Dict:
        prompt = self._build_typescript_prompt(components)
        
        try:
            response = await self._generate_content_with_timeout(prompt, timeout=60)
            return self._parse_typescript_interfaces(response.text)
        except Exception as e:
            self.logger.error(f"TypeScript generation failed: {e}")
            return self._fallback_typescript_interfaces()

    def _truncate_html(self, html: str, max_chars: int = 15000) -> str:
        """Truncate HTML to prevent token limit issues"""
        if len(html) <= max_chars:
            return html
        
        self.logger.warning(f"Truncating HTML from {len(html)} to {max_chars} chars")
        return html[:max_chars] + "\n<!-- ... truncated ... -->"

    def _build_component_analysis_prompt(self, semantic_html: str, patterns: Dict, css_analysis: Dict) -> str:
        return f"""
Analyze this semantic HTML structure and identify React components.

IMPORTANT: Return ONLY valid JSON without any markdown code blocks or extra text.

SEMANTIC HTML:
{semantic_html[:5000]}

DETECTED PATTERNS:
{json.dumps(patterns, indent=2)[:1000]}

CSS ANALYSIS:
{json.dumps(css_analysis, indent=2)[:1000]}

Return a JSON object with this exact structure (no markdown, just JSON):
{{
  "component_hierarchy": [
    {{
      "name": "ComponentName",
      "type": "functional",
      "props": ["prop1", "prop2"],
      "children": ["ChildComponent"],
      "reusable": true,
      "has_state": false,
      "styling": "css_modules"
    }}
  ],
  "reusable_components": [
    {{
      "name": "Button",
      "variants": ["primary", "secondary"],
      "props": ["children", "onClick", "variant", "disabled"]
    }}
  ],
  "design_tokens": {{
    "colors": {{"primary": "#007bff", "secondary": "#6c757d"}},
    "spacing": [4, 8, 16, 24, 32],
    "typography": {{"heading": "2rem", "body": "1rem"}}
  }}
}}
"""

    def _build_react_generation_prompt(self, component_analysis: Dict, design_tokens: Dict) -> str:
        return f"""
Generate TypeScript React components based on this analysis.

IMPORTANT: Return ONLY valid JSON without any markdown code blocks or extra text.

COMPONENT ANALYSIS:
{json.dumps(component_analysis, indent=2)[:3000]}

DESIGN TOKENS:
{json.dumps(design_tokens, indent=2)[:1000]}

Return a JSON object with this exact structure:
{{
  "components": {{
    "ComponentName": {{
      "tsx": "complete component code",
      "css": "complete css module code",
      "types": "typescript interfaces",
      "test": "jest test code"
    }}
  }},
  "index": "export statements",
  "package_dependencies": ["react", "@types/react"],
  "folder_structure": {{
    "components/": ["Button/", "Card/"],
    "types/": ["index.ts"],
    "styles/": ["globals.css"]
  }}
}}
"""

    def _build_optimization_prompt(self, components: Dict) -> str:
        return f"""
Optimize these React components for performance.

IMPORTANT: Return ONLY valid JSON without any markdown code blocks.

COMPONENTS:
{json.dumps(components, indent=2)[:3000]}

Return a JSON object with optimized components and performance notes.
"""

    def _build_typescript_prompt(self, components: Dict) -> str:
        return f"""
Generate TypeScript interfaces for these components.

IMPORTANT: Return ONLY valid JSON without any markdown code blocks.

COMPONENTS:
{json.dumps(components, indent=2)[:2000]}

Return a JSON object with interface definitions.
"""

    async def _generate_content_with_timeout(self, prompt: str, timeout: int = 90):
        """Generate content with timeout handling"""
        try:
            return await asyncio.wait_for(
                self._generate_content_async(prompt),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            self.logger.error(f"Generation timed out after {timeout} seconds")
            raise

    async def _generate_content_async(self, prompt: str):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.model.generate_content, prompt)

    def _clean_json_response(self, response_text: str) -> str:
        """Clean and extract JSON from response text"""
        # Remove markdown code blocks
        response_text = re.sub(r'```json\s*', '', response_text)
        response_text = re.sub(r'```\s*', '', response_text)
        
        # Find JSON object
        start_idx = response_text.find('{')
        end_idx = response_text.rfind('}') + 1
        
        if start_idx == -1 or end_idx == 0:
            raise ValueError("No JSON object found in response")
        
        json_str = response_text[start_idx:end_idx]
        
        # Fix common JSON issues
        # Replace single quotes with double quotes (careful with content)
        json_str = re.sub(r"'([^']*)':", r'"\1":', json_str)
        
        # Remove trailing commas
        json_str = re.sub(r',\s*([}\]])', r'\1', json_str)
        
        return json_str

    def _parse_component_analysis(self, response_text: str) -> Dict:
        try:
            json_str = self._clean_json_response(response_text)
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON decode error: {e}")
            self.logger.debug(f"Response text: {response_text[:500]}")
            return self._fallback_component_analysis()
        except Exception as e:
            self.logger.error(f"Failed to parse component analysis: {e}")
            return self._fallback_component_analysis()

    def _parse_react_components(self, response_text: str) -> Dict:
        try:
            json_str = self._clean_json_response(response_text)
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON decode error in React components: {e}")
            self.logger.debug(f"Response text: {response_text[:500]}")
            return self._fallback_react_generation()
        except Exception as e:
            self.logger.error(f"Failed to parse React components: {e}")
            return self._fallback_react_generation()

    def _parse_optimizations(self, response_text: str) -> Dict:
        try:
            json_str = self._clean_json_response(response_text)
            return json.loads(json_str)
        except Exception as e:
            self.logger.error(f"Failed to parse optimizations: {e}")
            return {}

    def _parse_typescript_interfaces(self, response_text: str) -> Dict:
        try:
            json_str = self._clean_json_response(response_text)
            parsed = json.loads(json_str)
            return parsed
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON decode error in TypeScript interfaces: {e}")
            self.logger.debug(f"Response text: {response_text[:500]}")
            return self._fallback_typescript_interfaces()
        except Exception as e:
            self.logger.error(f"Failed to parse TypeScript interfaces: {e}")
            return self._fallback_typescript_interfaces()

    def _fallback_component_analysis(self) -> Dict:
        return {
            "component_hierarchy": [
                {
                    "name": "App",
                    "type": "functional",
                    "props": [],
                    "children": ["Header", "Main", "Footer"],
                    "reusable": False,
                    "has_state": True,
                    "styling": "css_modules"
                }
            ],
            "reusable_components": [
                {
                    "name": "Button",
                    "variants": ["primary", "secondary"],
                    "props": ["children", "onClick", "variant"]
                }
            ],
            "design_tokens": {
                "colors": {"primary": "#007bff", "secondary": "#6c757d"},
                "spacing": [8, 16, 24, 32],
                "typography": {"heading": "1.5rem", "body": "1rem"}
            }
        }

    def _fallback_react_generation(self) -> Dict:
        return {
            "components": {
                "App": {
                    "tsx": "import React from 'react';\n\nconst App = () => {\n  return <div>Generated Component</div>;\n};\n\nexport default App;",
                    "css": ".app { padding: 1rem; }",
                    "types": "export interface AppProps {}",
                    "test": "import { render } from '@testing-library/react';\nimport App from './App';\n\ntest('renders app', () => {\n  render(<App />);\n});"
                }
            },
            "index": "export { default as App } from './App';",
            "package_dependencies": ["react", "@types/react"],
            "folder_structure": {
                "components/": ["App/"],
                "types/": ["index.ts"]
            }
        }

    def _fallback_typescript_interfaces(self) -> Dict:
        return {
            "interfaces": {
                "props": {
                    "BaseProps": "interface BaseProps { children?: React.ReactNode; className?: string; }"
                }
            },
            "utility_types": {
                "ComponentVariant": "type ComponentVariant = 'primary' | 'secondary';"
            }
        }