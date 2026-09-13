"""Render the website's two MP4 clips, README overview and GIF from public data.

python -m pip install -r tools/requirements-site.txt
python tools/export_media.py
"""
from pathlib import Path
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import imageio_ffmpeg

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/assets'
DATA=ROOT/'docs/data'
INK='#202b38'; MUTED='#596879'; BLUE='#194cac'
COLORS=['#536f83','#9b7115','#7653a7']
OBS=['pressure_only','pressure_plus_vx_vy','pressure_plus_vx_vy_vz']


def font(size, bold=False):
    # Resolve a TrueType font on Windows, Linux or macOS.
    candidates=[Path('C:/Windows/Fonts')/('segoeuib.ttf' if bold else 'segoeui.ttf'),
        Path('/usr/share/fonts/truetype/dejavu')/('DejaVuSans-Bold.ttf' if bold else 'DejaVuSans.ttf'),
        Path('/System/Library/Fonts/Supplemental/Arial.ttf')]
    for p in candidates:
        if p.exists():return ImageFont.truetype(str(p),size)
    return ImageFont.load_default(size=size)


def label(draw, xy, s, size=20, fill=INK, bold=False):
    draw.text(xy,s,font=font(size,bold),fill=fill)


z=np.load(DATA/'field_samples.npz')
p=z['ell_2_p']/z['ell_2_p_scale']
vx=z['ell_2_vtx']/z['ell_2_vxy_scale'];vy=z['ell_2_vty']/z['ell_2_vxy_scale']


def field_tile(phi, size=384):
    co,si=math.cos(phi),math.sin(phi)
    value=np.clip(p.real*co+p.imag*si,-1,1)
    mag=np.abs(value)[...,None]
    cols=np.where((value>=0)[...,None],[190,52,56],[43,90,163])
    rgb=(np.array([248,249,251])+(cols-np.array([248,249,251]))*mag).astype('uint8')
    im=Image.fromarray(rgb[::-1]).resize((size,size),Image.Resampling.BILINEAR)
    d=ImageDraw.Draw(im)
    for j in range(8,101,8):
        for i in range(8,101,8):
            dx=vx[j,i].real*co+vx[j,i].imag*si;dy=-(vy[j,i].real*co+vy[j,i].imag*si)
            length=math.hypot(dx,dy)
            if length<.035:continue
            dx*=size*.017/max(1,length);dy*=size*.017/max(1,length)
            x=i/100*size;y=(100-j)/100*size;a=math.atan2(dy,dx)
            d.line((x-dx/2,y-dy/2,x+dx/2,y+dy/2),fill='#294257',width=1)
            ex,ey=x+dx/2,y+dy/2
            for s in [-1,1]:d.line((ex,ey,ex-3*math.cos(a+s*.55),ey-3*math.sin(a+s*.55)),fill='#294257',width=1)
    return im


def field_frame(phi):
    im=Image.new('RGB',(960,540),'#f8f9fb');d=ImageDraw.Draw(im)
    label(d,(35,20),'AVS–OAM  /  THE SOUND FIELD',15,BLUE,True)
    tile=field_tile(phi);im.paste(tile,(65,77))
    for val,px in [('-40',65),('0',257),('40',449)]:label(d,(px-12,468),val,15,MUTED)
    label(d,(230,496),'x (cm)',16,MUTED)
    for val,py in [('40',77),('0',269),('-40',461)]:label(d,(23,py-10),val,15,MUTED)
    label(d,(16,51),'y (cm)',15,MUTED)
    label(d,(510,78),'One acoustic cycle.',34,INK,True)
    label(d,(510,132),'OAM mode ℓ = 2',23)
    label(d,(510,179),'Color: instantaneous pressure\nArrows: transverse particle velocity',19,MUTED)
    label(d,(510,259),'Re[p exp(−iωt)]',24,BLUE)
    label(d,(510,303),f'Phase  {round(phi/(2*math.pi)*360)%360}°',22)
    d.rounded_rectangle((510,353,903,361),radius=4,fill='#d9e0e7')
    d.rounded_rectangle((510,353,510+max(1,393*phi/(2*math.pi)),361),radius=4,fill=BLUE)
    label(d,(510,395),'3430 Hz carrier · z = 1.2 m\nSlow display playback · normalized fields',17,MUTED)
    label(d,(510,464),'Source: manuscript Fig. 2 complex arrays',15,MUTED)
    return im


payload=np.load(DATA/'payload.npz')
images=[Image.fromarray(payload[k].astype('uint8')*255).convert('RGB') for k in ['original']+OBS]


def recovery_frame(fraction):
    im=Image.new('RGB',(960,540),'#f8f9fb');d=ImageDraw.Draw(im)
    label(d,(30,20),'AVS–OAM  /  RECORDED IMAGE RECOVERY',15,BLUE,True)
    label(d,(30,55),'From the same payload to three reconstructions.',29,INK,True)
    label(d,(30,102),'S₄ · K = 6 · gap = 90° · SNR = 3 dB · calibrated geometry',17,MUTED)
    uses=round(fraction*196608)
    for i,(pic,title) in enumerate(zip(images,['Original','Pressure only','Transverse AVS','Full AVS'])):
        x=30+i*232; label(d,(x,158),title,20,INK if i==0 else COLORS[i-1],True)
        preview=pic.resize((204,153),Image.Resampling.LANCZOS)
        if i and fraction<1:
            blank=Image.new('RGB',(204,153),'#e7edf4');h=round(fraction*153)
            blank.paste(preview.crop((0,0,204,h)),(0,0));preview=blank
        im.paste(preview,(x,197));d.rectangle((x,197,x+204,350),outline='#b9c5d4')
        s=['786432 source bits','BER = 0.024217','BER = 0.01637','BER = 0.0022151'][i]
        label(d,(x,368),s,16,MUTED)
    label(d,(30,417),f'Decoded channel uses  {uses:,} / 196608',21)
    d.rounded_rectangle((30,458,930,466),radius=4,fill='#d9e0e7')
    d.rounded_rectangle((30,458,30+max(1,900*fraction),466),radius=4,fill=BLUE)
    label(d,(30,495),'Source: Fig. 14 reconstruction arrays · row-major symbol replay · no measured data rate implied',15,MUTED)
    return im


def movie(name,frame,n=144,fps=12):
    writer=imageio_ffmpeg.write_frames(str(OUT/name),(960,540),fps=fps,codec='libx264',
        pix_fmt_in='rgb24',pix_fmt_out='yuv420p',quality=7,macro_block_size=2,
        output_params=['-movflags','+faststart'],ffmpeg_log_level='error')
    writer.send(None)
    try:
        for i in range(n):writer.send(np.asarray(frame(i,n)))
    finally:writer.close()


def overview():
    im=Image.new('RGB',(1400,530),'#f8f9fb');d=ImageDraw.Draw(im)
    label(d,(40,24),'AVS–OAM',27,BLUE,True);label(d,(245,28),'Sound, with direction.',27,INK)
    for x,title in [(40,'01  SOUND FIELD'),(500,'02  CO-LOCATED OBSERVATIONS'),(980,'03  RECOVERED INFORMATION')]:label(d,(x,94),title,17,BLUE,True)
    im.paste(field_tile(0,300),(40,140));label(d,(40,455),'Pressure + transverse velocity · ℓ = 2',16,MUTED)
    d.ellipse((512,221,582,291),outline=BLUE,width=4);label(d,(526,240),'AVS',17,BLUE,True)
    for j,component in enumerate(['p','ṽₓ','ṽᵧ','ṽz']):
        y=153+j*70;d.line((582,256,680,y+19),fill='#a9b9d0',width=2)
        d.rounded_rectangle((680,y,875,y+44),radius=5,fill='#e8eef8',outline='#bbcae0');label(d,(707,y+8),component,21,BLUE,True)
    label(d,(500,455),'One position. Four sensing channels.',16,MUTED)
    im.paste(images[3].resize((370,278)),(980,153));label(d,(980,455),'Full AVS · source reconstruction, Fig. 14',16,MUTED)
    im.save(OUT/'overview.png',optimize=True)


if __name__=='__main__':
    OUT.mkdir(parents=True,exist_ok=True)
    movie('field-cycle.mp4',lambda i,n:field_frame(i/n*2*math.pi))
    movie('recovery.mp4',lambda i,n:recovery_frame(min(1,i/(n-25))),n=240)
    field_frame(0).save(OUT/'field-poster.jpg',quality=92)
    recovery_frame(1).save(OUT/'recovery-poster.jpg',quality=92)
    frames=[field_tile(i/36*2*math.pi,300).quantize(colors=96) for i in range(36)]
    frames[0].save(OUT/'field-preview.gif',save_all=True,append_images=frames[1:],duration=120,loop=0,optimize=True)
    overview()
    print('Two MP4 clips, posters, README overview and GIF exported from public source arrays.')
