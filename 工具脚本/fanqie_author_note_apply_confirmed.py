#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fanqie author note apply with real update confirmation.
One-by-one safe mode. Requires agent-browser session fanqie.
"""
from __future__ import annotations
import argparse, json, re, subprocess, time
from datetime import datetime
from pathlib import Path

PROJECT = Path('/root/workspace/科武纪元')
NOTES = PROJECT/'审核记录/作者有话说_已投稿1-72_现实科学引用整理.md'
URLMAP = PROJECT/'审核记录/fanqie_chapter_url_map_20260507.json'
OUTDIR = PROJECT/'审核记录/作者有话说录入记录/confirmed_update'
OUTDIR.mkdir(parents=True, exist_ok=True)


def ab(args: list[str], timeout=120) -> str:
    p = subprocess.run(['agent-browser','--session-name','fanqie','--cdp','9223',*args], text=True, capture_output=True, timeout=timeout)
    out = (p.stdout+p.stderr).strip()
    return out


def js(code: str, timeout=120):
    out = ab(['eval', code], timeout=timeout)
    try:
        return json.loads(out)
    except Exception:
        return out


def parse_notes() -> dict[int,str]:
    text = NOTES.read_text(encoding='utf-8')
    pat = re.compile(r'^### 第(\d+)章[^\n]*\n\n(.*?)\n\n字数：(\d+)', re.M|re.S)
    return {int(ch): note.strip() for ch,note,_ in pat.findall(text)}


def get_urlmap() -> dict[int,str]:
    m = json.loads(URLMAP.read_text(encoding='utf-8'))
    m.setdefault('71','https://fanqienovel.com/main/writer/7628216044850531352/publish/7637014147435086398/?enter_from=modifychapter')
    m.setdefault('72','https://fanqienovel.com/main/writer/7628216044850531352/publish/7637014558644650558/?enter_from=modifychapter')
    return {int(k): v for k,v in m.items()}


def state():
    return js(r"""
(()=>{
 const author=document.querySelector('.author-speak');
 const editor=document.querySelector('.author-speak .tiptap.ProseMirror');
 const buttons=[...document.querySelectorAll('button')].map((b,i)=>({
   i,text:b.innerText,disabled:b.disabled,cls:String(b.className),visible:!!(b.offsetWidth||b.offsetHeight)
 }));
 return {
   url:location.href,
   title:document.title,
   hasEmpty:!!document.querySelector('.author-speak-empty'),
   hasAuthor:!!author,
   authorText:author?.innerText || '',
   note:editor?.innerText?.trim() || '',
   bodyTail:document.body.innerText.slice(-1000),
   visibleButtons:buttons.filter(b=>b.visible).slice(0,30)
 };
})()
""")


def click_continue():
    return js(r"""
(()=>{const b=[...document.querySelectorAll('button')].find(b=>b.innerText.includes('继续编辑') && !b.disabled); if(b){b.click(); return true;} return false;})()
""")


def open_author_if_empty() -> bool:
    js("document.querySelector('.author-speak-guide-close')?.click(); true")
    time.sleep(0.3)
    # click add button / tooltip item robustly
    clicked = js(r"""
(()=>{
 const add=document.querySelector('.author-speak-empty-btn') || [...document.querySelectorAll('button,div,span')].find(e=>e.innerText?.trim()==='添加');
 if(add){add.scrollIntoView({block:'center'}); add.click(); return 'clicked_add';}
 return 'no_add';
})()
""")
    time.sleep(0.8)
    click_continue(); time.sleep(0.5)
    if isinstance(state(), dict) and state().get('hasAuthor'):
        return True
    clicked2 = js(r"""
(()=>{
 const item=[...document.querySelectorAll('.author-speak-type-selector-item,button,div,span')].find(e=>e.innerText?.includes('添加图文'));
 if(item){item.click(); return true;}
 return false;
})()
""")
    time.sleep(1.0)
    click_continue(); time.sleep(0.5)
    return isinstance(state(), dict) and state().get('hasAuthor')


def set_note(note: str):
    payload = json.dumps(note, ensure_ascii=False)
    return js(rf"""
(()=>{{
 const note={payload};
 const el=document.querySelector('.author-speak .tiptap.ProseMirror');
 if(!el) return {{ok:false, reason:'no_editor'}};
 el.focus();
 document.execCommand('selectAll', false, null);
 document.execCommand('insertText', false, note);
 el.dispatchEvent(new InputEvent('input',{{bubbles:true,inputType:'insertText',data:note}}));
 return {{ok:true, text:el.innerText.trim(), stat:document.querySelector('.author-speak-footer-stat')?.innerText || ''}};
}})()
""")


def click_author_save_then_update():
    out = {'save_click': None, 'update_click': None, 'after_save': None, 'after_update': None}
    out['save_click'] = js(r"""
(()=>{
 const scope=document.querySelector('.author-speak') || document;
 const btn=[...scope.querySelectorAll('button')].find(b=>b.innerText.trim()==='保存' && !b.disabled)
        || [...document.querySelectorAll('button')].find(b=>b.innerText.trim()==='保存' && !b.disabled && (b.offsetWidth||b.offsetHeight));
 if(!btn) return 'no_save_button';
 btn.click(); return 'clicked_save';
})()
""")
    time.sleep(1.5)
    out['after_save'] = state()
    out['update_click'] = js(r"""
(()=>{
 const btn=[...document.querySelectorAll('button')].find(b=>b.innerText.trim()==='更新' && !b.disabled && (b.offsetWidth||b.offsetHeight));
 if(!btn) return 'no_update_button';
 btn.click(); return 'clicked_update';
})()
""")
    time.sleep(5.0)
    out['after_update'] = state()
    return out


def process(ch:int, url:str, note:str):
    rec={'chapter':ch,'url':url,'target_note':note,'time':datetime.now().isoformat(timespec='seconds'),'steps':[]}
    ab(['navigate', url], timeout=160)
    ab(['wait','4000'], timeout=20)
    click_continue(); time.sleep(1.0)
    st=state(); rec['steps'].append({'after_open':st})

    if isinstance(st,dict) and '审核中' in st.get('authorText','') and note in st.get('authorText',''):
        rec['status']='ok_already_auditing'
        rec['final_state']=st
        return rec

    if isinstance(st,dict) and st.get('hasEmpty'):
        ok=open_author_if_empty(); rec['steps'].append({'open_author':ok,'state':state()})
    st=state()
    if not (isinstance(st,dict) and st.get('hasAuthor')):
        rec['status']='failed_no_author_module'; rec['final_state']=st; return rec

    # If readonly existing block has 编辑 button enabled, click it.
    if '编辑' in st.get('authorText','') and not document_editable_hint(st):
        js(r"""(()=>{const b=[...document.querySelectorAll('button')].find(b=>b.innerText.trim()==='编辑' && !b.disabled && (b.offsetWidth||b.offsetHeight)); if(b){b.click(); return true;} return false;})()""")
        time.sleep(1.2)

    rec['steps'].append({'set_note':set_note(note)})
    rec['steps'].append({'save_update':click_author_save_then_update()})
    st=state(); rec['final_state']=st
    if isinstance(st,dict) and ('审核中' in st.get('authorText','')) and note in st.get('authorText',''):
        rec['status']='ok_submitted_auditing'
    else:
        rec['status']='failed_not_auditing_after_update'
    return rec


def document_editable_hint(st:dict) -> bool:
    return bool(st.get('note')) or '退出保存' in st.get('authorText','') or '图片' in st.get('authorText','')


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--chapter', type=int, required=True)
    args=ap.parse_args()
    notes=parse_notes(); urls=get_urlmap()
    ch=args.chapter
    if ch not in notes or ch not in urls:
        raise SystemExit(f'missing note/url for chapter {ch}: note={ch in notes} url={ch in urls}')
    rec=process(ch, urls[ch], notes[ch])
    out=OUTDIR/f'chapter_{ch:03d}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    out.write_text(json.dumps(rec,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'chapter':ch,'status':rec.get('status'),'out':str(out),'authorText':rec.get('final_state',{}).get('authorText','')[:200]},ensure_ascii=False,indent=2))

if __name__=='__main__':
    main()
