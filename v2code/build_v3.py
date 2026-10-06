"""v3 build: normalize.py configs + echte Google Maps-gegevens uit v2data/<slug>.json.
Gebruik: python3 build_v3.py [slug ...]   -> bouwt naar out/<slug>/ en schrijft v2b/<slug>.json (deploy-payload).
Alleen feiten uit v2data; niets wordt verzonnen. Ontbreekt iets, dan blijft die sectie weg."""
import sys, os, json, re, shutil
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import normalize, gen_v2

MIN_COUNT = 3  # Google-score pas tonen vanaf 3 reviews

def overlay(c, d):
    if d.get('status') != 'ok': return c
    c = dict(c)
    c['maps'] = d['maps_url']
    if d.get('rating') and d.get('rating_count', 0) >= MIN_COUNT:
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
