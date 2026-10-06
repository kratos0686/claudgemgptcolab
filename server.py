#!/usr/bin/env python3
"""
server.py -- Flask backend that connects gui.html to real AI APIs via SSE streaming.

Endpoints:
  GET  /api/status             - health check + key status
  POST /api/session/start      - start a new session
  POST /api/session/turn       - run one round-robin AI turn (SSE stream)
  POST /api/session/next_phase - manually advance the phase
  POST /api/session/pause      - save checkpoint
  POST /api/session/end        - end session
  GET  /api/sessions           - list saved checkpoints
  DELETE /api/sessions/<id>    - delete a checkpoint

SSE events emitted by /api/session/turn:
  event:token       data:{ai, token}
  event:turn_done   data:{ai, full_text, phase_idx, phase, turn}
  event:phase_done  data:{phase, next_phase, phase_idx}
  event:round_done  data:{phase_idx, total_turns}
  event:done        data:{total_turns, reason}
  event:error       data:{message}

Start the server:
  python server.py              # default http://127.0.0.1:5000
  python server.py --port 8080
"""

import json, os, sys, argparse, threading, queue
from datetime import datetime
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    from flask import Flask, request, jsonify, Response, send_from_directory
    from flask_cors import CORS
except ImportError:
    sys.exit('Missing: pip install flask flask-cors')

try:
    import anthropic
except ImportError:
    sys.exit('Missing: pip install anthropic')

try:
    import openai as openai_lib
except ImportError:
    sys.exit('Missing: pip install openai')

try:
    from google import genai as genai_lib
    from google.genai import types as genai_types
except ImportError:
    sys.exit('Missing: pip install google-genai')

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
CLAUDE_MODEL  = 'claude-opus-4-6'
GPT_MODEL     = 'gpt-4o'
GEMINI_MODEL  = 'gemini-2.0-flash'
MAX_HISTORY   = 30
PHASE_DONE    = 'PHASE_COMPLETE'
DONE_SIGNAL   = 'PROJECT_COMPLETE'
SESSIONS_DIR  = Path('sessions')

PHASES = [
    ('PLAN',   'Define requirements, user stories, constraints, task list',          'Claude'),
    ('DESIGN', 'Architecture, tech stack, data models, folder structure, API contracts', 'Claude'),
    ('BUILD',  'Write all production-quality implementation code',                   'Gemini'),
    ('TEST',   'Write unit tests, integration tests, verify edge cases',             'GPT-4o'),
    ('DOCS',   'Write README, inline docstrings, usage examples, API reference',     'GPT-4o'),
    ('SHIP',   'Dockerfile, CI/CD config, env-var checklist, deployment runbook',    'Gemini'),
]
AI_ORDER = ['Claude', 'GPT-4o', 'Gemini']

# ---------------------------------------------------------------------------
# System prompts
# ---------------------------------------------------------------------------
_PHASE_LIST = '\n'.join(
    f'  {i+1}. [{name}] ({lead} leads) -- {goal}'
    for i, (name, goal, lead) in enumerate(PHASES)
)
_COMMON = f'''
Development phases (in order):
{_PHASE_LIST}

Each turn you MUST do ALL of the following in order:
1. REVIEW the previous AI output: flag errors with fixes, or say OK.
2. CONTRIBUTE concrete output for the CURRENT phase.
   Label code files: ```python:main.py  or  # main.py as first comment.
3. HAND OFF to the next AI.

Phase signals (on their own line):
PHASE_COMPLETE -- current phase fully done; advance to next
PROJECT_COMPLETE -- all phases done; project finished
'''.strip()

CLAUDE_SYSTEM = f'You are Claude, leading PLAN and DESIGN.\n{_COMMON}'
GPT_SYSTEM    = f'You are GPT-4o, leading TEST and DOCS.\n{_COMMON}'
GEMINI_SYSTEM = f'You are Gemini, leading BUILD and SHIP.\n{_COMMON}'

# ---------------------------------------------------------------------------
# Flask app
# ---------------------------------------------------------------------------
app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)
_session = {}
_lock = threading.Lock()

# ---------------------------------------------------------------------------
# Client factory
# ---------------------------------------------------------------------------
def _build_clients():
    ak = os.environ.get('ANTHROPIC_API_KEY', '')
    ok = os.environ.get('OPENAI_API_KEY', '')
    gk = os.environ.get('GEMINI_API_KEY', '')
    missing = [n for n,v in [('ANTHROPIC_API_KEY',ak),('OPENAI_API_KEY',ok),('GEMINI_API_KEY',gk)] if not v]
    if missing:
        raise ValueError(f'Missing API keys: {chr(44).join(missing)}')
    return (
        anthropic.Anthropic(api_key=ak),
        openai_lib.OpenAI(api_key=ok),
        genai_lib.Client(api_key=gk),
    )

# ---------------------------------------------------------------------------
# History trimming
# ---------------------------------------------------------------------------
def _trim(history, n=MAX_HISTORY):
    if len(history) <= n:
        return history
    return [history[0]] + history[-(n-1):]

# ---------------------------------------------------------------------------
# Streaming AI callers
# ---------------------------------------------------------------------------
def _stream_claude(client, history, project, phase, q):
    msgs = []
    for e in _trim(history):
        role = 'assistant' if e['speaker'] == 'Claude' else 'user'
        msgs.append({'role': role, 'content': f"[{e['speaker']}]: {e['text']}"})
    full = ''
    try:
        with client.messages.stream(
            model=CLAUDE_MODEL, max_tokens=4096,
            system=CLAUDE_SYSTEM + f'\n\nProject: {project}\nPhase: {phase}',
            messages=msgs,
        ) as stream:
            for chunk in stream.text_stream:
                full += chunk
                q.put(('token', {'ai': 'Claude', 'token': chunk}))
    except Exception as exc:
        q.put(('error', {'message': f'Claude error: {exc}'}))
    return full.strip()

def _stream_gpt(client, history, project, phase, q):
    msgs = [{'role':'system','content':GPT_SYSTEM},
            {'role':'user','content':f'Project: {project}\nPhase: {phase}'}]
    for e in _trim(history):
        role = 'assistant' if e['speaker'] == 'GPT-4o' else 'user'
        msgs.append({'role': role, 'content': f"[{e['speaker']}]: {e['text']}"})
    full = ''
    try:
        stream = client.chat.completions.create(
            model=GPT_MODEL, messages=msgs, max_tokens=4096, stream=True)
        for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                full += delta
                q.put(('token', {'ai': 'GPT-4o', 'token': delta}))
    except Exception as exc:
        q.put(('error', {'message': f'GPT-4o error: {exc}'}))
    return full.strip()

def _stream_gemini(client, history, project, phase, q):
    contents = []
    preamble = f'Project: {project}\nPhase: {phase}\n\nConversation below. Continue as Gemini.'
    contents.append(genai_types.Content(role='user', parts=[genai_types.Part(text=preamble)]))
    contents.append(genai_types.Content(role='model', parts=[genai_types.Part(text='Understood.')]))
    for e in _trim(history):
        role = 'model' if e['speaker'] == 'Gemini' else 'user'
        contents.append(genai_types.Content(role=role, parts=[genai_types.Part(text=f"[{e['speaker']}]: {e['text']}")]))
    if contents[-1].role == 'model':
        contents.append(genai_types.Content(role='user', parts=[genai_types.Part(text=f'Gemini, please review and continue (phase: {phase}).')]))
    full = ''
    try:
        for chunk in client.models.generate_content_stream(
            model=GEMINI_MODEL, contents=contents,
            config=genai_types.GenerateContentConfig(system_instruction=GEMINI_SYSTEM, max_output_tokens=4096),
        ):
            piece = chunk.text or ''
            full += piece
            q.put(('token', {'ai': 'Gemini', 'token': piece}))
    except Exception as exc:
        q.put(('error', {'message': f'Gemini error: {exc}'}))
    return full.strip()

# ---------------------------------------------------------------------------
# Session persistence
# ---------------------------------------------------------------------------
def _sess_path(sid):
    SESSIONS_DIR.mkdir(exist_ok=True)
    return SESSIONS_DIR / f'{sid}.json'

def _save(sess):
    data = {k: v for k, v in sess.items() if not k.startswith('_')}
    try:
        _sess_path(sess['session_id']).write_text(json.dumps(data, indent=2), encoding='utf-8')
    except OSError:
        pass

def _load(sid):
    p = _sess_path(sid)
    if not p.exists(): return None
    try: return json.loads(p.read_text(encoding='utf-8'))
    except Exception: return None

def _list():
    if not SESSIONS_DIR.exists(): return []
    files = sorted(SESSIONS_DIR.glob('*.json'), key=lambda f: f.stat().st_mtime, reverse=True)
    out = []
    for f in files[:20]:
        try: out.append(json.loads(f.read_text(encoding='utf-8')))
        except Exception: pass
    return out

# ---------------------------------------------------------------------------
# SSE helper
# ---------------------------------------------------------------------------
def _sse(event, data):
    return f'event: {event}\ndata: {json.dumps(data)}\n\n'

# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.route('/')
def index():
    return send_from_directory('.', 'gui.html')

@app.route('/api/status')
def api_status():
    ak = bool(os.environ.get('ANTHROPIC_API_KEY','').strip())
    ok = bool(os.environ.get('OPENAI_API_KEY','').strip())
    gk = bool(os.environ.get('GEMINI_API_KEY','').strip())
    return jsonify({
        'ok': True,
        'keys': {'anthropic': ak, 'openai': ok, 'gemini': gk},
        'all_keys_set': ak and ok and gk,
        'active_session': _session.get('session_id'),
    })

@app.route('/api/session/start', methods=['POST'])
def api_start():
    global _session
    body = request.get_json(force=True) or {}
    desc = (body.get('project_desc') or '').strip()
    if not desc:
        return jsonify({'error': 'project_desc required'}), 400
    try:
        cc, gc, gc2 = _build_clients()
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    sid = datetime.now().strftime('%Y%m%d_%H%M%S')
    with _lock:
        _session = {
            'session_id': sid, 'project_desc': desc,
            'phase_idx': 0, 'total_turns': 0,
            'history': [{'speaker': 'User', 'text': desc}],
            '_c': cc, '_g': gc, '_gem': gc2,
        }
    _save(_session)
    return jsonify({'session_id': sid, 'phase': PHASES[0][0], 'phase_idx': 0})

@app.route('/api/session/load', methods=['POST'])
def api_load():
    global _session
    body = request.get_json(force=True) or {}
    sid = body.get('session_id','')
    ck = _load(sid)
    if not ck: return jsonify({'error': 'not found'}), 404
    try:
        cc, gc, gc2 = _build_clients()
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    with _lock:
        _session = {**ck, '_c': cc, '_g': gc, '_gem': gc2}
    return jsonify({
        'session_id': sid, 'phase_idx': ck['phase_idx'],
        'total_turns': ck['total_turns'], 'history': ck['history'],
        'phase': PHASES[min(ck['phase_idx'], len(PHASES)-1)][0],
    })

@app.route('/api/session/turn', methods=['POST'])
def api_turn():
    body = request.get_json(force=True) or {}
    guidance = (body.get('user_guidance') or '').strip()
    if not _session.get('session_id'):
        return jsonify({'error': 'No active session'}), 400
    if guidance:
        with _lock:
            _session['history'].append({'speaker': 'User', 'text': guidance})

    def gen():
        with _lock:
            pidx    = _session['phase_idx']
            hist    = list(_session['history'])
            proj    = _session['project_desc']
            cc      = _session['_c']
            gc      = _session['_g']
            gc2     = _session['_gem']
            total   = _session['total_turns']
        if pidx >= len(PHASES):
            yield _sse('done', {'total_turns': total})
            return
        pname, pgoal, plead = PHASES[pidx]
        callers = {
            'Claude':  lambda h,p,ph,q: _stream_claude(cc,  h,p,ph,q),
            'GPT-4o':  lambda h,p,ph,q: _stream_gpt(gc,    h,p,ph,q),
            'Gemini':  lambda h,p,ph,q: _stream_gemini(gc2, h,p,ph,q),
        }
        advanced = False
        for ai in AI_ORDER:
            q = queue.Queue()
            result = [None]
            def worker(a=ai, hh=hist, pp=proj, ph=pname, qq=q, rb=result):
                rb[0] = callers[a](hh, pp, ph, qq)
                qq.put(('__done__', None))
            t = threading.Thread(target=worker, daemon=True)
            t.start()
            full = ''
            while True:
                ev, dat = q.get()
                if ev == '__done__': break
                if ev == 'error':
                    yield _sse('error', dat)
                    t.join(); return
                full += dat['token']
                yield _sse('token', dat)
            t.join()
            full = result[0] or full
            total += 1
            hist.append({'speaker': ai, 'text': full})
            yield _sse('turn_done', {'ai':ai,'full_text':full,'phase_idx':pidx,'phase':pname,'turn':total})
            if DONE_SIGNAL in full:
                with _lock:
                    _session['history'] = hist
                    _session['phase_idx'] = len(PHASES)
                    _session['total_turns'] = total
                _save(_session)
                yield _sse('done', {'total_turns': total, 'reason': 'PROJECT_COMPLETE'})
                return
            if PHASE_DONE in full:
                pidx += 1
                with _lock:
                    _session['history'] = hist
                    _session['phase_idx'] = pidx
                    _session['total_turns'] = total
                _save(_session)
                nxt = PHASES[pidx][0] if pidx < len(PHASES) else None
                yield _sse('phase_done', {'phase':pname,'next_phase':nxt,'phase_idx':pidx})
                if pidx >= len(PHASES):
                    yield _sse('done', {'total_turns': total, 'reason': 'ALL_PHASES'})
                advanced = True
                break
        if not advanced:
            with _lock:
                _session['history'] = hist
                _session['total_turns'] = total
            _save(_session)
            yield _sse('round_done', {'phase_idx': pidx, 'total_turns': total})

    return Response(gen(), mimetype='text/event-stream',
                    headers={'Cache-Control':'no-cache','X-Accel-Buffering':'no'})

@app.route('/api/session/next_phase', methods=['POST'])
def api_next_phase():
    with _lock:
        if _session.get('phase_idx', 0) < len(PHASES) - 1:
            _session['phase_idx'] += 1
        pidx = _session.get('phase_idx', 0)
    _save(_session)
    return jsonify({'phase_idx': pidx, 'phase': PHASES[min(pidx, len(PHASES)-1)][0]})

@app.route('/api/session/pause', methods=['POST'])
def api_pause():
    _save(_session)
    return jsonify({'ok': True, 'session_id': _session.get('session_id')})

@app.route('/api/session/end', methods=['POST'])
def api_end():
    global _session
    _save(_session)
    sid = _session.get('session_id')
    _session = {}
    return jsonify({'ok': True, 'session_id': sid})

@app.route('/api/sessions', methods=['GET'])
def api_sessions():
    return jsonify(_list())

@app.route('/api/sessions/<sid>', methods=['DELETE'])
def api_del_session(sid):
    p = _sess_path(sid)
    if p.exists(): p.unlink()
    return jsonify({'ok': True})

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='AI Collaboration Tool -- GUI server')
    parser.add_argument('--port', type=int, default=5000)
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('--debug', action='store_true')
    args = parser.parse_args()

    url = f'http://{args.host}:{args.port}'
    print(f'''
  +------------------------------------------------------+
  |  AI Collaboration Tool -- GUI Server                 |
  +------------------------------------------------------+
  |  Open in browser: {url}                    |
  +------------------------------------------------------+
    ''')

    for name, key in [('ANTHROPIC_API_KEY', 'anthropic'), ('OPENAI_API_KEY', 'openai'), ('GEMINI_API_KEY', 'gemini')]:
        val = bool(os.environ.get(name, '').strip())
        print(f'  {name:25s}: {chr(10003) if val else chr(10007)} {"set" if val else "MISSING"}')

    print()
    app.run(host=args.host, port=args.port, debug=args.debug, threaded=True)
