(function(){
"use strict";
document.querySelectorAll('[data-toggle]').forEach(function(b){b.addEventListener('click',function(){var d=document.getElementById(b.getAttribute('data-toggle'));if(!d)return;var o=d.classList.toggle('open');b.setAttribute('aria-expanded',o?'true':'false')})});
var _hd=(new Date().getDay()+6)%7,_hr=document.querySelector('#hrs tr[data-d="'+_hd+'"]');if(_hr)_hr.className='today';
})();