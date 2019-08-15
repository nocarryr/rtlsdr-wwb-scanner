import os
import io
import shutil
import zipfile

# requests is a kivy dependency already
import requests

from kivy.garden import iconfonts

BASE_PATH = os.path.dirname(os.path.abspath(__file__))
FONT_PATH = os.path.join(BASE_PATH, 'fonts')

ZIP_URL = 'https://github.com/FortAwesome/Font-Awesome/archive/master.zip'

def get_fontawesome():
    if not os.path.exists(FONT_PATH):
        os.makedirs(FONT_PATH)
    r = requests.get(ZIP_URL)
    assert r.ok
    zip_fn = os.path.join(FONT_PATH, 'font-awesome.zip')
    with open(zip_fn, 'wb') as f:
        #f.write(io.BytesIO(r.content))
        f.write(r.content)

    with zipfile.ZipFile(zip_fn) as zf:
        inf_list = zf.infolist()
        root = inf_list[0].filename
        p = ''.join([root, 'fonts'])
        l = [o for o in inf_list if o.filename.startswith(p) and o.filename.endswith('.ttf')]
        p = ''.join([root, 'css'])
        l.extend([o for o in inf_list if o.filename.startswith(p) and o.filename.endswith('.css')])
        for zinf in l:
            zf.extract(zinf, FONT_PATH)
            zfn = os.path.join(FONT_PATH, zinf.filename)
            new_fn = os.path.join(FONT_PATH, os.path.basename(zinf.filename))
            shutil.move(zfn, new_fn)
    shutil.rmtree(os.path.join(FONT_PATH, root))
    os.remove(zip_fn)


def build_fontd():
    fn = os.path.join(FONT_PATH, 'font-awesome.css')
    fn_d = os.path.join(FONT_PATH, 'font-awesome.fontd')
    if not os.path.exists(fn):
        get_fontawesome()
    iconfonts.create_fontdict_file(fn, fn_d)

if __name__ == '__main__':
    build_fontd()
