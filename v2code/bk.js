(function(){
const C=window.BOOK,root=document.getElementById('bk');if(!root)return;
const pad=n=>String(n).padStart(2,'0'),hm=m=>pad(Math.floor(m/60))+':'+pad(m%60),ymd=d=>d.getFullYear()+'-'+pad(d.getMonth()+1)+'-'+pad(d.getDate());
const DN=['zo','ma','di','wo','do','vr','za'],MN=['jan','feb','mrt','apr','mei','jun','jul','aug','sep','okt','nov','dec'];
const KEY='bk-'+C.key;let list=[];try{list=JSON.parse(localStorage.getItem(KEY)||'[]')}catch(e){}
const save=()=>{try{localStorage.setItem(KEY,JSON.stringify(list))}catch(e){}};
const esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const st={step:0,svc:null,date:null,time:null,name:'',phone:'',note:'',loc:'salon',addr:'',done:null};
const svc=()=>C.services.find(s=>s.id===st.svc);
const fd=k=>{const[y,m,d]=k.split('-').map(Number),t=new Date(y,m-1,d);return DN[t.getDay()]+' '+d+' '+MN[m-1]};
const meta=s=>(s.price?s.price+'<br>':'')+s.min+' min';
function slots(k){const[y,m,d]=k.split('-').map(Number),h=C.hours[new Date(y,m-1,d).getDay()];if(!h)return[];
 const len=svc().min,out=[],now=new Date(),today=ymd(now)===k,nm=now.getHours()*60+now.getMinutes();
 for(let t=h[0];t+len<=h[1];t+=C.step||30){const busy=list.some(b=>b.date===k&&t<b.start+b.len&&b.start<t+len);out.push({t,ok:!busy&&!(today&&t<=nm+30)})}return out}
root.innerHTML='<ol class="bk-steps" aria-label="Stappen"><li><b>1</b>Behandeling</li><li><b>2</b>Moment</li><li><b>3</b>Gegevens</li></ol><div class="bk-pane" aria-live="polite"></div><div class="bk-foot"><button class="bk-btn" type="button" data-back>Terug</button><span class="bk-sum"></span><button class="bk-btn pri" type="button" data-next>Ga verder</button></div>';
const pane=root.querySelector('.bk-pane'),back=root.querySelector('[data-back]'),next=root.querySelector('[data-next]'),sum=root.querySelector('.bk-sum');
function go(n){st.step=n;render();const t=root.getBoundingClientRect().top;if(t<0||t>innerHeight*.6)root.scrollIntoView({block:'start',behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth'})}
function render(){
 root.querySelectorAll('.bk-steps li').forEach((li,i)=>{li.className=st.done?'done':i===st.step?'on':i<st.step?'done':'';li.setAttribute('aria-current',i===st.step&&!st.done?'step':'false')});
 if(st.done)return done();
 back.style.visibility=st.step?'visible':'hidden';next.textContent=st.step===2?'Bevestigen':'Ga verder';
 sum.textContent=[svc()&&svc().name,st.time!=null&&st.date&&fd(st.date)+' '+hm(st.time)].filter(Boolean).join(', ');
 if(st.step===0){
  const groups=[...new Set(C.services.map(s=>s.g))];
  pane.innerHTML='<h3>Welke behandeling?</h3>'+groups.map(g=>'<p class="bk-grp">'+g+'</p><div class="bk-opts">'+C.services.filter(s=>s.g===g).map(s=>'<button type="button" class="bk-opt" data-s="'+s.id+'" aria-pressed="'+(st.svc===s.id)+'"><span>'+s.name+'</span><small>'+meta(s)+'</small></button>').join('')+'</div>').join('');
  pane.querySelectorAll('[data-s]').forEach(b=>b.onclick=()=>{st.svc=b.dataset.s;st.time=null;go(1)});next.disabled=!st.svc;
 }else if(st.step===1){
  const days=[],d0=new Date();d0.setHours(0,0,0,0);for(let i=0;i<21;i++){const d=new Date(d0);d.setDate(d0.getDate()+i);days.push(d)}
  if(!st.date||!slots(st.date).some(s=>s.ok)){const f=days.find(d=>slots(ymd(d)).some(s=>s.ok));st.date=f?ymd(f):null}
  const sl=st.date?slots(st.date):[];
  pane.innerHTML='<h3>Wanneer komt het je uit?</h3><div class="bk-days" role="group" aria-label="Kies een dag">'+days.map(d=>{const k=ymd(d),open=!!C.hours[d.getDay()];return '<button type="button" class="bk-day" data-d="'+k+'" aria-pressed="'+(st.date===k)+'"'+(open?'':' disabled aria-label="'+DN[d.getDay()]+' '+d.getDate()+' '+MN[d.getMonth()]+', gesloten"')+'>'+DN[d.getDay()]+'<b>'+d.getDate()+'</b>'+MN[d.getMonth()]+'</button>'}).join('')+'</div>'+
   (sl.some(s=>s.ok)?'<div class="bk-slots" role="group" aria-label="Kies een tijd">'+sl.map(s=>'<button type="button" class="bk-slot" data-t="'+s.t+'" aria-pressed="'+(st.time===s.t)+'"'+(s.ok?'':' disabled')+'>'+hm(s.t)+'</button>').join('')+'</div>':'<p class="bk-empty">Op deze dag is niets meer vrij. Kies een andere dag.</p>');
  pane.querySelectorAll('[data-d]').forEach(b=>b.onclick=()=>{st.date=b.dataset.d;st.time=null;render()});
  pane.querySelectorAll('[data-t]').forEach(b=>b.onclick=()=>{st.time=+b.dataset.t;render()});
  const sel=pane.querySelector('.bk-day[aria-pressed="true"]');if(sel)sel.scrollIntoView({block:'nearest',inline:'nearest'});
  next.disabled=st.time==null;
 }else{
  pane.innerHTML='<h3>Je gegevens</h3>'+
   (C.location?'<fieldset class="bk-field"><legend>Waar?</legend><div class="bk-seg"><label><input type="radio" name="bk-loc" id="bk-loc-s" value="salon"'+(st.loc==='salon'?' checked':'')+'>In de salon</label><label><input type="radio" name="bk-loc" id="bk-loc-h" value="thuis"'+(st.loc==='thuis'?' checked':'')+'>Bij mij thuis</label></div></fieldset>'+
    '<div class="bk-field" id="bk-addr-w"'+(st.loc==='thuis'?'':' hidden')+'><label for="bk-addr">Adres</label><input id="bk-addr" autocomplete="street-address" value="'+esc(st.addr)+'"></div>':'')+
   '<div class="bk-field"><label for="bk-name">Naam</label><input id="bk-name" autocomplete="name" value="'+esc(st.name)+'"></div>'+
   '<div class="bk-field"><label for="bk-phone">Telefoonnummer</label><input id="bk-phone" type="tel" inputmode="tel" autocomplete="tel" value="'+esc(st.phone)+'"></div>'+
   '<div class="bk-field"><label for="bk-note">Opmerking (optioneel)</label><textarea id="bk-note">'+esc(st.note)+'</textarea></div><p class="bk-err" id="bk-err"></p>';
  const bind=(id,k)=>{const el=pane.querySelector('#'+id);if(el)el.oninput=e=>st[k]=e.target.value};
  bind('bk-name','name');bind('bk-phone','phone');bind('bk-note','note');bind('bk-addr','addr');
  pane.querySelectorAll('[name="bk-loc"]').forEach(r=>r.onchange=()=>{st.loc=r.value;pane.querySelector('#bk-addr-w').hidden=st.loc!=='thuis'});
  next.disabled=false;
 }
}
back.onclick=()=>{if(st.step)go(st.step-1)};
next.onclick=()=>{
 if(st.done){Object.assign(st,{step:0,svc:null,date:null,time:null,note:'',done:null});return go(0)}
 if(st.step<2)return go(st.step+1);
 const er=pane.querySelector('#bk-err');
 if(st.name.trim().length<2){er.textContent='Vul je naam in.';return pane.querySelector('#bk-name').focus()}
 if(st.phone.replace(/\D/g,'').length<9){er.textContent='Vul een geldig telefoonnummer in, bijvoorbeeld 06 12345678.';return pane.querySelector('#bk-phone').focus()}
 if(C.location&&st.loc==='thuis'&&st.addr.trim().length<5){er.textContent='Vul het adres in waar we langskomen.';return pane.querySelector('#bk-addr').focus()}
 const s=svc();if(!slots(st.date).some(x=>x.t===st.time&&x.ok)){st.time=null;return go(1)}
 const b={date:st.date,start:st.time,len:s.min,svc:s.id,name:st.name.trim(),phone:st.phone.trim(),loc:st.loc,addr:st.addr.trim()};list.push(b);save();st.done=b;render();
};
function done(){const b=st.done,s=C.services.find(x=>x.id===b.svc);
 pane.innerHTML='<div class="bk-done"><h3>Je afspraak staat genoteerd</h3><dl><dt>Behandeling</dt><dd>'+s.name+'</dd>'+(s.price?'<dt>Prijs</dt><dd>'+s.price+'</dd>':'')+'<dt>Wanneer</dt><dd>'+fd(b.date)+', '+hm(b.start)+' tot '+hm(b.start+b.len)+'</dd>'+(C.location?'<dt>Waar</dt><dd>'+(b.loc==='thuis'?esc(b.addr):'In de salon')+'</dd>':'')+'<dt>Naam</dt><dd>'+esc(b.name)+'</dd></dl><p class="bk-empty">Lukt het toch niet? Laat het even weten via '+C.phone+'.</p></div>';
 back.style.visibility='hidden';sum.textContent='';next.disabled=false;next.textContent='Nog een afspraak';
}
render();
document.querySelectorAll('[data-copy]').forEach(b=>b.addEventListener('click',()=>{const t=b.dataset.copy,o=b.textContent;const ok=()=>{b.textContent='Gekopieerd';setTimeout(()=>b.textContent=o,1600)};
 try{navigator.clipboard.writeText(t).then(ok,()=>sel(b))}catch(e){sel(b)}}));
function sel(b){const n=b.previousElementSibling;if(!n)return;const r=document.createRange();r.selectNodeContents(n);const s=getSelection();s.removeAllRanges();s.addRange(r)}
})();
