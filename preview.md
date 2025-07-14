import os

folder = 'logo'

with open(os.path.join(folder, 'preview.md'), 'w', encoding='utf-8') as f:
    f.write('# EPG 项目 Logo 预览\n\n')
    for filename in sorted(os.listdir(folder)):
        if filename.lower().endswith('.png'):
            f.write(f'![{filename}](./{filename})\n\n')
