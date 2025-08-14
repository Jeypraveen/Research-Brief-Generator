import os

# Define the project structure
project_structure = {
    'RA': {
        'src': {
            '__init__.py': '',
            'config.py': '',
            'state.py': '',
            'nodes.py': '',
            'workflow.py': '',
            'tools.py': '',
            'schemas.py': ''
        },
        'web_app': {
            '__init__.py': '',
            'app.py': '',
            'templates': {
                'index.html': '',
                'brief.html': ''
            },
            'static': {
                'css': {
                    'style.css': ''
                },
                'js': {
                    'app.js': ''
                }
            }
        },
        'tests': {
            '__init__.py': '',
            'test_workflow.py': '',
            'test_nodes.py': ''
        },
        'api': {
            '__init__.py': '',
            'api.py': ''
        }
    }
}

# Function to create folders and files
def create_structure(base_path, structure):
    for name, content in structure.items():
        path = os.path.join(base_path, name)
        if isinstance(content, dict):
            os.makedirs(path, exist_ok=True)
            create_structure(path, content)
        else:
            with open(path, 'w') as f:
                f.write(content)
            print(f"📄 Created file: {path}")

# Base location for the project
base_path = r"C:\Projects"  # Windows path
os.makedirs(base_path, exist_ok=True)

# Create the RA project inside C:\Projects
create_structure(base_path, project_structure)

print("\n✅ Project structure for 'RA' created successfully in C:\\Projects!")
