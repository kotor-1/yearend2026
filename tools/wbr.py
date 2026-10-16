"""index.html の本文に、文節の切れ目ごとに <wbr> を入れる（BudouX）。
CSS の word-break:keep-all と組み合わせて、日本語が単語の途中で改行されないようにする。
本文を書きかえたら `python3 tools/wbr.py` を実行する（何度実行しても同じ結果になる）。
"""
import re, sys, pathlib
import budoux

INLINE = {'b', 'small', 'span', 'a', 'i', 'em', 'strong', 'mark'}
TOKEN = re.compile(r'(<!--.*?-->|<[^>]+>)', re.S)
parser = budoux.load_default_japanese_parser()


def tag_name(t):
    m = re.match(r'</?\s*([a-zA-Z0-9]+)', t)
    return m.group(1).lower() if m else ''


OPEN = '「（『【〈《“(['
CLOSE = '」）』】〉》”)]、。，．・！？!?：:'
WEEKDAY = re.compile(r'（[日月火水木金土]）')


def ok_cut(text, c):
    """文節の切れ目でも、改行するとおかしくなる所には入れない"""
    prev, nxt = text[c - 1], text[c]
    if prev.isspace() or nxt.isspace():
        return False          # 空白はもともと改行できる
    if prev in OPEN or nxt in CLOSE:
        return False          # 「（」の直後・「）、。」の直前
    if WEEKDAY.match(text, c):
        return False          # 12月27日（日） を離さない
    return True


def flush(run, out):
    """インラインのまとまり（文字とインラインタグ）を文節で区切って出力する"""
    text = ''.join(x for kind, x in run if kind == 't')
    if not text.strip() or not re.search(r'[぀-ヿ一-鿿]', text):
        out.extend(x for _, x in run)
        return
    cuts, pos = set(), 0
    for ph in parser.parse(text)[:-1]:
        pos += len(ph)
        cuts.add(pos)
    cuts = {c for c in cuts if ok_cut(text, c)}
    pos = 0
    for kind, x in run:
        if kind == 'g':
            out.append(x)
            continue
        buf = []
        for ch in x:
            if pos in cuts and pos > 0:
                buf.append('<wbr>')
            buf.append(ch)
            pos += 1
        out.append(''.join(buf))


def process(html):
    html = html.replace('<wbr>', '')
    head, sep, rest = html.partition('<body>')
    body, sep2, tail = rest.partition('<script>')
    out, run = [], []
    for part in TOKEN.split(body):
        if not part:
            continue
        if part.startswith('<'):
            if tag_name(part) in INLINE:
                run.append(('g', part))
            else:
                flush(run, out); run = []
                out.append(part)
        else:
            run.append(('t', part))
    flush(run, out)
    return head + sep + ''.join(out) + sep2 + tail


if __name__ == '__main__':
    p = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else 'index.html')
    p.write_text(process(p.read_text(encoding='utf-8')), encoding='utf-8')
    print('ok', p)
