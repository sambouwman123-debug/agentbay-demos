"""v3 build: normalize.py configs + echte Google Maps-gegevens uit v2data/<slug>.json.
Gebruik: python3 build_v3.py [slug ...]   -> bouwt naar out/<slug>/ en schrijft v2b/<slug>.json (deploy-payload).
Alleen feiten uit v2data; niets wordt verzonnen. Ontbreekt iets, dan blijft die sectie weg."""
import sys, os, json, re, shutil, hashlib, base64, urllib.request, concurrent.futures as cf
CACHE = '/home/claude/imgcache'
os.makedirs(CACHE, exist_ok=True)
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import normalize, gen_v2

MIN_COUNT = 3  # Google-score pas tonen vanaf 3 reviews
MIN_RATING = 4.5  # lagere scores laten we weg (niet verzonnen, alleen niet getoond)
CLAIM = re.compile(r'volger|volgen de|review|beoordeel|sterren|Trustoo|Treatwell|Telefoonboek|Stukadoorgids|Pedicure\.nl|Salonkee|Google|waarder|best bezochte|\b[1-9],\d\b|\b\d+ keer\b', re.I)
SKIP = {'reviews','photo','gallery','maps','book','phone','hours','addr','tok','dark','fonts','alt','slug','cat','tags','trust','usps','proof','about_photo','socials','name','title','logo'}
H1 = {
 'barbershop-yazan':'Strak geknipt <em>bij Yazan.</em>', 'mido-barbershop':'Precisie, rust <em>en een strakke coupe.</em>',
 'house-of-nofa':'Mooie nagels, <em>zeven dagen per week.</em>', 'barbershop-t-pleintje':'Strak geknipt <em>in Renkum.</em>',
 'barbershop-veenendaal':'Strak geknipt <em>in Veenendaal.</em>', 'elegant-barbershop':'Elegant geknipt <em>in Den Bosch.</em>',
 'barber-sam-gouda':'Strak geknipt <em>bij Sam.</em>', 'unique-nails-hengelo':'Uniek, <em>tot in elk detail.</em>',
 'antonina-beauty-nails':'Nagels en pedicure, <em>met aandacht.</em>', 'nails-beauty-aridj':'Nagels, brows en lashes, <em>één adres.</em>',
 'vikkis-beauty-world':'Lashes, brows <em>en nails.</em>', 'ruiter-tuin-timmer':'Tuinwerk en houtwerk, <em>in één hand.</em>',
 'lashmazing-enschede':'Wimpers, <em>helemaal lashmazing.</em>',
 'barbershop-de-schaar':'Strak geknipt <em>in \'s-Heerenberg.</em>', 'barbershop-tiel':'Strak geknipt <em>in Tiel.</em>',
 'salon-blush-gendt':'Mooi worden, <em>in Gendt.</em>', 'petra-pedicure-arnhem':'Zorg voor je voeten, <em>met aandacht.</em>',
 'nima-schildersbedrijf':'Strak geschilderd, <em>binnen en buiten.</em>', 'unique-barber-ede':'Uniek geknipt <em>in Ede.</em>',
 'maryam-pedicure-oss':'Medisch pedicure, <em>met zorg.</em>', 'redka-stucadoors':'Strakke wanden <em>en plafonds.</em>',
}
QUOTE = {'timmerbedrijf-joor':'Timmerwerk en glaszetten, met een klein team.','nima-schildersbedrijf':'Strak schilderwerk, binnen en buiten.',
 'trimsalon-beautify-duiven':'Elke hond krijgt de tijd en rust die hij nodig heeft.'}

def verified(d):
    try: r = float((d.get('rating') or '0').replace(',', '.'))
    except ValueError: r = 0
    return d.get('status') == 'ok' and d.get('rating_count', 0) >= MIN_COUNT and r >= MIN_RATING

def clean_text(v):
    """Verwijder zinnen met (niet-geverifieerde) score/review-claims; laat de rest staan."""
    def sents(t):
        parts = re.split(r'(?<=[.!?])\s+', t)
        return ' '.join(p for p in parts if not CLAIM.search(re.sub(r'<[^>]+>', '', p))).strip()
    if '<p>' in v:
        ps = re.findall(r'<p>(.*?)</p>', v, re.S)
        ps = [sents(p) for p in ps]
        return ''.join(f'<p>{p}</p>' for p in ps if p)
    return sents(v)

def sanitize(c, d):
    c = dict(c)
    for k, v in list(c.items()):
        if k in SKIP or not isinstance(v, str) or not CLAIM.search(re.sub(r'<[^>]+>', '', v)): continue
        c[k] = clean_text(v)
    if c['slug'] in H1: c['h1'] = H1[c['slug']]
    if c['slug'] in QUOTE: c['quote'] = QUOTE[c['slug']]
    bad = lambda a, b: CLAIM.search(gen_v2.strip(a) + ' ' + gen_v2.strip(b)) or re.fullmatch(r'[\d,.+]+', gen_v2.strip(a)) and re.search(r'klant|keer', b)
    c['trust'] = [t for t in c.get('trust', []) if not bad(*t)]
    c['usps'] = [u for u in c.get('usps', []) if not bad(*u)]
    spans = re.findall(r'<span>.*?</span>', c.get('proof', ''))
    spans = [x for x in spans if not CLAIM.search(gen_v2.strip(x))]
    if verified(d):
        spans = [f"<span><b>{d['rating']}</b> uit {d['rating_count']} Google-reviews</span>"] + spans
    c['proof'] = ''.join(spans[:3])
    c.pop('rating', None); c.pop('rating_count', None)
    return c

def apply_photos(c, hero, gallery, about=None, alt=None):
    if hero:
        c['photo'] = hero; c['alt'] = alt or f"{c['name']} in {c.get('place') or ''}".strip(); c['pos'] = 'center'
    if gallery: c['gallery'] = gallery
    if about: c['about_photo'] = about; c['about_alt'] = c['name']
    P = []
    for u in [hero] + (gallery or []) + [about]:
        if u and u not in P: P.append(u)
    if hero and len(P) >= 3: c['hero2'] = P[1]
    if len(P) >= 2: c['home_about_photo'] = about or P[1]
    if len(P) >= 5: c['svc_photo'] = P[3]
    if len(P) >= 6: c['steps_photo'] = P[4]
    return c

def apply_fb(c, d):
    fb = d.get('fb')
    if not fb or d.get('gallery'): return c
    c = apply_photos(c, fb.get('hero'), fb.get('gallery'))
    c['gallery_src'] = 'Foto’s van de eigen Facebook-pagina'
    if fb.get('followers'):
        c['usps'] = [(str(fb['followers']), 'volgers op Facebook')] + c.get('usps', [])[:3]
    so = dict(c.get('socials') or {}); so.setdefault('facebook', fb['url']); c['socials'] = so
    return c

STOP={'en','met','van','voor','de','het','een','in','op','je','jouw','of','tot','uit','bij','aan','nieuwe','klassieke','complete','extra'}
SYN={'fade':['fade','fades'],'knip':['knip','geknipt','kapsel','coupe','haar'],'baard':['baard'],'nagel':['nagel','nagels','gellak','biab'],
 'gellak':['gellak','nagels'],'biab':['biab'],'pedicure':['pedicure','voet','voeten','nagels'],'manicure':['manicure','handen','nagels'],
 'wimper':['wimper','lash','lashes'],'lash':['lash','wimper'],'brow':['brow','wenkbrauw'],'wenkbrauw':['wenkbrauw','brow'],
 'gezicht':['gezicht','huid','behandeling'],'massage':['massage','ontspann'],'tuin':['tuin','hovenier','border','snoei','gras','bestrating','terras'],
 'schilder':['schilder','geschilderd','verf','lak'],'stuc':['stuc','muren','muur','plafond','wanden'],'trim':['trim','getrimd','vacht','hond'],
 'wassen':['gewassen','wassen','vacht'],'kleur':['kleur','highlights','blond'],'scheer':['scheer','geschoren','scheren'],'kind':['kind','zoon','zoontje','dochter','kids','jongens'],
 'timmer':['timmer','hout','schutting','overkapping'],'kozijn':['kozijn','deur','raam']}
def svc_quotes(c, reviews):
    if not reviews: return c
    sents=[]
    for r in reviews:
        for sn in re.split(r'(?<=[.!?])\s+|\n+', r['text']):
            sn=sn.strip()
            if not (25<=len(sn)<=120): continue
            if not sn[0].isupper() and not sn[0].isdigit(): continue
            if re.match(r'(En|Maar|Zeker gezien|Ook|Dus|Want|Daarom|Omdat|Toen|Als|Wel|Nou|Echter|Verder|Tevens)\b',sn): continue
            if not re.search(r'top|super|blij|tevreden|mooi|netjes|strak|aanrader|fijn|goed|vakkundig|geweldig|perfect|prachtig|heerlijk|knap|beste|vakman|professioneel|vriendelijk|lekker|aan te raden|zorgvuldig',sn.lower()): continue
            sents.append((sn,r['name']))
    used=set(); svcs=[]
    for s in c.get('services',[]):
        s=dict(s); s.pop('quote',None)
        words=[w for w in re.findall(r'[a-zà-ÿ]+',s['name'].lower()) if w not in STOP and len(w)>=3]
        keys=set()
        for w in words:
            for k,v in SYN.items():
                if w.startswith(k) or k in w: keys.update(v)
        for w in re.findall(r'[a-zà-ÿ]+',s['name'].lower()):
            if len(w)>=5 and w not in STOP: keys.add(w[:6])
        best=None
        for sn,n in sents:
            if sn in used: continue
            low=sn.lower()
            if any(k in low for k in keys): best=(sn,n); break
        if best: used.add(best[0]); s['quote']={'text':best[0],'name':best[1]}
        svcs.append(s)
    c['services']=svcs
    return c

def overlay(c, d):
    c = sanitize(c, d)
    c = apply_fb(c, d)
    if d.get('status') != 'ok':
        c['no_rating'] = True
        for k, v in (d.get('copy') or {}).items(): c[k] = v
        return c
    c['maps'] = d['maps_url']
    if verified(d):
        c['g_rating'] = d['rating']; c['g_count'] = d['rating_count']
        rt = f"{d['rating']}"
        # trust: Google-score vooraan, oude score-items eruit
        tr = [t for t in c.get('trust', []) if not re.search(r'review|Google|Werkspot', gen_v2.strip(t[0]) + ' ' + gen_v2.strip(t[1]))
              and not re.fullmatch(r'[\d,]+', gen_v2.strip(t[0]))]
        c['trust'] = [(rt, f"uit {d['rating_count']} Google-reviews")] + tr[:3]
        us = [u for u in c.get('usps', []) if not re.search(r'review|Google', u[1]) and not re.fullmatch(r'[\d,]+', gen_v2.strip(u[0]))]
        c['usps'] = [(rt, 'op Google'), (str(d['rating_count']), 'reviews')] + us[:2]
    else:
        c['no_rating'] = True
    if d.get('reviews'): c['reviews'] = d['reviews']; c = svc_quotes(c, d['reviews'])
    c = apply_photos(c, d.get('hero'), d.get('gallery'), d.get('about_photo'), d.get('hero_alt'))
    rv = [r for r in (d.get('reviews') or []) if 40 <= len(r['text']) <= 170 and '\n' not in r['text'].strip()]
    if rv: c['band_review'] = sorted(rv, key=lambda r: abs(len(r['text']) - 100))[0]
    if d.get('hours'): c['hours'] = d['hours']
    if d.get('socials'): c['socials'] = d['socials']
    c['trust'] = [(a, b.lstrip(', ').capitalize() if b.startswith(',') else b) for a, b in c.get('trust', [])]
    for k, v in (d.get('copy') or {}).items(): c[k] = v
    for k in ('gallery_h', 'gallery_label', 'reviews_h', 'hm_h'):
        if d.get(k): c[k] = d[k]
    return c

def pack(outdir):
    files = []
    for r, _, fs in os.walk(outdir):
        for f in sorted(fs):
            p = os.path.join(r, f)
            if f.endswith('.jpg'):
                files.append({'file': os.path.relpath(p, outdir), 'data': base64.b64encode(open(p, 'rb').read()).decode(), 'encoding': 'base64'})
            else:
                files.append({'file': os.path.relpath(p, outdir), 'data': open(p).read()})
    return files

IMG_KEYS = ('photo', 'hero2', 'about_photo', 'home_about_photo', 'svc_photo', 'steps_photo')

def fetch(u, w):
    if u.startswith('/'):
        fn = os.path.join(CACHE, hashlib.md5(u.encode()).hexdigest() + f'_{w}.jpg')
        if not os.path.exists(fn):
            from PIL import Image
            im = Image.open(u).convert('RGB'); im.thumbnail((w, w)); im.save(fn, 'JPEG', quality=78, optimize=True, progressive=True)
        return fn
    base = u.split('=')[0]
    fn = os.path.join(CACHE, hashlib.md5(base.encode()).hexdigest() + f'_{w}.jpg')
    if not os.path.exists(fn) or os.path.getsize(fn) < 2000:
        for _ in range(3):
            try:
                data = urllib.request.urlopen(urllib.request.Request(f'{base}=w{w}', headers={'User-Agent': 'Mozilla/5.0'}), timeout=30).read()
                if data[:2] == b'\xff\xd8' or data[:4] == b'\x89PNG' or data[:4] == b'RIFF':
                    open(fn, 'wb').write(data)
                    try:
                        from PIL import Image
                        im = Image.open(fn).convert('RGB'); im.save(fn, 'JPEG', quality=76, optimize=True, progressive=True)
                    except Exception: pass
                    break
            except Exception as e:
                err = e
    return fn if os.path.exists(fn) else None

def localize(c):
    """Google-foto's downloaden en lokaal in de site zetten (images/pN.jpg) — zoals Richard."""
    urls = []
    for k in IMG_KEYS:
        if ('googleusercontent' in (c.get(k) or '') or (c.get(k) or '').startswith('/')) and c[k] not in urls: urls.append(c[k])
    for u in c.get('gallery') or []:
        if ('googleusercontent' in u or u.startswith('/')) and u not in urls: urls.append(u)
    if not urls: return c, {}
    jobs = {}
    with cf.ThreadPoolExecutor(8) as ex:
        for i, u in enumerate(urls):
            jobs[u] = (i, ex.submit(fetch, u, 1400), ex.submit(fetch, u, 700))
    m, files = {}, {}
    for u, (i, big, small) in jobs.items():
        b, sm = big.result(), small.result()
        if b and sm:
            m[u] = f'images/p{i}.jpg'; files[f'images/p{i}.jpg'] = b; files[f'images/p{i}-s.jpg'] = sm
    c = dict(c)
    for k in IMG_KEYS:
        if c.get(k) in m: c[k] = m[c[k]]
        elif 'googleusercontent' in (c.get(k) or ''): c.pop(k) if k != 'photo' else None
    if c.get('gallery'): c['gallery'] = [m[u] for u in c['gallery'] if u in m]
    return c, files

def finish(out, files):
    os.makedirs(os.path.join(out, 'images'), exist_ok=True)
    for rel, src in files.items(): shutil.copy(src, os.path.join(out, rel))
    for r, _, fs in os.walk(out):
        for f in fs:
            if not f.endswith('.html'): continue
            p = os.path.join(r, f); depth = os.path.relpath(r, out).count('/') + (0 if r == out else 1)
            t = open(p).read().replace('IMGROOT/', '../' * depth)
            open(p, 'w').write(t)

def main(only):
    cfgs = normalize.all_configs()
    for slug, c in cfgs.items():
        if only and slug not in only: continue
        dp = os.path.join(ROOT, 'v2data', slug + '.json')
        d = json.load(open(dp)) if os.path.exists(dp) else {}
        if d.get('status') == 'closed':
            print(slug, 'GESLOTEN - overgeslagen'); continue
        c = overlay(c, d)
        out = os.path.join(HERE, 'out', slug)
        shutil.rmtree(out, ignore_errors=True)
        c, files = localize(c)
        gen_v2.build(c, out)
        finish(out, files)
        json.dump(pack(out), open(os.path.join(ROOT, 'v2b', slug + '.json'), 'w'), ensure_ascii=False)
        print(slug, 'ok', 'reviews', len(c.get('reviews') or []), 'fotos', len(c.get('gallery') or []), 'score', c.get('g_rating'))

if __name__ == '__main__':
    main(sys.argv[1:])
