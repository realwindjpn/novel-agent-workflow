#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Apply/read back Fanqie author notes for known chapter edit URLs.
Uses agent-browser named session fanqie. Conservative: only touches author-speak block.
"""
from __future__ import annotations
import json, re, subprocess, time
from pathlib import Path

PROJECT = Path('/root/workspace/科武纪元')
NOTES = PROJECT/'审核记录/作者有话说_已投稿1-72_现实科学引用整理.md'
URLMAP = PROJECT/'审核记录/fanqie_chapter_url_map_20260507.json'
OUTDIR = PROJECT/'审核记录/作者有话说录入记录'
OUTDIR.mkdir(parents=True, exist_ok=True)


def run(cmd: str, timeout=90) -> str:
    p = subprocess.run(cmd, shell=True, text=True, capture_output=True, timeout=timeout)
    if p.returncode != 0:
        return (p.stdout + p.stderr).strip()
    return p.stdout.strip()


def ab(cmd: str, timeout=90) -> str:
    return run(f"agent-browser --session-name fanqie --cdp 9223 {cmd}", timeout=timeout)


def js(s: str, timeout=90):
    # use stdin to avoid shell quoting mess
    p = subprocess.run(['agent-browser','--session-name','fanqie','--cdp','9223','eval',s], text=True, capture_output=True, timeout=timeout)
    out=(p.stdout+p.stderr).strip()
    try:
        return json.loads(out)
    except Exception:
        return out


def parse_notes():
    text = NOTES.read_text(encoding='utf-8')
    pat = re.compile(r'^### 第(\d+)章[^\n]*\n\n(.*?)\n\n字数：(\d+)', re.M|re.S)
    return {int(ch): note.strip() for ch,note,_ in pat.findall(text)}


def get_urlmap():
    m=json.loads(URLMAP.read_text(encoding='utf-8'))
    # patched from 2026-05-07 live chapter-management page
    m.setdefault('71','https://fanqienovel.com/main/writer/7628216044850531352/publish/7637014147435086398/?enter_from=modifychapter')
    m.setdefault('72','https://fanqienovel.com/main/writer/7628216044850531352/publish/7637014558644650558/?enter_from=modifychapter')
    return {int(k):v for k,v in m.items()}


def page_state():
    return js(r"""
(()=>{
 const cont=[...document.querySelectorAll('button')].find(b=>b.innerText.includes('继续编辑'));
 return {
  url: location.href,
  hasContinue: !!cont,
  hasEmpty: !!document.querySelector('.author-speak-empty'),
  hasAuthor: !!document.querySelector('.author-speak'),
  note: document.querySelector('.author-speak .tiptap.ProseMirror')?.innerText || '',
  status: document.querySelector('.publish-maintain-info-status')?.innerText || '',
  nextDisabled: document.querySelector('.auto-editor-next')?.disabled ?? null,
  textTail: document.body.innerText.slice(-500)
 };
})()
""")


def click_continue_if_any():
    return js(r"""
(()=>{const b=[...document.querySelectorAll('button')].find(b=>b.innerText.includes('继续编辑')); if(b){b.click(); return true;} return false;})()
""")


def open_author_speak_if_empty():
    # Close guide if present, click add, click 添加图文 in tooltip.
    js("document.querySelector('.author-speak-guide-close')?.click(); 'ok'")
    time.sleep(0.2)
    # Native mouse/hover is more reliable for tooltip creation
    ab("eval \"document.querySelector('.author-speak-empty-btn')?.scrollIntoView({block:'center'}); 'ok'\"", timeout=30)
    time.sleep(0.2)
    ab("mouse move 900 493", timeout=30)
    ab("mouse down", timeout=30); ab("mouse up", timeout=30)
    time.sleep(0.8)
    # Handle stale modal if clicking add triggered it
    click_continue_if_any(); time.sleep(0.8)
    st=page_state()
    if isinstance(st,dict) and st.get('hasAuthor'):
        return True
    # Try tooltip item by JS, then by approximate coordinate
    clicked=js(r"""
(()=>{const item=[...document.querySelectorAll('.author-speak-type-selector-item')].find(e=>e.innerText.includes('添加图文')); if(item){item.click(); return true;} return false;})()
""")
    if not clicked:
        ab("mouse move 888 407", timeout=30); ab("mouse down", timeout=30); ab("mouse up", timeout=30)
    time.sleep(1.2)
    click_continue_if_any(); time.sleep(0.5)
    st=page_state()
    return isinstance(st,dict) and st.get('hasAuthor')


def set_note(note: str):
    payload=json.dumps(note, ensure_ascii=False)
    return js(rf"""
(()=>{{
 const note={payload};
 const el=document.querySelector('.author-speak .tiptap.ProseMirror');
 if(!el) return {{ok:false, reason:'no editor'}};
 el.focus();
 document.execCommand('selectAll', false, null);
 document.execCommand('insertText', false, note);
 el.dispatchEvent(new InputEvent('input',{{bubbles:true,inputType:'insertText',data:note}}));
 return {{ok:true, text:el.innerText, stat:document.querySelector('.author-speak-footer-stat')?.innerText}};
}})()
""")


def save_note():
    js("document.querySelector('.author-speak-title-btn button')?.click(); 'clicked'")
    time.sleep(2.5)
    return page_state()


def process(ch:int, url:str, note:str):
    rec={'chapter':ch,'url':url,'target_note':note,'steps':[]}
    ab(f"navigate '{url}'", timeout=120)
    ab("wait 4000", timeout=20)
    st=page_state(); rec['steps'].append({'after_open':st})
    click_continue_if_any(); time.sleep(1.0)
    st=page_state(); rec['steps'].append({'after_continue':st})
    if isinstance(st,dict) and st.get('note','').strip()==note:
        rec['status']='ok_verified_existing'
        return rec
    if isinstance(st,dict) and st.get('hasEmpty'):
        ok=open_author_speak_if_empty(); rec['steps'].append({'open_author_speak':ok,'state':page_state()})
    st=page_state()
    if not (isinstance(st,dict) and st.get('hasAuthor')):
        rec['status']='failed_no_author_editor'; rec['final_state']=st; return rec
    res=set_note(note); rec['steps'].append({'set_note':res})
    st=save_note(); rec['steps'].append({'after_save':st})
    # Reopen and read back; must click continue edit if stale modal appears
    ab(f"navigate '{url}'", timeout=120); ab("wait 4000", timeout=20)
    click_continue_if_any(); time.sleep(1.0)
    st=page_state(); rec['readback']=st
    if isinstance(st,dict) and st.get('note','').strip()==note:
        rec['status']='ok_verified_readback'
    else:
        rec['status']='save_unverified'
    return rec


def main():
    import argparse
    ap=argparse.ArgumentParser()
    ap.add_argument('--chapters', default='67')
    args=ap.parse_args()
    notes=parse_notes(); urls=get_urlmap()
    chapters=[]
    for part in args.chapters.split(','):
        part=part.strip()
        if '-' in part:
            a,b=map(int,part.split('-',1)); chapters.extend(range(a,b+1))
        elif part:
            chapters.append(int(part))
    results=[]
    for ch in chapters:
        if ch not in notes or ch not in urls:
            results.append({'chapter':ch,'status':'missing_note_or_url','has_note':ch in notes,'has_url':ch in urls})
            continue
        results.append(process(ch, urls[ch], notes[ch]))
        out=OUTDIR/f'番茄作者有话说_known_{args.chapters.replace(",","_")}_live.json'
        out.write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
        print(json.dumps(results[-1],ensure_ascii=False)[:1000], flush=True)
    print('OUT', out)

if __name__=='__main__': main()
