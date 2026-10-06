"""AgentBay v2 site generator — multi-page, Richard-style.
Input: normalized config dict per site (see normalize.py). Output: folder with index.html + subpages."""
import os, re, html as H, json

U='https://images.unsplash.com/'
def img(src, w):
    if src.startswith('http'): return src
    return f'{U}{src}?auto=format&fit=crop&w={w}&q=72'

PH='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M5 4h4l2 5-2.5 1.5a11 11 0 0 0 5 5L15 13l5 2v4a2 2 0 0 1-2 2A16 16 0 0 1 3 6a2 2 0 0 1 2-2"/></svg>'
WA='<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M12 2a10 10 0 0 0-8.6 15.1L2 22l5-1.3A10 10 0 1 0 12 2Zm0 18.2a8.2 8.2 0 0 1-4.2-1.1l-.3-.2-3 .8.8-2.9-.2-.3A8.2 8.2 0 1 1 12 20.2Zm4.5-6.1c-.2-.1-1.5-.7-1.7-.8s-.4-.1-.6.1-.7.8-.8 1-.3.2-.5.1a6.7 6.7 0 0 1-3.3-2.9c-.3-.4.2-.4.7-1.4a.5.5 0 0 0 0-.4l-.8-1.8c-.2-.5-.4-.4-.6-.4h-.5a1 1 0 0 0-.7.3 3 3 0 0 0-.9 2.2 5.2 5.2 0 0 0 1.1 2.7 11.8 11.8 0 0 0 4.5 4c1.7.7 2.3.8 3.2.7a2.7 2.7 0 0 0 1.8-1.3 2.2 2.2 0 0 0 .2-1.3c-.1-.1-.3-.2-.5-.3Z"/></svg>'
STAR='<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="m12 2 3 6.6 7.2.7-5.4 4.8 1.6 7.1L12 17.6 5.6 21.2l1.6-7.1L1.8 9.3 9 8.6z"/></svg>'
ARROW='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6"/></svg>'
PIN='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M12 21s7-6.2 7-12a7 7 0 1 0-14 0c0 5.8 7 12 7 12Z"/><circle cx="12" cy="9" r="2.5"/></svg>'
GRAIN="url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='160' height='160'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.9' numOctaves='2' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='.08'/%3E%3C/svg%3E\")"

def esc(s): return H.escape(s, quote=True)
def strip(s): return re.sub('<[^>]+>','',s or '')

def css(c):
    return f'''
:root{{{c["tok"]};--display:{c["display"]};--body:{c["body"]};color-scheme:light}}
@media (prefers-color-scheme:dark){{:root:not([data-theme="light"]){{{c["dark"]};color-scheme:dark}}}}
*,*::before,*::after{{box-sizing:border-box}}
html{{scroll-behavior:smooth;scroll-padding-top:90px;-webkit-text-size-adjust:100%}}
body{{margin:0;background:var(--bg);color:var(--fg);font:400 17px/1.65 var(--body);-webkit-font-smoothing:antialiased}}
img{{max-width:100%;display:block}}
a{{color:inherit}} :focus-visible{{outline:2px solid var(--accent);outline-offset:3px}}
h1,h2,h3{{font-family:var(--display);margin:0;text-wrap:balance;letter-spacing:{c.get("ls","-.015em")};font-weight:{c.get("h_w","600")}}}
p{{margin:0}}
.wrap{{max-width:1200px;margin:0 auto;padding-inline:20px}}
.eyebrow{{display:inline-flex;align-items:center;gap:10px;font:600 13px var(--body);letter-spacing:.16em;text-transform:uppercase;color:var(--accent-text)}}
.eyebrow::before{{content:"";width:22px;height:2px;background:currentColor}}
.dark .eyebrow{{color:var(--hero-accent)}}
.btn{{display:inline-flex;align-items:center;justify-content:center;gap:10px;min-height:52px;padding:0 24px;border-radius:var(--r);font:600 16px var(--body);text-decoration:none;border:1.5px solid transparent;cursor:pointer;white-space:nowrap;transition:transform .15s,background .2s}}
.btn:hover{{transform:translateY(-1px)}} .btn svg{{width:19px;height:19px;flex:none}}
.btn.pri{{background:var(--accent);color:var(--on-accent)}}
.btn.light{{border-color:rgba(255,255,255,.45);color:#fff}}
.btn.line{{border-color:var(--fg);color:var(--fg)}}
.btn.wa{{background:#1f8f4e;color:#fff}}
.grain{{position:relative;isolation:isolate}}
.grain::before{{content:"";position:absolute;inset:0;background-image:{GRAIN};pointer-events:none;z-index:-1;mix-blend-mode:overlay}}
.dark{{background:var(--ink);color:#f3f1ec}}
.dark .muted{{color:rgba(255,255,255,.72)}}
.muted{{color:var(--muted)}}
section.s{{padding-block:clamp(72px,9vw,112px)}}
.sh{{display:grid;gap:14px;max-width:720px;margin-bottom:44px}}
.sh h2{{font-size:clamp(32px,4.6vw,52px);line-height:1.06}}
.sh p{{font-size:18px}}
/* header */
.top{{position:fixed;inset:0 0 auto;z-index:50;background:color-mix(in srgb,var(--bg) 92%,transparent);backdrop-filter:blur(14px);-webkit-backdrop-filter:blur(14px);border-bottom:1px solid var(--line)}}
.top .wrap{{display:flex;align-items:center;justify-content:space-between;gap:16px;height:76px}}
.logo{{text-decoration:none;display:grid;line-height:1.08}}
.logo b{{font:{c.get("logo_w","700")} 21px var(--display);letter-spacing:{c.get("ls","-.015em")}}}
.logo small{{font-size:11.5px;letter-spacing:.12em;text-transform:uppercase;color:var(--muted)}}
.nav{{display:flex;align-items:center;gap:30px;font-size:15px;font-weight:500}}
.nav a:not(.btn){{text-decoration:none;color:var(--muted);padding:6px 0;border-bottom:2px solid transparent}}
.nav a[aria-current]{{color:var(--fg);border-color:var(--accent)}}
.nav .btn{{min-height:44px;padding:0 18px;font-size:15px}}
.burger{{display:none;background:none;border:0;padding:8px;color:var(--fg);cursor:pointer}}
.burger svg{{width:26px;height:26px}}
@media (max-width:900px){{.nav a:not(.btn){{display:none}}.burger{{display:block}}.nav .btn .t{{display:none}}.nav .btn{{padding:0 14px}}}}
.drawer{{position:fixed;inset:76px 0 auto;z-index:49;background:var(--bg);border-bottom:1px solid var(--line);padding:12px 20px 22px;display:none}}
.drawer.open{{display:grid;gap:4px}}
.drawer a{{text-decoration:none;font:600 20px var(--display);padding:12px 0;border-bottom:1px solid var(--line)}}
main{{padding-top:76px}}
/* hero */
.hero .wrap{{display:grid;gap:40px;padding-block:clamp(56px,8vw,104px)}}
@media (min-width:980px){{.hero .wrap{{grid-template-columns:1.05fr .95fr;align-items:center;gap:64px}}}}
.hero h1{{font-size:clamp(42px,6.2vw,78px);line-height:1.02;margin:18px 0 22px}}
.hero h1 em{{font-style:{c.get("em_style","italic")};color:var(--hero-accent)}}
.hero .lead{{font-size:clamp(17px,1.5vw,19.5px);max-width:52ch;color:rgba(255,255,255,.82)}}
.hero .cta{{display:flex;flex-wrap:wrap;gap:12px;margin-top:32px}}
.chip{{display:inline-flex;align-items:center;gap:12px;margin-top:30px;padding:10px 16px 10px 12px;border-radius:999px;background:rgba(255,255,255,.08);border:1px solid rgba(255,255,255,.14);text-decoration:none;font-size:15px}}
.chip b{{font:600 22px var(--display)}} .chip .stars{{display:flex;color:#f5b301}} .chip .stars svg{{width:15px;height:15px}}
.hero figure{{margin:0;position:relative}}
.hero figure img{{width:100%;aspect-ratio:4/4.6;object-fit:cover;object-position:{c.get("pos","center")};border-radius:calc(var(--r2) * 1.6)}}
@media (max-width:979px){{.hero figure img{{aspect-ratio:4/3}}}}
.hero figure figcaption{{position:absolute;left:16px;bottom:16px;right:16px;display:flex;justify-content:space-between;gap:10px;flex-wrap:wrap}}
.tag{{background:color-mix(in srgb,var(--ink) 78%,transparent);backdrop-filter:blur(8px);color:#fff;font-size:13.5px;padding:8px 13px;border-radius:999px}}
/* trust */
.trust{{background:var(--alt);border-bottom:1px solid var(--line)}}
.trust .wrap{{display:grid;grid-template-columns:repeat(2,1fr);gap:18px 24px;padding-block:24px}}
@media (min-width:860px){{.trust .wrap{{grid-template-columns:repeat(4,1fr)}}}}
.trust div{{display:grid;gap:2px;font-size:14.5px;color:var(--muted)}} .trust b{{color:var(--fg);font:600 18px var(--display)}}
/* about */
.about .wrap{{display:grid;gap:44px}}
@media (min-width:960px){{.about .wrap{{grid-template-columns:1fr 1fr;gap:80px;align-items:start}}}}
.about h2{{font-size:clamp(30px,4vw,46px);line-height:1.08;margin-top:14px}}
.about .txt{{display:grid;gap:16px;font-size:18px}}
.stats{{display:grid;grid-template-columns:repeat(2,1fr);gap:26px 22px;margin-top:30px;padding-top:28px;border-top:1px solid var(--line)}}
@media (min-width:600px){{.stats.s4{{grid-template-columns:repeat(4,1fr)}}}}
.stats b{{display:block;font:600 clamp(30px,3.6vw,40px)/1 var(--display);color:var(--accent-text)}}
.stats span{{font-size:14px;color:var(--muted)}}
.more{{display:inline-flex;align-items:center;gap:8px;font-weight:600;text-decoration:none;color:var(--accent-text);margin-top:26px}}
.more svg{{width:18px;height:18px}}
/* services */
.svcs{{display:grid;gap:14px}}
@media (min-width:720px){{.svcs{{grid-template-columns:repeat(2,1fr)}}}}
@media (min-width:1040px){{.svcs{{grid-template-columns:repeat(3,1fr)}}}}
.svc{{background:var(--surface);border:1px solid var(--line);border-radius:var(--r2);padding:30px 26px;display:grid;gap:10px;align-content:start;transition:border-color .2s,transform .2s}}
.svc:hover{{border-color:var(--accent);transform:translateY(-2px)}}
.svc .n{{font:600 14px var(--body);color:var(--accent-text);letter-spacing:.06em}}
.svc h3{{font-size:24px;line-height:1.15}}
.svc p{{color:var(--muted);font-size:16px}}
.svc .meta{{display:flex;gap:14px;font-size:14px;font-weight:600;color:var(--fg);margin-top:4px}}
/* band */
.band{{background:var(--accent);color:var(--on-accent)}}
.band .wrap{{padding-block:clamp(56px,7vw,88px);display:grid;gap:18px;max-width:980px;text-align:center;justify-items:center}}
.band blockquote{{margin:0;font:{c.get("q_w","500")} clamp(28px,3.8vw,44px)/1.18 var(--display);font-style:{c.get("em_style","italic")}}}
.band small{{font-size:13px;letter-spacing:.16em;text-transform:uppercase;opacity:.75}}
/* steps */
.steps{{list-style:none;margin:0;padding:0;display:grid;gap:14px;counter-reset:st}}
@media (min-width:860px){{.steps{{grid-template-columns:repeat({c.get("nsteps",3)},1fr)}}}}
.steps li{{counter-increment:st;border-top:1px solid rgba(255,255,255,.18);padding-top:22px;display:grid;gap:8px}}
.steps li::before{{content:counter(st,decimal-leading-zero);font:600 15px var(--body);color:var(--hero-accent);letter-spacing:.08em}}
.steps b{{font:600 22px var(--display);color:#fff}}
.steps span{{color:rgba(255,255,255,.75);font-size:16px}}
.light .steps li{{border-color:var(--line)}} .light .steps b{{color:var(--fg)}} .light .steps span{{color:var(--muted)}} .light .steps li::before{{color:var(--accent-text)}}
/* rating */
.rate .wrap{{display:grid;gap:30px;align-items:center}}
@media (min-width:900px){{.rate .wrap{{grid-template-columns:auto 1fr auto;gap:56px}}}}
.big{{font:600 clamp(72px,10vw,120px)/.9 var(--display);color:var(--accent-text)}}
.rate .stars{{display:flex;gap:3px;color:#f5b301;margin-bottom:8px}} .rate .stars svg{{width:22px;height:22px}}
.rate h2{{font-size:clamp(28px,3.4vw,40px);line-height:1.12}}
/* area */
.areas{{list-style:none;padding:0;margin:20px 0 0;display:flex;flex-wrap:wrap;gap:8px}}
.areas li{{border:1px solid var(--line);background:var(--surface);border-radius:999px;padding:8px 15px;font-size:15px}}
/* contact */
.contact .wrap{{display:grid;gap:44px}}
@media (min-width:980px){{.contact .wrap{{grid-template-columns:.9fr 1.1fr;gap:72px;align-items:start}}}}
.cards{{display:grid;gap:12px;margin-top:30px}}
.card{{display:flex;gap:16px;align-items:center;padding:18px 20px;border-radius:var(--r2);background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.12);text-decoration:none}}
.card svg{{width:22px;height:22px;flex:none;color:var(--hero-accent)}}
.card small{{display:block;font-size:12px;letter-spacing:.14em;text-transform:uppercase;opacity:.7}}
.card b{{font:600 19px var(--display)}}
form{{background:var(--surface);color:var(--fg);border-radius:calc(var(--r2) * 1.3);padding:clamp(22px,3vw,34px);display:grid;gap:16px;box-shadow:0 30px 60px -30px rgba(0,0,0,.45)}}
form h3{{font-size:24px}}
label{{display:grid;gap:7px;font-size:14px;font-weight:600}}
input,select,textarea{{font:16px var(--body);color:var(--fg);background:var(--bg);border:1px solid var(--line);border-radius:min(var(--r),12px);padding:14px;width:100%}}
textarea{{min-height:120px;resize:vertical}}
.two{{display:grid;gap:16px}} @media (min-width:560px){{.two{{grid-template-columns:1fr 1fr}}}}
form .btn{{width:100%}} .fine{{font-size:13px;color:var(--muted);text-align:center}}
.err{{color:#c0392b;font-size:14px;min-height:1em}}
/* page head */
.ph .wrap{{padding-block:clamp(56px,7vw,92px);display:grid;gap:16px;max-width:900px}}
.ph h1{{font-size:clamp(38px,5.4vw,64px);line-height:1.05}}
.ph p{{font-size:19px;max-width:60ch}}
.crumbs{{font-size:14px;color:rgba(255,255,255,.6)}} .crumbs a{{text-decoration:none}}
/* detail list */
.dl{{display:grid;gap:0;border-top:1px solid var(--line)}}
.dl article{{display:grid;gap:10px;padding:30px 0;border-bottom:1px solid var(--line)}}
@media (min-width:860px){{.dl article{{grid-template-columns:90px 1fr 1.3fr auto;gap:30px;align-items:baseline}}}}
.dl .n{{font:600 15px var(--body);color:var(--accent-text)}}
.dl h3{{font-size:26px;line-height:1.15}}
.dl p{{color:var(--muted)}}
.dl .pr{{font:600 18px var(--display);white-space:nowrap}}
/* gallery + reviews */
.gal{{display:grid;grid-template-columns:repeat(2,1fr);gap:10px}} @media (min-width:860px){{.gal{{grid-template-columns:repeat(3,1fr)}}}}
.gal img{{width:100%;aspect-ratio:1;object-fit:cover;border-radius:var(--r2)}}
.rvs{{display:grid;gap:14px}} @media (min-width:860px){{.rvs{{grid-template-columns:repeat(3,1fr)}}}}
.rv{{margin:0;background:var(--surface);border:1px solid var(--line);border-radius:var(--r2);padding:26px;display:grid;gap:14px;align-content:start}}
.rv .stars{{display:flex;color:#f5b301}} .rv .stars svg{{width:16px;height:16px}}
.rv blockquote{{margin:0;font-size:17px}} .rv figcaption{{font-size:14px;color:var(--muted)}} .rv b{{color:var(--fg)}}
/* faq */
details{{border-bottom:1px solid var(--line);padding:20px 0}}
summary{{cursor:pointer;font:600 20px var(--display);list-style:none;display:flex;justify-content:space-between;gap:20px}}
summary::-webkit-details-marker{{display:none}}
summary::after{{content:"+";color:var(--accent-text);font-size:26px;line-height:1}}
details[open] summary::after{{content:"–"}}
details p{{margin-top:12px;color:var(--muted);max-width:70ch}}
/* footer */
footer{{background:var(--ink);color:rgba(255,255,255,.72);padding:64px 0 110px;font-size:15px}}
@media (min-width:900px){{footer{{padding-bottom:48px}}}}
footer .wrap{{display:grid;gap:36px}}
@media (min-width:860px){{footer .wrap{{grid-template-columns:1.4fr 1fr 1fr}}}}
footer b{{display:block;color:#fff;font:600 22px var(--display);margin-bottom:10px}}
footer h4{{margin:0 0 12px;color:#fff;font:600 13px var(--body);letter-spacing:.14em;text-transform:uppercase}}
footer ul{{list-style:none;margin:0;padding:0;display:grid;gap:8px}} footer a{{text-decoration:none}} footer a:hover{{color:#fff}}
.legal{{border-top:1px solid rgba(255,255,255,.12);margin-top:44px;padding-top:22px;display:flex;justify-content:space-between;flex-wrap:wrap;gap:10px;font-size:13.5px}}
/* mobile bar */
.mbar{{position:fixed;left:12px;right:12px;bottom:calc(12px + env(safe-area-inset-bottom,0px));z-index:40;display:grid;grid-template-columns:1fr 1fr;gap:8px;padding:8px;border-radius:18px;background:color-mix(in srgb,var(--ink) 92%,transparent);backdrop-filter:blur(10px);box-shadow:0 12px 30px rgba(0,0,0,.3)}}
.mbar .btn{{min-height:48px;font-size:15px;padding:0 12px}}
@media (min-width:900px){{.mbar{{display:none}}}}
{c.get("extra_css","")}
'''

def rating_of(c):
    m=re.search(r'<b>([\d,]+)</b>\s*uit\s*([\d.]+)\s*(?:Google-)?reviews',c.get('proof',''))
    if m: return m.group(1), m.group(2)
    m=re.search(r'<b>([\d,]+)</b>\s*op Google',c.get('proof',''))
    if m: return m.group(1), None
    return c.get('rating'), c.get('rating_count')

def page(c, pg, title, body, prefix):
    intl='31'+c['phone'].replace(' ','')[1:] if c['phone'] else ''
    nav=[('', 'Home'),('diensten/','Diensten'),('over-ons/','Over ons')]+([('afspraak/','Afspraak')] if c.get('book') else [])+[('contact/','Contact')]
    links=''.join(f'<a href="{prefix}{h or "./"}"{" aria-current=\"page\"" if h==pg else ""}>{t}</a>' for h,t in nav)
    drawer=''.join(f'<a href="{prefix}{h or "./"}">{t}</a>' for h,t in nav)
    callbtn=f'<a class="btn pri" href="tel:+{intl}">{PH}<span class="t">{c["phone"]}</span></a>' if intl else f'<a class="btn pri" href="{prefix}contact/">Contact</a>'
    rt,rc=rating_of(c)
    foot_contact=''.join(x for x in [
        f'<li><a href="tel:+{intl}">{c["phone"]}</a></li>' if intl else '',
        f'<li><a href="https://wa.me/{intl}" target="_blank" rel="noopener">WhatsApp</a></li>' if intl else '',
        f'<li>{c["addr"][0]}<br>{c["addr"][1]}</li>' if c.get('addr') else f'<li>{c["place"]}</li>' if c.get('place') else '',
    ])
    desc=esc(strip(c['lead'])[:155])
    return f'''<!doctype html><html lang="nl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{esc(title)}</title><meta name="description" content="{desc}"><meta name="theme-color" content="#111">
<meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{desc}"><meta property="og:image" content="{img(c["photo"],1200)}">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?{c["fonts"]}&display=swap" rel="stylesheet">
<style>{css(c)}</style></head><body>
<header class="top"><div class="wrap"><a class="logo" href="{prefix or './'}"><b>{c["logo"]}</b><small>{c["logo_sub"]}</small></a>
<nav class="nav" aria-label="Hoofdmenu">{links}{callbtn}<button class="burger" aria-label="Menu" aria-expanded="false" onclick="var d=document.getElementById('dr');d.classList.toggle('open');this.setAttribute('aria-expanded',d.classList.contains('open'))"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 7h16M4 12h16M4 17h16"/></svg></button></nav></div></header>
<div class="drawer" id="dr">{drawer}</div>
<main>{body}</main>
<footer><div class="wrap"><div><b>{c["name"]}</b><p>{esc(strip(c["lead"]))}</p>{f'<p style="margin-top:14px">{STAR.replace("<svg","<svg style=\"width:15px;height:15px;color:#f5b301;display:inline;vertical-align:-2px\"")} <strong style="color:#fff">{rt}</strong> {"uit "+rc+" reviews op Google" if rc else "op Google"}</p>' if rt else ''}</div>
<div><h4>Pagina’s</h4><ul>{''.join(f'<li><a href="{prefix}{h or "./"}">{t}</a></li>' for h,t in nav)}</ul></div>
<div><h4>Contact</h4><ul>{foot_contact}</ul></div></div>
<div class="wrap"><div class="legal"><span>© {c["name"]}{", "+c["place"] if c.get("place") else ""}</span><span>Website door AgentBay</span></div></div></footer>
{f'<div class="mbar"><a class="btn light" href="tel:+{intl}">{PH}Bellen</a><a class="btn wa" href="https://wa.me/{intl}" target="_blank" rel="noopener">{WA}WhatsApp</a></div>' if intl else ''}
<script>
document.querySelectorAll('form[data-wa]').forEach(f=>f.addEventListener('submit',e=>{{e.preventDefault();const v=n=>(f.elements[n]?.value||'').trim();const er=f.querySelector('.err');
if(!v('naam')){{er.textContent='Vul je naam in.';f.elements.naam.focus();return}}er.textContent='';
const msg='Hoi, ik ben '+v('naam')+(v('plaats')?' uit '+v('plaats'):'')+'. {esc(c["wa_intro"])} '+v('soort').toLowerCase()+'.'+(v('tekst')?'\\n\\n'+v('tekst'):'');
window.open('https://wa.me/{intl}?text='+encodeURIComponent(msg),'_blank','noopener')}}));
</script>{c.get("page_js","") if pg=="afspraak/" else ""}</body></html>'''

def stars(): return '<span class="stars">'+STAR*5+'</span>'

def hero(c, prefix):
    rt,rc=rating_of(c)
    chip=f'<a class="chip" href="{c["maps"]}" target="_blank" rel="noopener">{stars()}<b>{rt}</b><span>{(rc+" reviews op Google") if rc else "op Google"}</span></a>' if rt else ''
    intl='31'+c['phone'].replace(' ','')[1:] if c['phone'] else ''
    tags=''.join(f'<span class="tag">{strip(t)}</span>' for t in c.get('tags',[])[:2])
    return f'''<section class="hero dark grain"><div class="wrap"><div><span class="eyebrow">{c["kick"]}</span><h1>{c["h1"]}</h1><p class="lead">{c["lead"]}</p>
<div class="cta"><a class="btn pri" href="{prefix}contact/">{c["cta"]}{ARROW}</a>{f'<a class="btn light" href="tel:+{intl}">{PH}{c["phone"]}</a>' if intl else ''}</div>{chip}</div>
<figure><img src="{img(c["photo"],1400)}" srcset="{img(c["photo"],700)} 700w, {img(c["photo"],1100)} 1100w, {img(c["photo"],1600)} 1600w" sizes="(min-width:980px) 46vw, 100vw" alt="{esc(c["alt"])}" fetchpriority="high"><figcaption>{tags}</figcaption></figure></div></section>'''

def trust(c):
    items=c['trust'][:4]
    return '<section class="trust"><div class="wrap">'+''.join(f'<div><b>{a}</b>{b}</div>' for a,b in items)+'</div></section>'

def svc_cards(c, n=6):
    out=''
    for i,s in enumerate(c['services'][:n]):
        meta=''
        if s.get('price') or s.get('min'):
            meta='<div class="meta">'+(f'<span>{s["price"]}</span>' if s.get('price') else '')+(f'<span class="muted">{s["min"]} min</span>' if s.get('min') else '')+'</div>'
        out+=f'<article class="svc"><span class="n">{i+1:02d}</span><h3>{s["name"]}</h3><p>{s["d"]}</p>{meta}</article>'
    return out

def steps(c, light=False):
    return '<ol class="steps">'+''.join(f'<li><b>{a}</b><span>{b}</span></li>' for a,b in c['steps'])+'</ol>'

def rating_block(c, prefix):
    rt,rc=rating_of(c)
    if not rt: return ''
    return f'''<section class="s rate"><div class="wrap"><div class="big">{rt}</div><div>{stars()}<h2>{(rc+" klanten") if rc else "Klanten"} beoordeelden {c["short"]} op Google.</h2><p class="muted" style="margin-top:10px">Lees zelf wat ze schrijven, of ervaar het met je eigen afspraak.</p></div>
<div style="display:flex;flex-wrap:wrap;gap:10px"><a class="btn line" href="{c["maps"]}" target="_blank" rel="noopener">Lees de reviews</a><a class="btn pri" href="{prefix}contact/">{c["cta"]}</a></div></div></section>'''

def contact_block(c, prefix, page=False):
    intl='31'+c['phone'].replace(' ','')[1:] if c['phone'] else ''
    opts=''.join(f'<option>{s["name"]}</option>' for s in c['services'])+'<option>Iets anders</option>'
    cards=''
    if intl:
        cards+=f'<a class="card" href="tel:+{intl}">{PH}<span><small>Bellen</small><b>{c["phone"]}</b></span></a>'
        cards+=f'<a class="card" href="https://wa.me/{intl}" target="_blank" rel="noopener">{WA}<span><small>WhatsApp</small><b>Stuur een bericht</b></span></a>'
    if c.get('addr'):
        cards+=f'<a class="card" href="{c["maps"]}" target="_blank" rel="noopener">{PIN}<span><small>Adres</small><b>{c["addr"][0]}, {c["addr"][1]}</b></span></a>'
    h=f'<h1 style="font-size:clamp(38px,5.4vw,60px);line-height:1.05;margin:14px 0 16px">{c["form_h"]}</h1>' if page else f'<h2 style="font-size:clamp(32px,4.4vw,50px);line-height:1.06;margin:14px 0 16px">{c["form_h"]}</h2>'
    return f'''<section class="s contact dark grain"><div class="wrap"><div><span class="eyebrow">{c["form_eyebrow"]}</span>{h}<p class="muted" style="font-size:18px">{c["form_p"]}</p><div class="cards">{cards}</div></div>
<form data-wa novalidate><h3>Vertel kort wat je zoekt</h3><div class="two"><label>Naam *<input name="naam" autocomplete="name" required></label><label>Plaats<input name="plaats" autocomplete="address-level2"></label></div>
<label>{c["f_kind"]}<select name="soort">{opts}</select></label><label>Omschrijving<textarea name="tekst" placeholder="{esc(c["f_ph"])}"></textarea></label>
<p class="err" role="alert"></p><button class="btn wa" type="submit">{WA}Verstuur via WhatsApp</button><p class="fine">{c["f_small"]}</p></form></div></section>'''

def area_block(c):
    if not c['area'] and not c.get('area_note'): return ''
    chips='<ul class="areas">'+''.join(f'<li>{a}</li>' for a in c['area'])+'</ul>' if c['area'] else ''
    return f'''<section class="s"><div class="wrap" style="display:grid;gap:30px;max-width:900px"><div class="sh" style="margin:0"><span class="eyebrow">{c.get("area_label","Werkgebied")}</span><h2>{c["area_h"]}</h2><p class="muted">{c.get("area_note","")}</p></div>{chips}</div></section>'''

def gallery(c):
    g=c.get('gallery') or []
    if not g: return ''
    return '<section class="s"><div class="wrap"><div class="sh"><span class="eyebrow">Recent werk</span><h2>'+c.get('gallery_h','Een greep uit ons werk.')+'</h2></div><div class="gal">'+''.join(f'<img src="{u}" alt="Foto van {esc(c["name"])}" loading="lazy">' for u in g[:9])+'</div></div></section>'

def reviews(c, prefix):
    R=c.get('reviews') or []
    if not R: return rating_block(c,prefix)
    rt,rc=rating_of(c)
    head=f'<div class="big" style="font-size:clamp(56px,7vw,84px)">{rt}</div><div>{stars()}<p class="muted">{(rc+" reviews op Google") if rc else "op Google"}</p></div>' if rt else ''
    cards=''.join(f'<figure class="rv"><span class="stars">{STAR*5}</span><blockquote>“{esc(t)}”</blockquote><figcaption><b>{esc(n)}</b>{(" · "+esc(w)) if w else ""}</figcaption></figure>' for t,n,w in R[:6])
    return f'''<section class="s" id="reviews"><div class="wrap"><div class="sh"><span class="eyebrow">Reviews</span><h2>Wat klanten zelf schrijven.</h2></div><div style="display:flex;gap:18px;align-items:center;margin-bottom:30px">{head}</div><div class="rvs">{cards}</div><a class="more" href="{c["maps"]}" target="_blank" rel="noopener">Alle reviews op Google {ARROW}</a></div></section>'''

def faq(c):
    items=c.get('faq') or []
    if not items: return ''
    return '<section class="s"><div class="wrap" style="max-width:900px"><div class="sh"><span class="eyebrow">Veelgestelde vragen</span><h2>Goed om te weten.</h2></div>'+''.join(f'<details><summary>{q}</summary><p>{a}</p></details>' for q,a in items)+'</div></section>'

def build(c, outdir):
    os.makedirs(outdir, exist_ok=True)
    P=lambda sub: os.path.join(outdir, sub, 'index.html') if sub else os.path.join(outdir,'index.html')
    stats_cls='stats s4' if len(c['usps'])>=4 else 'stats'
    stats='<div class="%s">'%stats_cls+''.join(f'<div><b>{a}</b><span>{b}</span></div>' for a,b in c['usps'][:4])+'</div>'
    # HOME
    pre=''
    body=hero(c,pre)+trust(c)
    body+=f'''<section class="s about"><div class="wrap"><div><span class="eyebrow">{c["over_label"]}</span><h2>{c["quote"]}</h2></div><div><div class="txt">{c["about"]}</div>{stats}<a class="more" href="over-ons/">Meer over {c["short"]} {ARROW}</a></div></div></section>'''
    body+=f'''<section class="s" style="background:var(--surface);border-block:1px solid var(--line)"><div class="wrap"><div class="sh"><span class="eyebrow">{c["svc_label"]}</span><h2>{c["svc_h"]}</h2><p class="muted">{c["svc_p"]}</p></div><div class="svcs">{svc_cards(c)}</div><a class="more" href="diensten/">{c["svc_more"]} {ARROW}</a></div></section>'''
    body+=f'<section class="band grain"><div class="wrap"><blockquote>“{strip(c["band"])}”</blockquote><small>{c["name"]}</small></div></section>'
    body+=f'''<section class="s dark grain"><div class="wrap"><div class="sh"><span class="eyebrow">Werkwijze</span><h2>{c["steps_h"]}</h2></div>{steps(c)}</div></section>'''
    body+=gallery(c)+reviews(c,pre)
    body+=contact_block(c,pre)
    open(P(''),'w').write(page(c,'',c['title'],body,pre))
    # DIENSTEN
    pre='../'
    rows=''
    for i,s in enumerate(c['services']):
        pr=s.get('price') or ''
        if s.get('min'): pr=(pr+' · ' if pr else '')+f'{s["min"]} min'
        rows+=f'<article><span class="n">{i+1:02d}</span><h3>{s["name"]}</h3><p>{s.get("long") or s["d"]}</p><span class="pr">{pr}</span></article>'
    body=f'''<section class="ph dark grain"><div class="wrap"><span class="crumbs"><a href="../">Home</a> / Diensten</span><h1>{c["svc_h"]}</h1><p class="muted">{c["svc_p"]}</p></div></section>
<section class="s"><div class="wrap"><div class="dl">{rows}</div>{('<p class="muted" style="margin-top:22px;font-size:14px">'+c["price_note"]+'</p>') if c.get("price_note") else ''}</div></section>
<section class="s" style="background:var(--alt)"><div class="wrap light"><div class="sh"><span class="eyebrow">Werkwijze</span><h2>{c["steps_h"]}</h2></div>{steps(c)}</div></section>'''+contact_block(c,pre)
    os.makedirs(os.path.dirname(P('diensten')),exist_ok=True)
    open(P('diensten'),'w').write(page(c,'diensten/',f'Diensten | {c["name"]}',body,pre))
    # OVER ONS
    body=f'''<section class="ph dark grain"><div class="wrap"><span class="crumbs"><a href="../">Home</a> / Over ons</span><h1>{c["quote"]}</h1></div></section>
<section class="s about"><div class="wrap"><div><span class="eyebrow">{c["over_label"]}</span><div class="txt" style="margin-top:18px">{c["about"]}{c.get("about_more","")}</div></div><div><img src="{img(c["photo"],1100)}" alt="{esc(c["alt"])}" style="width:100%;aspect-ratio:4/3;object-fit:cover;border-radius:calc(var(--r2) * 1.4)" loading="lazy">{stats}</div></div></section>
<section class="band grain"><div class="wrap"><blockquote>“{strip(c["band"])}”</blockquote><small>{c["name"]}</small></div></section>
<section class="s"><div class="wrap light"><div class="sh"><span class="eyebrow">Werkwijze</span><h2>{c["steps_h"]}</h2></div>{steps(c)}</div></section>'''+area_block(c)+faq(c)+rating_block(c,pre)+contact_block(c,pre)
    os.makedirs(os.path.dirname(P('over-ons')),exist_ok=True)
    open(P('over-ons'),'w').write(page(c,'over-ons/',f'Over ons | {c["name"]}',body,pre))
    # CONTACT
    body=contact_block(c,pre,page=True)+area_block(c)
    if c.get('hours'):
        body+='<section class="s" style="padding-top:0"><div class="wrap" style="max-width:900px"><div class="sh"><span class="eyebrow">Openingstijden</span><h2>Wanneer je ons bereikt.</h2></div><table style="width:100%;border-collapse:collapse;font-size:17px">'+''.join(f'<tr style="border-bottom:1px solid var(--line)"><td style="padding:12px 0">{d}</td><td style="text-align:right">{t}</td></tr>' for d,t in c['hours'])+'</table></div></section>'
    os.makedirs(os.path.dirname(P('contact')),exist_ok=True)
    open(P('contact'),'w').write(page(c,'contact/',f'Contact | {c["name"]}',body,pre))
    # AFSPRAAK (booking)
    if c.get('book'):
        body=f'''<section class="ph dark grain"><div class="wrap"><span class="crumbs"><a href="../">Home</a> / Afspraak</span><h1>Plan je afspraak</h1><p class="muted">Kies een behandeling en een moment. Je ziet direct welke tijden nog vrij zijn.</p></div></section>
<section class="s"><div class="wrap"><style>{c["bk_css"]}</style><div class="bk" id="bk" style="margin:0 auto"></div></div></section>'''
        os.makedirs(os.path.dirname(P('afspraak')),exist_ok=True)
        open(P('afspraak'),'w').write(page(c,'afspraak/',f'Afspraak maken | {c["name"]}',body,pre))
