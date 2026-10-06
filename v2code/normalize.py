"""Turn old single-page configs (SITES) + legacy booking sites into gen_v2 configs."""
import sys, re, json, urllib.parse as up
sys.path.insert(0, '/home/claude/beauty')
import sites_bouw as S

def strip(s): return re.sub('<[^>]+>', '', s or '').strip()

# ---------- category detection ----------
BEAUTY_W = ['pedicure','nagel','nail','wimper','lash','beauty','schoonheid','huid','skin','spa','esthique','glow','brow']
KAP_W = ['barb','kapsalon','kapper','hair','haar','hip-man','walid-style','styling']
TUIN_W = ['hovenier','tuin','garden','groen']
DIER_W = ['trim','hond','paw','dog']
MODE_W = ['fashion','vintage','streetwear','nofa','loaded']

import glob as _g
SEED={}
for _f in _g.glob('/home/claude/seed/**/*.json', recursive=True):
    _d=json.load(open(_f))
    for _x in (_d if isinstance(_d,list) else [_d]):
        if isinstance(_x,dict) and _x.get('site') and _x.get('cat'): SEED[_x['site'].rstrip('/').split('/')[-1]]=_x['cat']
def category(slug, c):
    if slug in SEED: return SEED[slug]
    t = (slug + ' ' + c.get('title','')).lower()
    if any(w in t for w in DIER_W): return 'dieren'
    if any(w in slug for w in KAP_W) or 'barbier' in t: return 'kapper'
    if any(w in t for w in BEAUTY_W): return 'beauty'
    if any(w in t for w in TUIN_W): return 'hovenier'
    if any(w in slug for w in MODE_W): return 'mode'
    if 'rijschool' in slug: return 'rijschool'
    if 'bloem' in slug: return 'bloemist'
    if 'onroerend' in slug: return 'vastgoed'
    if 'bakfriet' in slug or 'heleentje' in slug: return 'catering'
    return 'bouw'

BANDS = {
 'bouw': ['Afspraak is afspraak. En we laten het netjes achter.', 'Eén vakman, één aanspreekpunt, van begin tot eind.', 'Goed werk zie je terug, jaren later nog.'],
 'hovenier': ['Een mooie tuin groeit met de jaren. Wij zorgen dat hij goed begint.', 'Buiten is je tweede woonkamer. Zo behandelen we hem ook.'],
 'beauty': ['Even een uur alleen voor jou.', 'Rust, aandacht en vakwerk. Meer heb je niet nodig.', 'Je loopt lichter naar buiten dan je binnenkwam.'],
 'kapper': ['Strak geknipt is geen geluk. Het is vakwerk.', 'Even zitten, bijpraten en weer scherp naar buiten.'],
 'dieren': ['Een rustige hond is een blije hond. Daar nemen we de tijd voor.'],
 'mode': ['Kleding met een verhaal, uitgekozen met aandacht.'],
}
FAQ = {
 'bouw': [('Is een offerte vrijblijvend?', 'Ja. We komen kijken, denken mee en je krijgt een duidelijke prijs vooraf. Pas als je akkoord bent, plannen we het werk in.'),
          ('Hoe snel krijg ik een reactie?', 'Stuur een bericht via WhatsApp of bel. Je krijgt zo snel mogelijk antwoord, meestal nog dezelfde dag.'),
          ('Werken jullie ook voor bedrijven?', 'Ja, voor particulieren én zakelijke klanten. Vraag gerust naar de mogelijkheden.'),
          ('Kan ik foto’s sturen voor een eerste inschatting?', 'Graag zelfs. Stuur via WhatsApp een paar foto’s mee, dan weten we meteen waar het om gaat.')],
 'hovenier': [('Komen jullie eerst kijken?', 'Ja. We bekijken de tuin samen en bespreken je wensen. Daarna krijg je een duidelijk voorstel.'),
          ('Doen jullie ook onderhoud?', 'Ja, eenmalig of periodiek. Zo blijft je tuin het hele jaar netjes.'),
          ('Kan ik foto’s van mijn tuin sturen?', 'Graag. Stuur ze via WhatsApp, dan kunnen we alvast meedenken.')],
 'beauty': [('Moet ik een afspraak maken?', 'Ja, er wordt op afspraak gewerkt. Zo heb je alle rust en aandacht tijdens je behandeling.'),
          ('Ik weet niet welke behandeling bij me past.', 'Geen probleem. Stuur een berichtje of vraag het bij je afspraak, je krijgt eerlijk advies.'),
          ('Kan ik een afspraak verzetten?', 'Natuurlijk. Laat het zo vroeg mogelijk weten via WhatsApp of telefoon.')],
 'kapper': [('Moet ik een afspraak maken?', 'Bel of stuur een WhatsApp, dan hoor je meteen wanneer je terecht kunt.'),
          ('Knippen jullie ook kinderen?', 'Vraag het gerust, de meeste behandelingen zijn voor iedereen.'),
          ('Kan ik een foto laten zien van wat ik wil?', 'Graag. Neem een foto mee of stuur hem vooraf via WhatsApp.')],
 'dieren': [('Hoe lang duurt een trimbeurt?', 'Dat hangt af van ras, vacht en grootte. Bij het maken van de afspraak hoor je hoe lang je hond ongeveer blijft.'),
          ('Mijn hond is wat angstig. Kan dat?', 'Zeker. Er wordt rustig en met geduld gewerkt, zodat je hond zich op zijn gemak voelt.')],
}
FAQ['mode'] = [('Kan ik ook langskomen om te passen?', 'Ja, kom gerust langs of stuur eerst een bericht.'), ('Kan ik iets laten reserveren?', 'Stuur een WhatsApp met wat je zoekt, dan kijken we wat mogelijk is.')]
for k in ['catering','rijschool','bloemist','vastgoed']: FAQ[k] = FAQ['bouw'][1:2]

def trust_items(c, cat):
    out = []
    for sp in re.findall(r'<span>(.*?)</span>', c.get('proof','')):
        m = re.match(r'\s*<b>(.*?)</b>\s*(.*)', sp)
        if m: out.append((m.group(1), strip(m.group(2)) or '&nbsp;'))
    fill = [('Direct contact', 'bel of WhatsApp'), ('Vrijblijvend', 'advies en offerte' if cat in ('bouw','hovenier') else 'een vraag stellen'), (c.get('place') or 'Lokaal', 'en omgeving')]
    for f in fill:
        if len(out) >= 4: break
        if not any(strip(f[0]) == strip(o[0]) for o in out): out.append(f)
    return out[:4]

def maps_link(name, addr, place):
    q = name + ' ' + (' '.join(addr) if addr else (place or ''))
    return 'https://www.google.com/maps/search/?api=1&query=' + up.quote(q.strip())

def short_of(c):
    ol = strip(c.get('over_label',''))
    if ol.startswith('Over ') and ol != 'Over ons':
        return ol[5:]
    return c['name']

def from_sites(slug, c, i):
    cat = category(slug, c)
    services = [{'name': n, 'd': d} for n, d in c['services']]
    svc_label = 'Behandelingen' if cat in ('beauty','kapper') else 'Diensten'
    out = dict(c)
    for k in ('sig_css','sig_html','h3_w','f_place','f_desc','contact_h'): out.pop(k, None)
    bands = BANDS.get(cat, BANDS['bouw'])
    out.update(
        slug=slug, cat=cat, short=short_of(c), services=services,
        trust=trust_items(c, cat), svc_label=svc_label,
        svc_more=f'Alle {svc_label.lower()} bekijken',
        band=bands[i % len(bands)],
        area_h=c.get('contact_h') or f"{c.get('place','')} en omgeving",
        f_kind=c.get('f_kind', 'Waar gaat het om?'),
        f_small=c.get('f_small', 'Stuur gerust een foto mee in WhatsApp.'),
        maps=maps_link(c['name'], c.get('addr'), c.get('place')),
        tags=[c.get('place') or '', services[0]['name']] if c.get('place') else [services[0]['name']],
        faq=FAQ.get(cat, FAQ['bouw']), nsteps=len(c['steps']),
        area=c.get('area') or [],
    )
    return out

# ---------- legacy booking sites ----------
def hx(h):
    h = h.lstrip('#')
    if len(h) == 3: h = ''.join(ch*2 for ch in h)
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
def toh(t): return '#%02x%02x%02x' % tuple(max(0, min(255, round(v))) for v in t)
def mix(a, b, t): A, B = hx(a), hx(b); return toh(tuple(A[i]*(1-t)+B[i]*t for i in range(3)))
def lum(h): r, g, b = hx(h); return (0.2126*r + 0.7152*g + 0.0722*b)/255
def sat(h): r, g, b = hx(h); return (max(r,g,b)-min(r,g,b))/255

def legacy_palette(root):
    v = dict(re.findall(r'--([a-z0-9-]+):\s*([^;]+);', root))
    v = {k: x.strip() for k, x in v.items()}
    def res(x):
        while x and x.startswith('var('): x = v.get(x[6:-1], '#333')
        return x
    acc = res(v.get('accent', '#333'))
    # prefer a coloured brand var when accent is the text colour
    named = [res(x) for k, x in v.items() if k not in ('bg','surface','fg','muted','line','accent','on-accent','err','ink') and x.startswith('#') and len(x) in (4,7)]
    if sat(acc) < .12 and named:
        best = max(named, key=sat)
        if sat(best) > .15: acc = best
    dark_root = lum(res(v.get('bg', '#fff'))) < .3
    if dark_root:
        ink = res(v['bg']); bg = '#f6f3ee'; surface = '#fffdf9'; fg = mix(ink, '#000', .1); muted = '#625d56'; line = '#e4ded4'
        accent = acc if lum(acc) < .45 else mix(ink, '#fff', .08)
        hero = acc if lum(acc) > .5 else mix(acc, '#fff', .55)
    else:
        bg, surface, fg, muted, line = (res(v[k]) for k in ('bg','surface','fg','muted','line'))
        ink = mix(fg, '#000', .15) if lum(fg) < .2 else '#1a1a1a'
        accent = acc if lum(acc) < .5 else mix(acc, '#000', .45)
        hero = mix(accent, '#fff', .62)
    on = '#fff' if lum(accent) < .55 else '#141414'
    acct = accent if lum(accent) < .35 else mix(accent, '#000', .3)
    alt = mix(bg, fg, .04)
    tok = f'--bg:{bg};--surface:{surface};--fg:{fg};--muted:{muted};--line:{line};--accent:{accent};--on-accent:{on};--accent-text:{acct};--alt:{alt};--ink:{ink};--hero-accent:{hero};--err:#b3261e;--r:999px;--r2:18px;--bk-r:14px'
    dacc = mix(accent, '#fff', .45) if lum(accent) < .5 else accent
    dark = f'--bg:{mix(ink,"#000",.35)};--surface:{mix(ink,"#000",.15)};--fg:#f1eee9;--muted:#aba59d;--line:{mix(ink,"#fff",.1)};--accent:{dacc};--on-accent:#141414;--accent-text:{mix(dacc,"#fff",.25)};--alt:{mix(ink,"#000",.25)};--ink:{mix(ink,"#000",.5)};--err:#ffb4ab'
    m = re.search(r'--display:\s*([^;]+);', root); disp = m.group(1).strip() if m else 'Georgia,serif'
    m = re.search(r'--body:\s*([^;]+);', root); body = m.group(1).strip() if m else 'system-ui,sans-serif'
    return tok, dark, disp, body

PH = {
 'pedi': ('photo-1787651344170-c2f81514934d', 'Behandelstoel met voetenbad in een rustige pedicuresalon'),
 'pedi2': ('photo-1577117633143-a2437fb9bdda', 'Voeten in een kom met water tijdens een voetbad'),
 'pedi3': ('photo-1564935192630-328856ef4f52', 'Verzorgde voeten'),
 'nails': ('photo-1604654894610-df63bc536371', 'Hand met verzorgde nagels en een gouden ring'),
 'nails2': ('photo-1610992015762-45dca7fa3a85', 'Hand met lichtroze gemanicuurde nagels'),
 'nails3': ('photo-1519014816548-bf5fe059798b', 'Close-up van een roze manicure'),
 'nails4': ('photo-1607779097040-26e80aa78e66', 'Hand met mauve, witte en glitter nagels'),
 'lash': ('photo-1589710751893-f9a6770ad71b', 'Specialiste zet wimperextensions bij een klant'),
 'face': ('photo-1643684391140-c5056cfd3436', 'Vrouw krijgt een ontspannende gezichtsbehandeling'),
 'face2': ('photo-1616394584738-fc6e612e71b9', 'Vrouw ontspant met een verzorgend masker'),
 'skin': ('photo-1555820585-c5ae44394b79', 'Vrouw met gesloten ogen en een stralende huid'),
 'spa': ('photo-1544717304-a2db4a7b16ee', 'Vrouw in witte handdoek ontspant in een wellness-omgeving'),
 'massage': ('photo-1559185590-879c66a55254', 'Schoonheidsspecialiste geeft een ontspannende massage'),
 'hair': ('photo-1560066984-138dadb4c035', 'Lichte, moderne kapsalon met stoelen en spiegels'),
 'hair2': ('photo-1562322140-8baeececf3df', 'Kapster kleurt het haar van een klant'),
 'hair3': ('photo-1522337360788-8b13dee7a37e', 'Kapster föhnt en stylet het haar van een klant'),
}
# slug: (photo key, kick, h1 with <em>, short name, svc_h)
LEG = {
 'ashleys-haar-nagels': ('hair', 'Haarmode & nagelstudio', 'Haar en nagels, <em>in één afspraak.</em>', 'Ashley', 'Haar en nagels'),
 'beauty-by-aniek': ('lash', 'Nagels & wimpers', 'Nagels en wimpers, <em>tot in detail.</em>', 'Aniek', 'Nagels en wimpers'),
 'ellens-puur-voet': ('pedi2', 'Pedicure', 'Even je voeten <em>in goede handen.</em>', 'Ellen', 'Voetverzorging'),
 'head-spa-doetinchem': ('spa', 'Head spa', 'Een uur lang <em>niets hoeven.</em>', 'Head Spa Doetinchem', 'Head spa behandelingen'),
 'marlou-beauty-salon': ('lash', 'Lashes, brows & spraytan', 'Lashes, brows en <em>een zomerse glow.</em>', 'Marlou', 'Behandelingen'),
 'medisch-pedicure-verhoeven': ('pedi', 'Medisch pedicure', 'Zorg voor uw voeten, <em>met medische kennis.</em>', 'Medisch Pedicure Verhoeven', 'Voetzorg'),
 'melody-beauty': ('hair2', 'Dameskapsalon · kleurspecialist', 'Kleur <em>die leeft.</em>', 'Melody Beauty', 'Knippen en kleuren'),
 'merie-spijker': ('face', 'Huid- en voetverzorging', 'Huid en voeten, <em>dertig jaar vakwerk.</em>', 'Mérie', 'Gezicht en voeten'),
 'mooi-bij-rianne': ('hair3', 'Kapsalon', 'Mooi haar, <em>eerlijke prijs.</em>', 'Rianne', 'Knippen en kleuren'),
 'moon-en-more': ('pedi3', 'Pedicuresalon', 'Voeten die weer <em>lichter voelen.</em>', 'Moon & More', 'Voetverzorging'),
 'nails-by-jose': ('nails4', 'Nagelstyliste', 'Strakke nagels, <em>gezet met aandacht.</em>', 'José', 'Nagels'),
 'namaste-beauty': ('nails2', 'Hand- & nagelverzorging', 'Rust in je hoofd, <em>mooi aan je handen.</em>', 'Namasté Beauty', 'Handen, nagels en voeten'),
 'natasja-hair-nails': ('hair', 'Hair & nailstyling', 'Haar en nagels <em>in één afspraak.</em>', 'Natasja', 'Haar en nagels'),
 'nathies-nails': ('nails', 'Nagelstudio sinds 2009', 'Mooie handen, <em>sterke nagels.</em>', 'Nathalie', 'Nagels'),
 'noor-pedicure-manicure': ('pedi2', 'Pedicure & manicure', 'Verzorgde handen en voeten, <em>met aandacht.</em>', 'Noor', 'Handen en voeten'),
 'pedicure-framoni': ('pedi3', 'Pedicure & ontharen', 'Gezonde voeten, <em>gladde huid.</em>', 'Framoni', 'Behandelingen'),
 'pedicuresalon-jeannette': ('pedi', 'Pedicure & medische voetzorg', 'Weer pijnvrij <em>en met plezier lopen.</em>', 'Jeannette', 'Voetzorg'),
 'reus-beauty': ('face2', 'Schoonheid, pedicure & kapper', 'Rust en aandacht, <em>in de salon of thuis.</em>', 'Liesbeth', 'Behandelingen'),
 'richelle-pedicure': ('pedi', 'Pedicure & schoonheidssalon', 'Voetzorg en verzorging <em>onder één dak.</em>', 'Richelle', 'Behandelingen'),
 'salon-binnenstebuiten': ('massage', 'Schoonheidssalon', 'Even <em>tot rust komen.</em>', 'Salon Binnenstebuiten', 'Behandelingen'),
 'skindy': ('skin', 'Medical beauty', 'Huidverzorging <em>met kennis van zaken.</em>', 'Skindy', 'Behandelingen'),
 'styling-84': ('hair3', 'Haar & make-up', 'Haar en make-up <em>met stijl.</em>', 'Styling 84', 'Haar en make-up'),
 'wendys-beauty-nails': ('face', 'Beauty & nails', 'Even helemaal <em>voor jezelf.</em>', 'Wendy', 'Behandelingen'),
 'wimpers-by-laurie': ('lash', 'Wimperextensions', 'Wakker worden <em>met mooie wimpers.</em>', 'Laurie', 'Wimpers'),
 'y-style': ('nails3', 'Nails & beauty', 'Nails & beauty <em>die opvallen.</em>', 'Y-Style', 'Nagels en wimpers'),
 'yomy-pedicure': ('pedi2', 'Pedicure', 'Even helemaal <em>op adem komen.</em>', 'Yomy', 'Voetverzorging'),
}

def clean(p): return re.sub(r'\s+', ' ', p).strip()

def from_legacy(slug, e, bk, i):
    photo, kick, h1, short, svc_h = LEG[slug]
    tok, dark, disp, body = legacy_palette(e['root'])
    addr = None; place = ''
    if e.get('addr'):
        parts = [x.strip() for x in e['addr'].split('\n') if x.strip()]
        if len(parts) == 2:
            place = re.sub(r'^\d{4}\s?[A-Z]{2}\s+', '', parts[1])
            addr = (parts[0], parts[1]) if parts[0] != e['title'] and re.search(r'\d', parts[0] + parts[1]) else None
            if parts[0] == e['title'] or not re.search(r'\d', parts[0]): addr = None
        else: place = parts[-1]
    tel = e['tel']
    phone = ('0' + tel[2:3] + ' ' + tel[3:]) if tel else ''
    paras = [clean(p) for p in e['paras'] if len(clean(p)) > 40 and len(clean(p)) < 400 and 'Kies een behandeling en een moment' not in p]
    lead = paras[0] if paras else ''
    about = ''.join(f'<p>{p}</p>' for p in paras[1:4]) or f'<p>{lead}</p>'
    svcs = []
    for s in bk['services']:
        svcs.append({'name': s['name'], 'd': s.get('d', ''), 'min': s.get('min'), 'price': s.get('price')})
    n_svc = len(svcs)
    cat = 'kapper' if photo.startswith('hair') else 'beauty'
    bcfg = dict(bk); bcfg['phone'] = phone
    page_js = '<script>window.BOOK=' + json.dumps(bcfg, ensure_ascii=False) + ';</script><script>' + open('/home/claude/beauty/bk.js').read() + '</script>'
    trust = [(f'{n_svc}', 'behandelingen'), ('Online', 'afspraak plannen'), ('Direct', 'contact via WhatsApp'), (place or 'Lokaal', 'en omgeving')]
    nm = e['title']
    return dict(
        slug=slug, cat=cat, legacy=True, name=nm, short=short, place=place, phone=phone, addr=addr,
        title=f'{nm} | {svc_h} in {place}' if place else nm,
        logo=nm.replace('Pedicuresalon ', '') if len(nm) > 26 else nm, logo_sub=f'{kick} · {place}' if place else kick,
        fonts=e['fonts'], display=disp, body=body, tok=tok, dark=dark,
        photo=PH[photo][0], alt=PH[photo][1], pos='center',
        kick=kick, h1=h1, lead=lead, cta='Plan je afspraak', proof='',
        trust=trust, services=svcs, over_label=f'Over {short}' if short != nm else 'Over ons',
        quote=clean(re.sub('<[^>]+>', '', h1)), band=BANDS['beauty'][i % 3], about=about,
        usps=[(str(n_svc), 'behandelingen'), ('Online', 'afspraak plannen'), ('1', 'vast aanspreekpunt'), ('Lokaal', f'in {place}' if place else 'in de buurt')],
        svc_label='Behandelingen', svc_h=svc_h, svc_p='Kies wat bij je past. Je ziet direct de duur van elke behandeling.',
        svc_more='Alle behandelingen bekijken',
        steps=[('Kies je behandeling', 'Bekijk wat er mogelijk is en kies wat bij je past.'), ('Plan een moment', 'Kies online een vrije tijd, of stuur een berichtje.'), ('Even voor jezelf', 'Je wordt rustig en met aandacht geholpen.')],
        steps_h='Zo eenvoudig plan je het', nsteps=3,
        form_eyebrow='Contact', form_h='Liever eerst even vragen?', form_p='Stuur een berichtje via WhatsApp. Je krijgt zo snel mogelijk antwoord.',
        f_kind='Behandeling', f_ph='Bijvoorbeeld: wanneer kan ik terecht, of welke behandeling past bij mij?',
        f_small='Je bericht opent in WhatsApp.', wa_intro='Ik heb een vraag over',
        area=[], area_h=f'Te vinden in {place}' if place else 'Op afspraak', area_note='', area_label='Locatie',
        maps=maps_link(nm, addr, place), tags=[place, svcs[0]['name']] if place else [svcs[0]['name']],
        faq=FAQ['beauty'], hours=None,
        book=True, bk_css=open('/home/claude/beauty/bk.css').read(), page_js=page_js,
        price_note='Duur is een indicatie. Vraag gerust naar de actuele prijzen.',
    )

def all_configs():
    out = {}
    for i, (slug, c) in enumerate(S.SITES.items()):
        out[slug] = from_sites(slug, c, i)
    raw = json.load(open('/home/claude/v2/legacy_raw.json'))
    book = json.load(open('/home/claude/v2/legacy_book.json'))
    for i, (slug, e) in enumerate(raw.items()):
        out[slug] = from_legacy(slug, e, book[slug], i)
    return out

if __name__ == '__main__':
    import gen_v2, os, shutil
    cfgs = all_configs()
    only = sys.argv[1:]
    base = '/home/claude/v2/out'
    for slug, c in cfgs.items():
        if only and slug not in only: continue
        d = os.path.join(base, slug)
        shutil.rmtree(d, ignore_errors=True)
        gen_v2.build(c, d)
    json.dump({k: {'cat': v['cat'], 'name': v['name'], 'place': v.get('place'), 'phone': v['phone']} for k, v in cfgs.items()}, open('/home/claude/v2/index.json', 'w'), ensure_ascii=False, indent=0)
    print('built', len(only) or len(cfgs))
