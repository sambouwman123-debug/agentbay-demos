(function(){
  var btn=document.getElementById('menuBtn');
  var nav=document.getElementById('nav');
  var mobile=document.getElementById('mobile');
  if(btn){btn.addEventListener('click',function(){
    var open=mobile.style.display==='block';
    mobile.style.display=open?'none':'block';
  });}
  // close mobile menu on link click
  if(mobile){mobile.querySelectorAll('a').forEach(function(a){
    a.addEventListener('click',function(){mobile.style.display='none';});
  });}
})();
