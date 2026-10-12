(function(){
"use strict";
document.querySelectorAll('[data-toggle]').forEach(function(b){b.addEventListener('click',function(){var d=document.getElementById(b.getAttribute('data-toggle'));if(!d)return;var o=d.classList.toggle('open');b.setAttribute('aria-expanded',o?'true':'false')})});
var _hd=(new Date().getDay()+6)%7,_hr=document.querySelector('#hrs tr[data-d="'+_hd+'"]');if(_hr)_hr.className='today';
var WAINTRO="Ik wil graag een afspraak voor",WAPHONE="31640944777";
document.querySelectorAll('form[data-wa]').forEach(function(f){f.addEventListener('submit',function(e){e.preventDefault();var v=function(n){return((f.elements[n]&&f.elements[n].value)||'').trim()};var er=f.querySelector('.err');if(!v('naam')){if(er)er.textContent='Vul je naam in.';if(f.elements.naam)f.elements.naam.focus();return}if(er)er.textContent='';var msg='Hoi, ik ben '+v('naam')+(v('plaats')?' uit '+v('plaats'):'')+'. '+WAINTRO+' '+v('soort').toLowerCase()+'.'+(v('tekst')?'\n\n'+v('tekst'):'');window.open('https://wa.me/'+WAPHONE+'?text='+encodeURIComponent(msg),'_blank','noopener')})});
})();