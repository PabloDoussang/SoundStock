'use strict';
// Las gráficas se dibujan con datos JSON del servidor. No almacenamos stock en el navegador.
const svgNS = 'http://www.w3.org/2000/svg';
function svgEl(name, attrs, text) {
  const node = document.createElementNS(svgNS, name);
  for (const [key,value] of Object.entries(attrs)) node.setAttribute(key, String(value));
  if (text !== undefined) node.textContent = text;
  return node;
}
document.querySelectorAll('[data-chart]').forEach(container => {
  const data = JSON.parse(document.getElementById(container.dataset.chart).textContent);
  if (!data.length) { const p=document.createElement('p');p.className='empty';p.textContent='Sin movimientos en este período.';container.append(p);return; }
  const width=Math.max(600,data.length*34),height=250,left=48,right=16,top=18,bottom=40;
  const raw=data.flatMap(d=>[d.entrada,d.salida,d.ajuste]);
  const max=Math.max(1,...raw)*1.1, min=Math.min(0,...raw)*1.1;
  const y=v=>top+(max-v)/(max-min)*(height-top-bottom);
  const svg=svgEl('svg',{viewBox:'0 0 '+width+' '+height,style:'min-width:'+(data.length > 22 ? Math.min(width,2400) : 310)+'px'});
  for(let i=0;i<5;i++) {
    const val=min+(max-min)*i/4, yp=y(val);
    svg.append(svgEl('line',{x1:left,y1:yp,x2:width-right,y2:yp,stroke:'#e4ece6','stroke-dasharray':'3 4'}));
    svg.append(svgEl('text',{x:left-8,y:yp+4,'text-anchor':'end',fill:'#819086','font-size':11},Math.round(val).toLocaleString('es-CL')));
  }
  svg.append(svgEl('line',{x1:left,y1:y(0),x2:width-right,y2:y(0),stroke:'#a9bcb0'}));
  const step=(width-left-right)/data.length, bw=Math.min(12,step/4.5);
  data.forEach((row,i)=>{
    const center=left+step*(i+.5);
    ['entrada','salida','ajuste'].forEach((key,j)=>{
      const val=row[key], bar=svgEl('rect',{x:center+(j-1.5)*bw,y:Math.min(y(val),y(0)),width:Math.max(2,bw-2),height:Math.max(val===0?0:2,Math.abs(y(val)-y(0))),rx:2,fill:['#4d9e79','#24463d','#d8a250'][j]});
      bar.append(svgEl('title',{},row.date+' · '+key+': '+val+' unidades'));svg.append(bar);
    });
    if(data.length<22 || i%Math.ceil(data.length/18)===0) svg.append(svgEl('text',{x:center,y:height-14,'text-anchor':'middle',fill:'#718176','font-size':11},row.date.slice(8,10)+'/'+row.date.slice(5,7)));
  });
  container.append(svg);
});
document.querySelectorAll('[data-category-chart]').forEach(el=>{
  const data=JSON.parse(document.getElementById(el.dataset.categoryChart).textContent);
  const total=data.reduce((a,b)=>a+b.total,0);
  if(!total){el.style.display='none';return;}
  data.forEach((row,i)=>{if(!row.total)return;const part=document.createElement('span');part.style.width=(row.total/total*100)+'%';part.style.background=['#24463d','#4d9e79','#8abd91','#d8a250','#91a9b5','#d1ddbf'][i%6];part.title=row.category+': '+row.total+' unidades';el.append(part);});
});
const stockForm=document.getElementById('stock-form');
if(stockForm){
  const data=JSON.parse(document.getElementById('stock-data').textContent),product=document.getElementById('id_product'),kind=document.getElementById('id_kind'),quantity=document.getElementById('id_quantity'),dest=document.getElementById('id_destination'),preview=document.getElementById('stock-preview');
  function update(){
    const p=data.find(p=>p.id===Number(product.value)), n=quantity.value===''?null:Number(quantity.value);
    dest.closest('.field').hidden=kind.value!=='salida';dest.required=kind.value==='salida';
    quantity.min=kind.value==='ajuste'?'0':'1';
    if(!p){preview.textContent='Selecciona un producto para consultar sus existencias.';return;}
    const after=n===null?null:kind.value==='ajuste'?n:p.stock+(kind.value==='entrada'?n:-n);
    preview.textContent='Ubicación: '+p.location+' · Stock actual: '+p.stock+' unidades'+(after===null?'':' → Stock previsto: '+after+' unidades')+(after<0?' · Stock insuficiente.':'');
  }
  [product,kind,quantity].forEach(el=>el.addEventListener('input',update));update();
}

// Navegación interna en la pestaña actual, también en navegadores integrados.
document.addEventListener('click', (event) => {
  if (event.defaultPrevented || event.button !== 0 || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
  const link = event.target.closest?.('a[href]');
  if (!link || link.hasAttribute('download')) return;
  const destination = new URL(link.href, window.location.href);
  if (destination.origin !== window.location.origin || !['http:', 'https:'].includes(destination.protocol)) return;
  if (destination.pathname === window.location.pathname && destination.search === window.location.search && destination.hash) return;
  if (destination.pathname.startsWith('/exportar/')) return;
  event.preventDefault();
  event.stopPropagation();
  window.location.assign(destination.href);
}, true);
