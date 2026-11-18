"""Builds app/fx-catalog.json (all 51 effects of the `effects` skill, in Russian) and renders a 4 s preview of each
on a clip with a face. Skips previews that already exist. Writes the status of each render to the catalog.
Run: python tools/make-catalog.py   (sequential, ~1-2 min per effect)."""
import json, os, subprocess, sys, glob
ROOT = r'C:\src\content-studio'
HOME = os.path.expanduser('~')
PY = os.path.join(HOME, '.claude', 'skills', 'effects', '.venv', 'Scripts', 'python.exe')
FX = os.path.join(HOME, '.claude', 'skills', 'effects', 'scripts', 'fx.py')
D = os.path.join(ROOT, 'trials', 'reels', 'fx')
PREV = os.path.join(ROOT, 'app', 'previews')
CAT = os.path.join(ROOT, 'app', 'fx-catalog.json')
IMGS = os.path.join(D, 'imgs')
os.makedirs(PREV, exist_ok=True); os.makedirs(IMGS, exist_ok=True)

# id, русское имя, описание, нужен человек в кадре, картинки, аргументы превью
E = [
('noise','Лента роликов','Рилсы сыплются за головой, по одному каждые четверть секунды',1,1,[]),
('lineup','Нумерованные плитки','Плитки с номерами веером над головой',1,0,['--text','HOOK|STORY|PROOF|OFFER']),
('locked-on','Захват лица','Угловые рамки цепляются за лицо, камера ведёт',1,0,['--text','KOSTA']),
('orbit','Орбита роликов','Ролики кружат вокруг головы',1,1,[]),
('lean-in','Наезд на слово','Быстрый наезд камеры на одно слово',1,0,[]),
('backdrop-word','Слово за спиной','Огромное слово падает за человеком',1,0,['--text','DISCIPLINE']),
('spotlight','Прожектор','Гасит фон, человек остаётся в свете',1,0,['--text','FOCUS']),
('the-bill','Чек с инструкцией','Инструкция печатается как чек над головой',1,0,['--text','Fill the bottle|Set it by your shoes|Go']),
('moody','Цветокоррекция','Тёплый, холодный, ч/б, контрастный тон на весь ролик',0,0,['--opt','grade=warm']),
('swipe','До / после','Ползунок «до/после» проходит по кадру (для цвета, не для тела)',0,0,['--opt','grade=warm']),
('todo','Список дел','Список рядом с головой, пункты отмечаются по мере речи',1,0,['--text','Plan|Water|Move','--opt','ticks=1|2|3']),
('comment-box','Строка комментария','Печатает слово в комментарии (в заготовке чужой ник, правим перед работой)',1,0,['--text','SOCKS']),
('tap','Кнопка Follow','Follow нажимается и становится Following',0,0,['--opt','at=2.0','--opt','color=#C9AB7C']),
('pause-point','Стоп-кадр со стрелкой','Кадр замирает, рисованная стрелка показывает на человека',1,0,['--text','LOOK']),
('uninstall','Полоса удаления','Глючная полоса «удаление», кадр рассыпается',0,0,['--text','OLD HABITS']),
('reel-frame','Рамка рилса','Видео уменьшается до карточки рилса',0,0,['--text','kosta_method']),
('shortcut-rain','Дождь клавиш','Клавиши клавиатуры падают за спиной',1,0,['--text','⌘|K|Z|⏎']),
('reject-stamp','Штамп','Красная печать на слове',0,0,['--text','NOT MONDAY']),
('countdown-flip','Отсчёт 3-2-1','Перекидные цифры отсчёта',0,0,[]),
('rabbit-hole','Туннель','Кадр уходит сам в себя, для перехода',0,0,[]),
('cover-star','Обложка журнала','Человек становится обложкой, заголовок за головой',1,0,['--text','KOSTA']),
('scribble','Маркер','Рисованные стрелки и обводка',0,0,['--text',"DON'T SKIP"]),
('glass-widgets','Стеклянные виджеты','Матовые виджеты парят вокруг головы (в заготовке подписи автора, правим)',1,0,['--text','30','--opt','name=Kosta','--opt','handle=kosta_method']),
('red-collage','Красный коллаж','Ч/б человек, огромное красное слово позади, три строки',1,0,['--text','HABIT','--opt','lines=Small|Steps|Daily']),
('split-headline','Заголовок сверху','Карточка с заголовком сдвигает человека вниз',1,0,['--text','ONE SMALL HABIT|CHANGES EVERYTHING']),
('pastel-word','Пастельное слово','Сиреневая комната, слово за спиной, карточка профиля',1,0,['--text','CALM','--opt','name=Kosta','--opt','handle=kosta_method']),
('check-pills','Галочки-таблетки','Клетчатая комната, курсор нажимает синие таблетки',1,1,['--text','Water|Sleep|Steps']),
('timeline','Таймлайн монтажа','Тёмно-красный тон, таймлайн, REC и бегунок',0,0,['--text','KOSTA METHOD','--opt','sub=Day 1']),
('headline-box','Заголовок с наездом','Две строки, вторая в белой рамке',0,0,['--text','REST DAY|IS PART OF THE PLAN']),
('profile-wall','Стена профиля','Сетка роликов за спиной, счётчик растёт',1,1,[]),
('tier-list','Тир-лист','Падает тир-лист, нужный предмет летит в S',1,0,['--opt','title=HABITS','--opt','item=WATER']),
('broll-split','Б-ролл и человек','Сверху б-ролл с ценником, снизу человек',1,1,['--text','NEW']),
('phone-fan','Веер телефонов','Ролики веером как карты в руке',1,1,['--text','TOP 3|HABITS']),
('dot-reveal','Сборка из точек','Кадр собирается из светящихся точек',0,0,[]),
('headline-wall','Стена заголовков','Заголовки копятся за головой, затем итог',1,0,['--text','Move more::Day 1|Drink water::Day 2|Sleep early::Day 3','--opt','total=3 habits','--opt','label=TOTAL']),
('checklist','Чек-лист задач','Список под подбородком, шаги крутятся и зеленеют',1,0,['--text','Plan::done|Water::done|Move::done','--opt','title=TODAY']),
('liquid-glass-graph','Стеклянный график','Зелёный график растёт, число считается вверх',1,0,['--text','STREAK','--opt','from=1','--opt','to=30']),
('carousel-spin','Карусель','Ролики вращаются 3D-каруселью и замедляются',1,1,[]),
('match-cut','Склейка по слову','Страницы новостей режутся на одном слове в красной рамке',1,0,['--text','HABIT']),
('apple-toggles','Переключатели iPhone','Карточка настроек, переключатели включаются по строкам',1,0,['--text','Water|Sleep|Steps','--opt','ticks=1|2|3']),
('led-sign','LED-вывеска','Свет гаснет, за спиной печатается светящаяся вывеска',1,0,['--text','KEEP GOING']),
('slow-push','Медленный наезд','Кинематографичный наезд на лицо, фон расплывается',1,0,[]),
('over-the-shoulder-zoom','Графики из-за плеча','Камера наезжает в угол, рядом растёт стеклянный график',1,0,['--text','STEPS|WATER','--opt','to=7K|2L']),
('messages','Всплывающие сообщения','Сообщения iMessage всплывают одно за другим',1,0,['--text','Workout today?|Yes, 10 minutes|Proud of you']),
('place-in-grid','Плитка профиля','Человек сжимается в центр сетки 3×3, вокруг появляются ролики',1,1,[]),
('tape-label','Лента с фразой','Жёлтая лента с фразой ложится на грудь',1,0,['--text','STOP DECIDING']),
('select-resize','Выделение и увеличение','Синяя рамка хватает число и курсор увеличивает его',1,0,['--text','2X']),
('wave-trim','Обрезка тишины','Панель с голосом, красные паузы схлопываются',0,0,[]),
('huge-strike','Огромное слово зачёркнуто','Большое слово появляется и перечёркивается красной линией',1,0,['--text','EXCUSES']),
('crayon-write','Мелок','Красный мелок пишет слово, подчёркивает и улетает',1,0,['--text','START']),
('fan-build','Веер обложек','Обложки раскладываются веером по одной',1,1,[]),
]
assert len(E) == 51, len(E)

def sh(*a, **k): return subprocess.run(a, capture_output=True, text=True, **k)

sample = os.path.join(D, 'face_sample.mp4')
if not os.path.exists(sample):
    sh('ffmpeg','-v','error','-y','-ss','0','-t','4','-i',os.path.join(D,'km_plan_tonight_en_nofx.mp4'),'-c:v','libx264','-crf','20','-c:a','aac',sample)
if not glob.glob(os.path.join(IMGS, '*.jpg')):
    for i, f in enumerate(['km_missed_workout_en_nofx','km_plan_tonight_en_nofx','km_boring_days_en_nofx']):
        for j, t in enumerate([1, 5, 9]):
            sh('ffmpeg','-v','error','-y','-ss',str(t),'-i',os.path.join(D,f+'.mp4'),'-frames:v','1','-vf','scale=540:-1',os.path.join(IMGS,f'{i*3+j+1}.jpg'))

old = {c['id']: c for c in json.load(open(CAT, encoding='utf-8'))} if os.path.exists(CAT) else {}
cat = []
for id_, ru, desc, face, imgs, args in E:
    p = os.path.join(PREV, id_ + '.mp4')
    st = old.get(id_, {}).get('status', 'ok' if os.path.exists(p) else 'todo')
    cat.append(dict(id=id_, ru=ru, desc=desc, face=bool(face), images=bool(imgs), status=st))
json.dump(cat, open(CAT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

env = dict(os.environ, PYTHONIOENCODING='utf-8')
for c, (id_, ru, desc, face, imgs, args) in zip(cat, E):
    p = os.path.join(PREV, id_ + '.mp4')
    if c['status'] in ('ok',) and os.path.exists(p): continue
    cmd = [PY, FX, id_, sample, p, '--start', '0.3', '--end', '3.7', '--width', '540'] + args
    if imgs: cmd += ['--opt', 'images=' + IMGS]
    r = subprocess.run(cmd, capture_output=True, text=True, env=env)
    ok = r.returncode == 0 and os.path.exists(p) and os.path.getsize(p) > 20000
    c['status'] = 'ok' if ok else 'fail'
    if not ok:
        open(os.path.join(D, f'prev_{id_}.log'), 'w', encoding='utf-8').write((r.stdout or '') + (r.stderr or ''))
    json.dump(cat, open(CAT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(id_, c['status'], flush=True)
print('done')
