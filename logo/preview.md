import os

folder = 'images'
with open(os.path.join(folder, 'preview.md'), 'w') as f:
    f.write('# 图片预览\n\n')
    for filename in os.listdir(folder):
        if filename.lower().endswith('.png'):
            f.write(f'![{filename}](./{filename})\n')
