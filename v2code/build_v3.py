"""v3 build: normalize.py configs + echte Google Maps-gegevens uit v2data/<slug>.json.
Gebruik: python3 build_v3.py [slug ...]   -> bouwt naar out/<slug>/ en schrijft v2b/<slug>.json (deploy-payload).
Alleen feiten uit v2data; niets wordt verzonnen. Ontbreekt iets, dan blijft die sectie weg."""
import sys, os, json, re, shutil
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import normalize, gen_v2

MIN_COUNT = 3  # Google-score pas tonen vanaf 3 reviews
MIN_RATING = 4.5  # lagere scores laten we weg (niet verzonnen, alleen niet getoond)
CLAIM = re.compile(r'review|beoordeel|sterren|Trustoo|Treatwell|Telefoonboek|Stukadoorgids|Pedicure\.nl|Salonkee|Google|waarder|best bezochte|\b[1-9],\d\b|\b\d+ keer\b', re.I)
SKIP = {'reviews','photo','gallery','maps','book','phone','hours','addr','tok','dark','fonts','alt','slug','cat','tags','trust','usps','proof','about_photo','socials','name','title','logo'}
H1 = {
 'barbershop-yazan':'Strak geknipt <em>bij Yazan.</em>', 'mido-barbershop':'Precisie, rust <em>en een strakke coupe.</em>',
 'house-of-nofa':'Mooie nagels, <em>zeven dagen per week.</em>', 'barbershop-t-pleintje':'Strak geknipt <em>in Renkum.</em>',
 'barbershop-veenendaal':'Strak geknipt <em>in Veenendaal.</em>', 'elegant-barbershop':'Elegant geknipt <em>in Den Bosch.</em>',
 'barber-sam-gouda':'Strak geknipt <em>bij Sam.</em>', 'unique-nails-hengelo':'Uniek, <em>tot in elk detail.</em>',
 'antonina-beauty-nails':'Nagels en pedicure, <em>met aandacht.</em>', 'nails-beauty-aridj':'Nagels, brows en lashes, <em>één adres.</em>',
 'vikkis-beauty-world':'Lashes, brows <em>en nails.</em>', 'ruiter-tuin-timmer':'Tuinwerk en houtwerk, <em>in één hand.</em>',
 'lashmazing-enschede':'Wimpers, <em>helemaal lashmazing.</em>',
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

def overlay(c, d):
    c = sanitize(c, d)
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
    if d.get('reviews'): c['reviews'] = d['reviews']
    if d.get('hero'):
        c['photo'] = d['hero']; c['alt'] = d.get('hero_alt') or f"{c['name']} in {c.get('place') or ''}".strip()
        c['pos'] = 'center'
    if d.get('gallery'): c['gallery'] = d['gallery']
    if d.get('about_photo'):
        c['about_photo'] = d['about_photo']; c['about_alt'] = f"{c['name']}"
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
            files.append({'file': os.path.relpath(p, outdir), 'data': open(p).read()})
    return files

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
        gen_v2.build(c, out)
        json.dump(pack(out), open(os.path.join(ROOT, 'v2b', slug + '.json'), 'w'), ensure_ascii=False)
        print(slug, 'ok', 'reviews', len(c.get('reviews') or []), 'fotos', len(c.get('gallery') or []), 'score', c.get('g_rating'))

if __name__ == '__main__':
    main(sys.argv[1:])
