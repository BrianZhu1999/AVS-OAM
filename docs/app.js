const $ = id => document.getElementById(id);
const OBS = ['pressure_only', 'pressure_plus_vx_vy', 'pressure_plus_vx_vy_vz'];
const LABELS = ['Pressure only', 'Transverse AVS', 'Full AVS'];
const CLASSES = ['pressure', 'transverse', 'full'];
const COLORS = ['#536f83', '#9b7115', '#7653a7'];
const COMPONENTS = ['p', 'ṽₓ', 'ṽᵧ', 'ṽz'];
const TAU = Math.PI * 2;
const reduced = window.matchMedia('(prefers-reduced-motion: reduce)');
// Shared scientific formatting: no insignificant trailing zeros or negative zero.
const fmt = (n, digits=4) => {
  if (Math.abs(n) < 1e-12) return '0';
  return String(Number(Number(n).toPrecision(digits))).replace(/e-0/g, 'e−');
};
const num = n => new Intl.NumberFormat('en-US').format(n);
const cache = new Map();
async function data(file) {
  if (!cache.has(file)) cache.set(file, fetch(`data/${file}.json`).then(r => {
    if (!r.ok) throw Error(`Could not load ${file}: HTTP ${r.status}`);
    return r.json();
  }));
  return cache.get(file);
}
function guard(region, fn) {
  return fn().catch(error => {
    console.error(error);
    const p = document.createElement('p'); p.className='load-error';
    p.textContent='This explorer could not load its data. Reload the page or use the source downloads below.';
    $(region).append(p);
  });
}
function setupCanvas(canvas, height) {
  const w = Math.max(1, canvas.clientWidth), h = typeof height==='function' ? height(w) : height;
  const dpr = Math.min(window.devicePixelRatio || 1, 2);
  if (canvas.width!==Math.round(w*dpr) || canvas.height!==Math.round(h*dpr)) {
    canvas.width=Math.round(w*dpr); canvas.height=Math.round(h*dpr); canvas.style.height=`${h}px`;
  }
  const c=canvas.getContext('2d'); c.setTransform(dpr,0,0,dpr,0,0); c.clearRect(0,0,w,h);
  c.font='13px "Segoe UI", Arial, sans-serif'; c.fillStyle='#596879';
  return {c,w,h};
}
function observeSize(element, draw) { new ResizeObserver(draw).observe(element); }
function text(c,s,x,y,align='center',color='#596879',size=13) {
  c.fillStyle=color; c.font=`${size}px "Segoe UI", Arial, sans-serif`; c.textAlign=align; c.textBaseline='middle'; c.fillText(s,x,y);
}
function line(c,x1,y1,x2,y2,color='#d9e0e7',width=1,dash=[]) {
  c.beginPath(); c.setLineDash(dash); c.strokeStyle=color;c.lineWidth=width;c.moveTo(x1,y1);c.lineTo(x2,y2);c.stroke();c.setLineDash([]);
}
function circle(c,x,y,r,fill,stroke,sw=1) {
  c.beginPath();c.arc(x,y,r,0,TAU);if(fill){c.fillStyle=fill;c.fill();}if(stroke){c.strokeStyle=stroke;c.lineWidth=sw;c.stroke();}
}
function pointer(canvas,event) {const r=canvas.getBoundingClientRect();return {x:event.clientX-r.left,y:event.clientY-r.top};}
function option(value,label) {const o=document.createElement('option');o.value=value;o.textContent=label;return o;}

async function initField() {
  const fields=await data('fields');const canvas=$('field-canvas');
  const tile=document.createElement('canvas');tile.width=101;tile.height=101;const tc=tile.getContext('2d');const pixels=tc.createImageData(101,101);
  let mode='2',phase=0,playing=false,visible=true,last=0;
  function draw(){
    const {c,w}=setupCanvas(canvas,w=>w+62);const left=43,top=24,side=w-62;
    const arr=fields[mode],co=Math.cos(phase),si=Math.sin(phase);
    for(let j=0;j<101;j++)for(let i=0;i<101;i++){
      const a=j*101+i,p=4*((100-j)*101+i),v=Math.max(-1,Math.min(1,arr.pr[a]*co+arr.pi[a]*si));
      const col=v>=0?[190,52,56]:[43,90,163],t=Math.abs(v);
      pixels.data[p]=Math.round(248+(col[0]-248)*t);pixels.data[p+1]=Math.round(249+(col[1]-249)*t);pixels.data[p+2]=Math.round(251+(col[2]-251)*t);pixels.data[p+3]=255;
    }
    tc.putImageData(pixels,0,0);c.imageSmoothingEnabled=true;c.drawImage(tile,left,top,side,side);
    if($('velocity').checked){
      for(let j=8;j<101;j+=8)for(let i=8;i<101;i+=8){
        const n=j*101+i,vx=arr.xr[n]*co+arr.xi[n]*si,vy=arr.yr[n]*co+arr.yi[n]*si;
        const len=Math.hypot(vx,vy);if(len<.035)continue;
        const scale=side*.017/Math.max(1,len),dx=vx*scale,dy=-vy*scale,x=left+i/100*side,y=top+(100-j)/100*side;
        line(c,x-dx/2,y-dy/2,x+dx/2,y+dy/2,'#253a4bc0',.9);
        const a=Math.atan2(dy,dx),ex=x+dx/2,ey=y+dy/2;
        line(c,ex,ey,ex-3*Math.cos(a-.55),ey-3*Math.sin(a-.55),'#253a4bc0',.9);
        line(c,ex,ey,ex-3*Math.cos(a+.55),ey-3*Math.sin(a+.55),'#253a4bc0',.9);
      }
    }
    c.setLineDash([4,4]);circle(c,left+side/2,top+side/2,side*.15,null,'#263d66a0');c.setLineDash([]);
    for(const v of [-40,0,40]){text(c,String(v),left+(v+40)/80*side,top+side+17);text(c,String(v),left-10,top+(40-v)/80*side,'right');}
    text(c,'x (cm)',left+side/2,top+side+38);c.save();c.translate(10,top+side/2);c.rotate(-Math.PI/2);text(c,'y (cm)',0,0);c.restore();
    text(c,`ℓ = ${mode}`,left+10,top+17,'left','#202b38',15);
    const bx=left+side*.3,by=top+side+60,bw=side*.4,grad=c.createLinearGradient(bx,0,bx+bw,0);grad.addColorStop(0,'#2b5aa3');grad.addColorStop(.5,'#f8f9fb');grad.addColorStop(1,'#be3438');c.fillStyle=grad;c.fillRect(bx,by,bw,7);
    text(c,'−1',bx-9,by+3,'right',undefined,11);text(c,'0',bx+bw/2,by+19,'center',undefined,11);text(c,'1',bx+bw+9,by+3,'left',undefined,11);
    $('phase-value').textContent=`${Math.round(phase/TAU*360)%360}°`;
  }
  $('field-mode').onchange=e=>{mode=e.target.value;draw();};$('velocity').onchange=draw;
  $('field-phase').oninput=e=>{phase=+e.target.value/360*TAU;draw();};
  function setPlaying(v){playing=v;last=0;$('field-play').textContent=playing?'Pause phase':'Play phase';$('field-play').setAttribute('aria-pressed',String(playing));}
  $('field-play').onclick=()=>setPlaying(!playing);
  new IntersectionObserver(entries=>{visible=entries[0].isIntersecting;last=0;}).observe(canvas);
  reduced.addEventListener('change',()=>{if(reduced.matches)setPlaying(false);});
  function tick(t){if(playing&&visible&&!document.hidden){if(last){phase=(phase+(t-last)/12000*TAU)%TAU;$('field-phase').value=Math.round(phase/TAU*360);draw();}last=t;}else last=0;requestAnimationFrame(tick);}
  observeSize(canvas,draw);draw();requestAnimationFrame(tick);
}

async function initReceiver(){
  const r=await data('receiver'),canvas=$('receiver-canvas');let selected=0,strategy=2,mode=2,hit=[];
  for(let i=0;i<5;i++)$('receiver-select').append(option(i,`Point ${i+1}`));
  function drawRing(){const {c,w}=setupCanvas(canvas,w=>w*.82);const cx=w/2,cy=w*.39,rad=w*.28;circle(c,cx,cy,rad,null,'#bbc8d8',1.5);line(c,cx-rad-25,cy,cx+rad+25,cy,'#e0e5ec');line(c,cx,cy-rad-25,cx,cy+rad+25,'#e0e5ec');text(c,'x',cx+rad+29,cy,'left');text(c,'y',cx,cy-rad-33);hit=[];
    for(let i=0;i<5;i++){const a=TAU*i/5,x=cx+rad*Math.cos(a),y=cy-rad*Math.sin(a);hit.push({x,y});circle(c,x,y,i===selected?12:7,i===selected?'#194cac':'white','#194cac',2);text(c,String(i+1),cx+(rad+25)*Math.cos(a),cy-(rad+25)*Math.sin(a),'center','#194cac',14);}
    text(c,'co-located p, ṽₓ, ṽᵧ, ṽz',cx,cy+rad+47,'center','#596879',12);
  }
  function update(){
    $('receiver-select').value=selected;drawRing();const n=[1,3,4][strategy];
    $('channel-readouts').replaceChildren(...COMPONENTS.map((name,i)=>{const d=document.createElement('div');d.className='channel'+(i>=n?' inactive':'');const a=r.raw_real[i*5+selected][mode],b=r.raw_imag[i*5+selected][mode];d.innerHTML=`<strong>${name}</strong><code>${fmt(a,3)} ${b<0?'−':'+'}<br>${fmt(Math.abs(b),3)}i</code>`;return d;}));
    $('matrix-shape').textContent=`${n*5} rows × 4 modes · |Aeff|`;
    const mat=r.matrices[strategy].magnitude,max=Math.max(...mat.flat());const tbody=$('receiver-matrix').tBodies[0];tbody.replaceChildren();
    mat.forEach((row,i)=>{const tr=document.createElement('tr');if(i%5===selected)tr.className='active-row';const td=document.createElement('td');td.textContent=`${COMPONENTS[Math.floor(i/5)]} · ${i%5+1}`;tr.append(td);row.forEach(v=>{const cell=document.createElement('td');cell.textContent=fmt(v,3);cell.style.backgroundColor=`rgba(25,76,172,${.04+.35*v/max})`;tr.append(cell);});tbody.append(tr);});
  }
  canvas.onclick=e=>{const p=pointer(canvas,e),idx=hit.findIndex(a=>Math.hypot(a.x-p.x,a.y-p.y)<25);if(idx>=0){selected=idx;update();}};
  $('receiver-select').onchange=e=>{selected=+e.target.value;update();};$('receiver-strategy').onchange=e=>{strategy=+e.target.value;update();};$('probe-mode').onchange=e=>{mode=+e.target.value;update();};observeSize(canvas,drawRing);update();
}

async function initGeometry(){
  const g=await data('codewords');let selected=0;const cards=[];const limit=Math.max(...g.views.flatMap(v=>v.xy.flat().map(Math.abs)))*1.22;
  g.symbols.forEach((s,i)=>$('codeword-select').append(option(i,`${i} · [${s.map(x=>x>0?'+1':'−1').join(', ')}]`)));
  g.views.forEach((view,k)=>{const card=document.createElement('div');card.className='geometry-card';card.innerHTML=`<h3 class="${CLASSES[k]}">${LABELS[k]}</h3><canvas aria-label="Two-dimensional projection of ${LABELS[k]} codewords"></canvas><dl><dt>Nearest squared distance</dt><dd class="dmin"></dd><dt>2D variance retained</dt><dd>${fmt(view.retained_variance*100,3)}%</dd></dl><p class="nearest"></p>`;const can=card.querySelector('canvas');$('geometry-grid').append(card);cards.push({card,can,view,points:[]});can.onclick=e=>{const p=pointer(can,e),hit=cards[k].points.find(a=>Math.hypot(a.x-p.x,a.y-p.y)<20);if(hit){const idx=hit.ids.indexOf(selected);selected=hit.ids[(idx+1)%hit.ids.length];update();}};observeSize(can,()=>draw(k));});
  function draw(k){const {card,can,view}=cards[k],{c,w}=setupCanvas(can,w=>w*.9+20);const m=26,side=w-m*2,xx=x=>m+(x+limit)/(2*limit)*side,yy=y=>m+(limit-y)/(2*limit)*side;
    line(c,xx(-limit),yy(0),xx(limit),yy(0),'#dce3ec');line(c,xx(0),yy(-limit),xx(0),yy(limit),'#dce3ec');text(c,'MDS 1',w-2,yy(0)+18,'right',undefined,10);text(c,'MDS 2',xx(0)+8,10,'left',undefined,10);
    const d=view.d2[selected],minimum=Math.min(...d.filter((_,i)=>i!==selected));const nearest=d.map((v,i)=>i!==selected&&Math.abs(v-minimum)<1e-7?i:-1).filter(i=>i>=0);
    const groups=new Map();view.xy.forEach((xy,i)=>{const key=xy.map(v=>Number(v.toFixed(6))).join(',');if(!groups.has(key))groups.set(key,{x:xx(xy[0]),y:yy(xy[1]),ids:[]});groups.get(key).ids.push(i);});
    const start=view.xy[selected];nearest.forEach(i=>line(c,xx(start[0]),yy(start[1]),xx(view.xy[i][0]),yy(view.xy[i][1]),'#c4ccda',1,[4,4]));
    cards[k].points=[...groups.values()];for(const p of groups.values()){
      const active=p.ids.includes(selected),near=p.ids.some(i=>nearest.includes(i));circle(c,p.x,p.y,active?9:6,active?COLORS[k]:'#fff',COLORS[k],near?2.5:1.5);
      if(active)circle(c,p.x,p.y,13,null,COLORS[k],1);
      if(p.ids.length>1)text(c,`×${p.ids.length}`,p.x+12,p.y-14,'left','#596879',11);
    }
    card.querySelector('.dmin').textContent=fmt(minimum,6);card.querySelector('.nearest').textContent=`Nearest codeword${nearest.length>1?'s':''}: ${nearest.join(', ')}. Filled marker: ${selected}.`;
  }
  function update(){$('codeword-select').value=selected;$('codeword-label').textContent=`s = [${g.symbols[selected].map(x=>x>0?'+1':'−1').join(', ')}]`;cards.forEach((_,k)=>draw(k));}
  $('codeword-select').onchange=e=>{selected=+e.target.value;update();};update();
}

const EXP = {
  snr:{x:'SNR_dB',label:'SNR (dB)',fig:'Fig. 3',context:'Pressure nonorthogonality ε = 0.35; received-mode-power normalization before AVS noise whitening. 200000 frames per point.'},
  offset_nominal:{x:'receiver_offset_R',label:'Receiver offset / R',fig:'Fig. 5',context:'SNR = 6 dB; detector retains the nominal receiving matrix. 200000 frames per point.'},
  offset_calibrated:{x:'receiver_offset_R',label:'Receiver offset / R',fig:'Fig. 7',context:'SNR = 6 dB; detector calibrated at the actual receiver offset. 200000 frames per point.'},
  distance:{x:'z_rx_m',label:'Propagation distance z (m)',fig:'Fig. 8',context:'Nominal SNR = 0 dB at z₀ = 1.2 m; normalization fixed at z₀; detector calibrated at each distance. 200000 frames per point.'},
  pilots:{x:'n_cal_per_mode',label:'Pilot symbols per mode',fig:'Fig. 10',context:'Training and data SNR = 5 dB; 6 calibration repeats with 50000 data frames each.'},
  hardware:{x:'hardware_phase_std_deg',label:'Phase-error standard deviation (°)',fig:'Fig. 13 source sweep',context:'Nominal detector under amplitude and phase errors; 2 hardware realizations with 8000 data frames each. SNR and error grids are discrete.'}
};
async function initPerformance(){
  const canvas=$('performance-canvas');let records=[],curves=[],xs=[],chosen=0,active='snr',request=0,plot=null;
  [0,.25,.5,1,1.5,2,3].forEach(n=>$('amp-error').append(option(n,fmt(n))));[-5,0,3,6,9,12,15,20].forEach(n=>$('hw-snr').append(option(n,fmt(n))));$('hw-snr').value=9;$('amp-error').value=.5;
  async function update(){const token=++request;active=$('experiment').value;$('hardware-controls').hidden=active!=='hardware';const rows=await data(active);if(token!==request)return;records=rows;filter();}
  function filter(){const e=EXP[active];let rr=records.filter(r=>r.active_set_id===$('task').value);if(active==='hardware')rr=rr.filter(r=>r.error_family===$('error-family').value&&r.hardware_amp_std_db===+$('amp-error').value&&r.snr_db===+$('hw-snr').value);
    xs=[...new Set(rr.map(r=>r[e.x]))].sort((a,b)=>a-b);curves=OBS.map(obs=>rr.filter(r=>r.observation_mode===obs).sort((a,b)=>a[e.x]-b[e.x]));chosen=Math.min(Math.floor(xs.length/2),xs.length-1);$('point-index').max=xs.length-1;$('point-index').value=chosen;$('point-axis-label').textContent=e.label;$('experiment-context').textContent=e.context;$('performance-source').textContent=`${e.fig} · ${rr.length} evaluated rows`;$('csv-download').href=`data/${active}.csv`;draw();readout();
  }
  function draw(){if(!xs.length)return;const {c,w,h}=setupCanvas(canvas,w=>w<500?320:380);const l=56,r=16,t=22,b=55,pw=w-l-r,ph=h-t-b,e=EXP[active];const logX=active==='pilots',tx=x=>logX?Math.log2(x):x,min=tx(xs[0]),max=tx(xs.at(-1)),xx=x=>l+(tx(x)-min)/(max-min||1)*pw,yy=y=>t+(-Math.log10(Math.max(1e-6,y)))/6*ph;plot={xx,yy,l,r,t,b,w,h};
    for(let power=0;power<=6;power++){const y=yy(10**-power);line(c,l,y,w-r,y,'#e3e8ef');text(c,power===0?'1':`10${['','⁻¹','⁻²','⁻³','⁻⁴','⁻⁵','⁻⁶'][power]}`,l-10,y,'right',undefined,12);}
    const step=Math.ceil((xs.length-1)/(w<500?3:6));xs.forEach((x,i)=>{if(i%step===0||i===xs.length-1){const px=xx(x);text(c,fmt(x,3),px,h-b+19,'center',undefined,12);}});
    text(c,e.label,l+pw/2,h-12,'center','#202b38',13);text(c,'BER',l,t-13,'left','#202b38',12);
    line(c,xx(xs[chosen]),t,xx(xs[chosen]),h-b,'#6e8fb8',1,[4,4]);
    curves.forEach((rows,k)=>{c.beginPath();c.strokeStyle=COLORS[k];c.lineWidth=2;c.setLineDash(k===0?[5,4]:k===1?[2,3]:[]);rows.forEach((row,i)=>{const x=xx(row[e.x]),y=yy(row.BER);if(i===0)c.moveTo(x,y);else c.lineTo(x,y);});c.stroke();c.setLineDash([]);rows.forEach((row,i)=>{const x=xx(row[e.x]),y=yy(row.BER),rad=i===chosen?5:3;if(row.BER===0){c.beginPath();c.moveTo(x-5,y-4);c.lineTo(x+5,y-4);c.lineTo(x,y+4);c.closePath();c.fillStyle=COLORS[k];c.fill();}else circle(c,x,y,rad,'#fff',COLORS[k],i===chosen?2:1.3);});});
  }
  function readout(){if(!xs.length)return;$('point-value').textContent=fmt(xs[chosen]);$('performance-readouts').innerHTML=curves.map((rr,k)=>{const r=rr[chosen],errors=r.bit_errors??r.n_bit_errors,total=r.bit_total??r.n_data_frames_per_repeat*(r.active_set_id==='two_stream_pm1'?2:4),repeats=r.n_cal_repeats??r.n_error_repeats;const count=repeats?`Mean of ${repeats} runs · ${num(total)} bits/run`:`${num(errors)} bit errors / ${num(total)} bits`;return `<div class="ber-readout ${CLASSES[k]}"><span>${LABELS[k]}</span><strong>${fmt(r.BER,5)}</strong><small>${count}${active==='pilots'?`<br>Channel error (Frobenius): ${fmt(r.relative_channel_error_fro,4)}`:''}</small></div>`;}).join('');}
  $('experiment').onchange=()=>update().catch(console.error);['task','error-family','amp-error','hw-snr'].forEach(id=>$(id).onchange=filter);$('point-index').oninput=e=>{chosen=+e.target.value;draw();readout();};
  canvas.onclick=e=>{if(!plot)return;const p=pointer(canvas,e);chosen=xs.map(x=>Math.abs(plot.xx(x)-p.x)).reduce((best,v,i,a)=>v<a[best]?i:best,0);$('point-index').value=chosen;draw();readout();};observeSize(canvas,draw);await update();
}

async function loadImage(src){return new Promise((resolve,reject)=>{const im=new Image();im.onload=()=>resolve(im);im.onerror=reject;im.src=src;});}
async function initPayload(){
  const metrics=await data('payload_metrics'),keys=['original',...OBS];const images=await Promise.all(keys.map(k=>loadImage(`assets/payload-${k}.png`)));const masks=await Promise.all(OBS.map(k=>loadImage(`assets/errors-${k}.png`)));const cards=[];let progress=196608,x=512,y=360,playing=false,last=0,visible=true;
  keys.forEach((k,i)=>{const d=document.createElement('div');d.className='payload-card';d.innerHTML=`<h3 class="${i?CLASSES[i-1]:''}">${i?LABELS[i-1]:'Original payload'}</h3><p class="metric">${i?`BER ${fmt(+metrics[i-1].BER,5)}`:'786432 source bits'}</p><canvas aria-label="${i?LABELS[i-1]:'Original'} image, point to choose a magnified region"></canvas><p class="zoom-label">SHARED MAGNIFIER</p><canvas aria-label="Magnified ${i?LABELS[i-1]:'original'} pixels"></canvas>`;$('payload-grid').append(d);const [main,zoom]=d.querySelectorAll('canvas');cards.push({main,zoom});
    const move=e=>{const p=pointer(main,e);x=Math.max(64,Math.min(960,p.x/main.clientWidth*1024));y=Math.max(48,Math.min(720,p.y/main.clientHeight*768));$('zoom-x').value=x;$('zoom-y').value=y;draw();};main.onpointermove=e=>{if(e.pointerType!=='touch'||e.buttons)move(e);};main.onclick=move;observeSize(main,draw);
  });
  function clipProgress(c,w,h,bits){const row=Math.floor(bits/1024),extra=bits%1024;c.beginPath();c.rect(0,0,w,Math.min(h,row/768*h));if(row<768)c.rect(0,row/768*h,extra/1024*w,h/768);c.clip();}
  function draw(){cards.forEach(({main,zoom},i)=>{let {c,w,h}=setupCanvas(main,w=>w*.75);c.fillStyle='#e7edf4';c.fillRect(0,0,w,h);c.save();if(i)clipProgress(c,w,h,Math.floor(progress)*4);c.drawImage(images[i],0,0,w,h);if(i&&$('error-mask').checked)c.drawImage(masks[i-1],0,0,w,h);c.restore();c.strokeStyle='#194cac';c.lineWidth=1.5;c.strokeRect((x-64)/1024*w,(y-48)/768*h,128/1024*w,96/768*h);
      const z=setupCanvas(zoom,w=>w*.75);z.c.imageSmoothingEnabled=false;z.c.drawImage(images[i],Math.round(x-64),Math.round(y-48),128,96,0,0,z.w,z.h);if(i&&$('error-mask').checked)z.c.drawImage(masks[i-1],Math.round(x-64),Math.round(y-48),128,96,0,0,z.w,z.h);
      // The zoom follows the same partial-decoding state as the overview.
      if(i&&progress<196608){const bits=Math.floor(progress)*4,row=Math.floor(bits/1024),extra=bits%1024,boundary=(row-Math.round(y-48))/96*z.h,rowH=z.h/96;z.c.fillStyle='#e7edf4';if(boundary<0)z.c.fillRect(0,0,z.w,z.h);else if(boundary<z.h){const start=Math.max(0,Math.min(z.w,(extra-Math.round(x-64))/128*z.w));z.c.fillRect(start,boundary,z.w-start,rowH);z.c.fillRect(0,boundary+rowH,z.w,z.h-boundary-rowH);}}
    });$('payload-count').textContent=`${num(Math.round(progress))} / 196608`;}
  function setPlaying(v){playing=v;last=0;$('payload-play').textContent=v?'Pause decoding':'Replay decoding';}
  $('payload-play').onclick=()=>{if(!playing&&progress>=196608)progress=0;setPlaying(!playing);draw();};$('payload-progress').oninput=e=>{progress=+e.target.value;setPlaying(false);draw();};$('error-mask').onchange=draw;['x','y'].forEach(a=>$(`zoom-${a}`).oninput=e=>{if(a==='x')x=+e.target.value;else y=+e.target.value;draw();});
  new IntersectionObserver(entries=>{visible=entries[0].isIntersecting;last=0;}).observe($('payload-grid'));reduced.addEventListener('change',()=>{if(reduced.matches)setPlaying(false);});
  function tick(t){if(playing&&!document.hidden&&visible){if(last){progress=Math.min(196608,progress+(t-last)/20000*196608);$('payload-progress').value=Math.round(progress);draw();if(progress>=196608)setPlaying(false);}last=t;}else last=0;requestAnimationFrame(tick);}draw();requestAnimationFrame(tick);
}

async function initGallery(){const gallery=await data('gallery');for(const f of gallery){const d=document.createElement('div');d.className='gallery-item';const b=document.createElement('button');b.type='button';b.setAttribute('aria-label',`Open Figure ${f.id}: ${f.title}`);const im=document.createElement('img');im.src=f.image;im.alt=`Figure ${f.id}: ${f.title}`;im.loading='lazy';im.width=600;im.height=400;b.append(im);const p=document.createElement('p');p.innerHTML=`<span>FIGURE ${f.id}</span>${f.title}`;d.append(b,p);$('gallery-grid').append(d);b.onclick=()=>{$('dialog-title').textContent=`Figure ${f.id} · ${f.title}`;$('dialog-image').src=f.image;$('dialog-image').alt=im.alt;$('figure-original').href=f.image;$('figure-dialog').showModal();};}
  $('dialog-close').onclick=()=>$('figure-dialog').close();$('figure-dialog').onclick=e=>{if(e.target===$('figure-dialog')){const r=e.target.getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)e.target.close();}};
}

// Explicit English controls also make playback accessible outside browser-native controls.
document.querySelectorAll('.film-grid figure').forEach((figure,i)=>{
  const video=figure.querySelector('video'),button=document.createElement('button');
  button.type='button';button.className='film-play';button.textContent='Play video';
  button.setAttribute('aria-label',i===0?'Play field-cycle video':'Play recovery video');
  figure.querySelector('figcaption').prepend(button);
  const sync=()=>{button.textContent=video.paused?'Play video':'Pause video';button.setAttribute('aria-pressed',String(!video.paused));};
  video.addEventListener('play',sync);video.addEventListener('pause',sync);video.addEventListener('ended',sync);
  button.onclick=async()=>{if(video.paused){try{await video.play();}catch(error){button.textContent='Use the MP4 download below';console.error(error);}}else video.pause();};
});

await Promise.allSettled([guard('field',initField),guard('reception',initReceiver),guard('geometry',initGeometry),guard('performance',initPerformance),guard('payload',initPayload),guard('figures',initGallery)]);
document.documentElement.dataset.ready='true';
