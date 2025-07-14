import os

folder = 'logo'  # 你项目中的 logo 文件夹名

with open(os.path.join(folder, 'preview.md'), 'w', encoding='utf-8') as f:
    f.write('# EPG 项目 Logo 预览\n\n')
    for filename in sorted(os.listdir(folder)):
        if filename.lower().endswith('.png'):
            # 注意路径是相对于 preview.md 的
            f.write(f'![{filename}](./{filename})\n\n')
