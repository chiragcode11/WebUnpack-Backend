import os
import json
from typing import Dict, List, Optional
from pathlib import Path
import zipfile
from datetime import datetime
import re

class ReactCodeGenerator:
    def __init__(self):
        self.template_mapping = {
            'functional_component': self._generate_functional_component,
            'button': self._generate_button_component,
            'card': self._generate_card_component,
            'form': self._generate_form_component,
            'navigation': self._generate_navigation_component,
            'layout': self._generate_layout_component
        }

    def generate_react_project(self, components_data: Dict, job_id: str) -> Dict:
        project_path = Path(f"app/static/{job_id}_react")
        project_path.mkdir(parents=True, exist_ok=True)

        project_structure = self._create_project_structure(project_path)
        
        generated_files = self._generate_all_components(components_data, project_path)
        
        self._generate_package_json(project_path, components_data.get('package_dependencies', []))
        self._generate_tsconfig(project_path)
        self._generate_next_config(project_path)
        self._generate_tailwind_config(project_path)
        self._generate_readme(project_path, components_data)
        
        zip_path = self._create_project_zip(project_path, job_id)
        
        return {
            'success': True,
            'project_path': str(project_path),
            'zip_path': zip_path,
            'files_generated': len(generated_files),
            'components_created': len(components_data.get('components', {})),
            'project_structure': project_structure
        }

    def _create_project_structure(self, project_path: Path) -> Dict:
        structure = {
            'src/': {
                'components/': {},
                'pages/': {},
                'styles/': {},
                'types/': {},
                'hooks/': {},
                'utils/': {},
                'lib/': {}
            },
            'public/': {},
            'tests/': {}
        }
        
        for path_str in self._flatten_structure(structure):
            full_path = project_path / path_str
            full_path.mkdir(parents=True, exist_ok=True)
        
        return structure

    def _flatten_structure(self, structure: Dict, prefix: str = '') -> List[str]:
        paths = []
        for key, value in structure.items():
            current_path = prefix + key
            paths.append(current_path)
            if isinstance(value, dict) and value:
                paths.extend(self._flatten_structure(value, current_path))
        return paths

    def _generate_all_components(self, components_data: Dict, project_path: Path) -> List[str]:
        generated_files = []
        components = components_data.get('components', {})
        
        for component_name, component_data in components.items():
            component_files = self._generate_component_files(
                component_name, component_data, project_path
            )
            generated_files.extend(component_files)
        
        self._generate_index_file(project_path, list(components.keys()))
        self._generate_app_component(project_path, components_data)
        
        return generated_files

    def _generate_component_files(self, component_name: str, component_data: Dict, project_path: Path) -> List[str]:
        component_dir = project_path / 'src' / 'components' / component_name
        component_dir.mkdir(parents=True, exist_ok=True)
        
        files_created = []
        
        tsx_file = component_dir / f'{component_name}.tsx'
        with open(tsx_file, 'w', encoding='utf-8') as f:
            f.write(self._clean_code_block(component_data.get('tsx', '')))
        files_created.append(str(tsx_file))
        
        css_file = component_dir / f'{component_name}.module.css'
        with open(css_file, 'w', encoding='utf-8') as f:
            f.write(self._clean_code_block(component_data.get('css', '')))
        files_created.append(str(css_file))
        
        types_file = component_dir / 'types.ts'
        with open(types_file, 'w', encoding='utf-8') as f:
            f.write(self._clean_code_block(component_data.get('types', '')))
        files_created.append(str(types_file))
        
        test_file = component_dir / f'{component_name}.test.tsx'
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(self._clean_code_block(component_data.get('test', '')))
        files_created.append(str(test_file))
        
        index_file = component_dir / 'index.ts'
        with open(index_file, 'w', encoding='utf-8') as f:
            f.write(f"export {{ default }} from './{component_name}';\nexport * from './types';")
        files_created.append(str(index_file))
        
        return files_created

    def _generate_index_file(self, project_path: Path, component_names: List[str]):
        index_file = project_path / 'src' / 'components' / 'index.ts'
        
        exports = []
        for name in component_names:
            exports.append(f"export {{ default as {name} }} from './{name}';")
        
        with open(index_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(exports))

    def _generate_app_component(self, project_path: Path, components_data: Dict):
        app_component = """import React from 'react';
import type { NextPage } from 'next';
import Head from 'next/head';
import styles from '../styles/Home.module.css';

const Home: NextPage = () => {
  return (
    <div className={styles.container}>
      <Head>
        <title>Generated React App</title>
        <meta name="description" content="Generated from HTML using AI" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <main className={styles.main}>
        <h1 className={styles.title}>
          Welcome to your generated React app!
        </h1>
        <p className={styles.description}>
          This app was automatically generated from HTML using AI
        </p>
      </main>
    </div>
  );
};

export default Home;"""
        
        pages_dir = project_path / 'src' / 'pages'
        pages_dir.mkdir(parents=True, exist_ok=True)
        
        with open(pages_dir / 'index.tsx', 'w', encoding='utf-8') as f:
            f.write(app_component)

    def _generate_package_json(self, project_path: Path, dependencies: List[str]):
        package_json = {
            "name": "generated-react-app",
            "version": "0.1.0",
            "private": True,
            "scripts": {
                "dev": "next dev",
                "build": "next build",
                "start": "next start",
                "lint": "next lint",
                "test": "jest",
                "test:watch": "jest --watch"
            },
            "dependencies": {
                "react": "^18.0.0",
                "react-dom": "^18.0.0",
                "next": "^13.0.0",
                "@types/node": "^20.0.0",
                "@types/react": "^18.0.0",
                "@types/react-dom": "^18.0.0",
                "typescript": "^5.0.0"
            },
            "devDependencies": {
                "eslint": "^8.0.0",
                "eslint-config-next": "^13.0.0",
                "@testing-library/react": "^13.0.0",
                "@testing-library/jest-dom": "^5.0.0",
                "jest": "^29.0.0",
                "jest-environment-jsdom": "^29.0.0"
            }
        }
        
        for dep in dependencies:
            if dep not in package_json["dependencies"]:
                package_json["dependencies"][dep] = "^18.0.0"
        
        with open(project_path / 'package.json', 'w', encoding='utf-8') as f:
            json.dump(package_json, f, indent=2)

    def _generate_tsconfig(self, project_path: Path):
        tsconfig = {
            "compilerOptions": {
                "target": "es5",
                "lib": ["dom", "dom.iterable", "es6"],
                "allowJs": True,
                "skipLibCheck": True,
                "strict": True,
                "forceConsistentCasingInFileNames": True,
                "noEmit": True,
                "esModuleInterop": True,
                "module": "esnext",
                "moduleResolution": "node",
                "resolveJsonModule": True,
                "isolatedModules": True,
                "jsx": "preserve",
                "incremental": True,
                "plugins": [{"name": "next"}],
                "baseUrl": ".",
                "paths": {
                    "@/*": ["./src/*"],
                    "@/components/*": ["./src/components/*"],
                    "@/styles/*": ["./src/styles/*"],
                    "@/types/*": ["./src/types/*"]
                }
            },
            "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
            "exclude": ["node_modules"]
        }
        
        with open(project_path / 'tsconfig.json', 'w', encoding='utf-8') as f:
            json.dump(tsconfig, f, indent=2)

    def _generate_next_config(self, project_path: Path):
        next_config = """/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  experimental: {
    appDir: false,
  },
  images: {
    domains: [],
  },
}

module.exports = nextConfig"""
        
        with open(project_path / 'next.config.js', 'w', encoding='utf-8') as f:
            f.write(next_config)

    def _generate_tailwind_config(self, project_path: Path):
        tailwind_config = """/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#eff6ff',
          500: '#3b82f6',
          900: '#1e3a8a',
        },
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
      },
    },
  },
  plugins: [],
}"""
        
        with open(project_path / 'tailwind.config.js', 'w', encoding='utf-8') as f:
            f.write(tailwind_config)

    def _generate_readme(self, project_path: Path, components_data: Dict):
        component_count = len(components_data.get('components', {}))
        
        readme_content = f"""# Generated React Application

This React application was automatically generated from HTML using AI.

## 📊 Generation Stats
- **Components Created**: {component_count}
- **Generated On**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **Framework**: Next.js with TypeScript

## 🚀 Getting Started

### Prerequisites
- Node.js 16+ 
- npm or yarn

### Installation
```bash
npm install
# or
yarn install
```

### Running the Development Server
```bash
npm run dev 
# or
yarn dev
```

### Building for Production
```bash
npm run build
# or
yarn build
```

## 📁 Project Structure
```
src/
├── components/     # React components
├── pages/          # Next.js pages
├── styles/         # CSS modules and global styles
├── types/          # TypeScript type definitions
├── hooks/          # Custom React hooks
└── utils/          # Utility functions
```

## 🧪 Testing
```bash
npm run test
# or
yarn test
```

## 📝 Components Generated
{chr(10).join([f"- {name}" for name in components_data.get('components', {}).keys()])}

## 🎨 Styling
This project uses CSS Modules for component-scoped styling and Tailwind CSS for utility classes.

## 🔧 Configuration
- TypeScript configuration: `tsconfig.json`
- Next.js configuration: `next.config.js`
- Tailwind configuration: `tailwind.config.js`

## 📚 Learn More
- [Next.js Documentation](https://nextjs.org/docs)
- [React Documentation](https://reactjs.org/docs)
- [TypeScript Documentation](https://www.typescriptlang.org/docs)
"""
        
        with open(project_path / 'README.md', 'w', encoding='utf-8') as f:
            f.write(readme_content)

    def _create_project_zip(self, project_path: Path, job_id: str) -> str:
        zip_path = f"app/static/{job_id}_react.zip"
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(project_path):
                for file in files:
                    file_path = Path(root) / file
                    arcname = file_path.relative_to(project_path.parent)
                    zipf.write(file_path, arcname)
        
        return zip_path

    def _clean_code_block(self, code: str) -> str:
        """Clean code blocks from markdown formatting"""
        if not code:
            return ""
        
        # Remove opening code block markers (```language or ```)
        code = re.sub(r'^```[a-z]*\n?', '', code, flags=re.MULTILINE)
        # Remove closing code block markers
        code = re.sub(r'\n?```$', '', code, flags=re.MULTILINE)
        
        lines = code.split('\n')
        # Remove leading empty line
        if lines and not lines[0].strip():
            lines = lines[1:]
        # Remove trailing empty line
        if lines and not lines[-1].strip():
            lines = lines[:-1]
        
        return '\n'.join(lines)

    def _generate_functional_component(self, name: str, props: List[str]) -> str:
        props_interface = f"{name}Props"
        
        return f"""import React from 'react';
import styles from './{name}.module.css';
import {{ {props_interface} }} from './types';

const {name}: React.FC<{props_interface}> = ({{
  {', '.join(props) if props else 'children'}
}}) => {{
  return (
    <div className={{styles.{name.lower()}}}>
      {{children}}
    </div>
  );
}};

export default {name};"""

    def _generate_button_component(self, name: str, variants: List[str]) -> str:
        return f"""import React from 'react';
import styles from './{name}.module.css';
import {{ {name}Props }} from './types';

const {name}: React.FC<{name}Props> = ({{
  children,
  variant = 'primary',
  size = 'medium',
  disabled = false,
  onClick,
  ...props
}}) => {{
  const className = [
    styles.button,
    styles[variant],
    styles[size],
    disabled && styles.disabled
  ].filter(Boolean).join(' ');

  return (
    <button
      className={{className}}
      disabled={{disabled}}
      onClick={{onClick}}
      {{...props}}
    >
      {{children}}
    </button>
  );
}};

export default {name};"""

    def _generate_card_component(self, name: str, props: List[str]) -> str:
        return f"""import React from 'react';
import styles from './{name}.module.css';
import {{ {name}Props }} from './types';

const {name}: React.FC<{name}Props> = ({{
  title,
  description,
  image,
  href,
  children,
  ...props
}}) => {{
  const CardContent = () => (
    <div className={{styles.card}} {{...props}}>
      {{image && (
        <div className={{styles.imageContainer}}>
          <img src={{image.src}} alt={{image.alt}} className={{styles.image}} />
        </div>
      )}}
      <div className={{styles.content}}>
        {{title && <h3 className={{styles.title}}>{{title}}</h3>}}
        {{description && <p className={{styles.description}}>{{description}}</p>}}
        {{children}}
      </div>
    </div>
  );

  if (href) {{
    return (
      <a href={{href}} className={{styles.cardLink}}>
        <CardContent />
      </a>
    );
  }}

  return <CardContent />;
}};

export default {name};"""

    def _generate_form_component(self, name: str, fields: List[str]) -> str:
        return f"""import React, {{ useState }} from 'react';
import styles from './{name}.module.css';
import {{ {name}Props }} from './types';

const {name}: React.FC<{name}Props> = ({{
  onSubmit,
  children,
  ...props
}}) => {{
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {{
    e.preventDefault();
    if (isSubmitting) return;

    setIsSubmitting(true);
    try {{
      if (onSubmit) {{
        await onSubmit(e);
      }}
    }} finally {{
      setIsSubmitting(false);
    }}
  }};

  return (
    <form
      className={{styles.form}}
      onSubmit={{handleSubmit}}
      {{...props}}
    >
      {{children}}
      <button
        type="submit"
        disabled={{isSubmitting}}
        className={{styles.submitButton}}
      >
        {{isSubmitting ? 'Submitting...' : 'Submit'}}
      </button>
    </form>
  );
}};

export default {name};"""

    def _generate_navigation_component(self, name: str, links: List[str]) -> str:
        return f"""import React, {{ useState }} from 'react';
import Link from 'next/link';
import styles from './{name}.module.css';
import {{ {name}Props }} from './types';

const {name}: React.FC<{name}Props> = ({{
  links,
  logo,
  className,
  ...props
}}) => {{
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  return (
    <nav className={{`${{styles.nav}} ${{className || ''}}`}} {{...props}}>
      <div className={{styles.container}}>
        {{logo && (
          <Link href="/" className={{styles.logo}}>
            {{typeof logo === 'string' ? <span>{{logo}}</span> : logo}}
          </Link>
        )}}

        <button
          className={{styles.menuToggle}}
          onClick={{() => setIsMenuOpen(!isMenuOpen)}}
          aria-label="Toggle menu"
        >
          <span></span>
          <span></span>
          <span></span>
        </button>

        <div className={{`${{styles.menu}} ${{isMenuOpen ? styles.menuOpen : ''}}`}}>
          {{links.map((link, index) => (
            <Link
              key={{index}}
              href={{link.href}}
              className={{styles.link}}
              onClick={{() => setIsMenuOpen(false)}}
            >
              {{link.label}}
            </Link>
          ))}}
        </div>
      </div>
    </nav>
  );
}};

export default {name};"""

    def _generate_layout_component(self, name: str, sections: List[str]) -> str:
        return f"""import React from 'react';
import Head from 'next/head';
import styles from './{name}.module.css';
import {{ {name}Props }} from './types';

const {name}: React.FC<{name}Props> = ({{
  children,
  title = 'Generated React App',
  description = 'AI-generated React application',
  className,
  ...props
}}) => {{
  return (
    <>
      <Head>
        <title>{{title}}</title>
        <meta name="description" content={{description}} />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="icon" href="/favicon.ico" />
      </Head>
      <div className={{`${{styles.layout}} ${{className || ''}}`}} {{...props}}>
        {{children}}
      </div>
    </>
  );
}};

export default {name};"""