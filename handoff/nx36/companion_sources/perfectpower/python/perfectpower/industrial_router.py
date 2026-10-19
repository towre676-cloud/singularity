"""Opt-in sort-checked QF_NIA to QF_LIA dispatch. Assertions stay unchanged."""
from .smt_cert import split_commands, _sexpr


def numeral(t):
    if isinstance(t, str) and t.isdigit():
        return int(t)
    if isinstance(t, list) and len(t) == 2 and t[0] == '-':
        n = numeral(t[1])
        return None if n is None else -n
    return None


def route_lia(script):
    frames = [{}]
    commands = split_commands(script)
    logic = None

    def sort(t):
        if isinstance(t, str):
            if numeral(t) is not None:
                return 'Int'
            if t in ('true', 'false'):
                return 'Bool'
            return next((f[t] for f in reversed(frames) if t in f), None)
        if not t:
            return None
        op, args = t[0], t[1:]
        ss = [sort(a) for a in args]
        if op in ('+', '-') and args and all(s == 'Int' for s in ss):
            return 'Int'
        if op == '*' and args and all(s == 'Int' for s in ss):
            return 'Int' if sum(numeral(a) is None for a in args) <= 1 else None
        if op in ('div', 'mod') and len(args) == 2 and ss == ['Int', 'Int']:
            d = numeral(args[1])
            return 'Int' if d is not None and d != 0 else None
        if op in ('and', 'or', 'xor') and all(s == 'Bool' for s in ss):
            return 'Bool'
        if op == '=>' and len(args) >= 2 and all(s == 'Bool' for s in ss):
            return 'Bool'
        if op == 'not' and ss == ['Bool']:
            return 'Bool'
        if op in ('=', 'distinct') and len(args) >= 2 and ss[0] in ('Int', 'Bool') and len(set(ss)) == 1:
            return 'Bool'
        if op in ('<', '<=', '>', '>=') and len(args) >= 2 and all(s == 'Int' for s in ss):
            return 'Bool'
        if op == 'ite' and len(args) == 3 and ss[0] == 'Bool' and ss[1] in ('Int', 'Bool') and ss[1] == ss[2]:
            return ss[1]
        return None

    try:
        for index, raw in enumerate(commands):
            t = _sexpr(raw)
            op = t[0]
            if op == 'set-logic':
                if t != ['set-logic', 'QF_NIA'] or logic is not None:
                    return script, False
                logic = index
            elif op in ('declare-const', 'declare-fun'):
                if op == 'declare-const' and len(t) == 3:
                    name, s = t[1:]
                elif op == 'declare-fun' and len(t) == 4 and t[2] == []:
                    name, s = t[1], t[3]
                else:
                    return script, False
                if s not in ('Int', 'Bool') or any(name in f for f in frames):
                    return script, False
                frames[-1][name] = s
            elif op == 'assert':
                if len(t) != 2 or sort(t[1]) != 'Bool':
                    return script, False
            elif op in ('push', 'pop'):
                n = 1 if len(t) == 1 else numeral(t[1]) if len(t) == 2 else None
                if n is None or n < 0:
                    return script, False
                if op == 'push':
                    frames.extend({} for _ in range(n))
                elif n >= len(frames):
                    return script, False
                elif n:
                    del frames[-n:]
            elif op == 'check-sat-assuming':
                if len(t) != 2 or not isinstance(t[1], list) or any(sort(a) != 'Bool' for a in t[1]):
                    return script, False
            elif op not in ('set-info', 'check-sat', 'get-model', 'get-info', 'get-value', 'exit'):
                return script, False
        if logic is None:
            return script, False
        commands[logic] = '(set-logic QF_LIA)'
        return '\n'.join(commands) + '\n', True
    except (ValueError, TypeError, IndexError):
        return script, False
