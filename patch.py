import os
filepath = r'bolsa_empleo/settings.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

apps_old = '''    'django.contrib.postgres',
    'core',
]'''
apps_new = '''    'django.contrib.postgres',
    'cloudinary_storage',
    'cloudinary',
    'core',
]'''
content = content.replace(apps_old, apps_new)

media_old = '''MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'staticfiles_build', 'media')'''

media_new = '''MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'staticfiles_build', 'media')

import cloudinary
import cloudinary.uploader
import cloudinary.api

CLOUDINARY_STORAGE = {
    'CLOUDINARY_URL': os.environ.get('CLOUDINARY_URL')
}
if os.environ.get('CLOUDINARY_URL'):
    DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'
'''
content = content.replace(media_old, media_new)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
print("Settings successfully patched!")
