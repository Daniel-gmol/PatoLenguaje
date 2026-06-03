import glob
import os

files = glob.glob('tests/**/*.pt', recursive=True)
for f in files:
    with open(f, 'r') as file:
        content = file.read()
    if '};' in content:
        content = content.replace('};', '}')
        with open(f, 'w') as file:
            file.write(content)
        print(f"Fixed {f}")
