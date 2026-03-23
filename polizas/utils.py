# utils.py
import re
import unicodedata

def normalize_name(s):
    print('s*******+',s)
    if not s:
        return ''
    s = unicodedata.normalize('NFD', s)
    s = ''.join(ch for ch in s if unicodedata.category(ch) != 'Mn')  # quita acentos
    s = s.upper()
    s = re.sub(r'[^A-Z0-9 ]+', ' ', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s
