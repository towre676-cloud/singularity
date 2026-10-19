"""Reusable request interface for compiled exact completion planners."""
import json
from pathlib import Path
from random import Random
from .planning import CompletionPlanner, optimize_allocation

METHODS = ('summary', 'evidence', 'count', 'completions', 'select', 'rank', 'optimize', 'page', 'sample')


def execute(request):
    if not isinstance(request, dict) or set(request)-{'specification', 'queries', 'seed', 'optimization_only'} or not {'specification', 'queries'} <= set(request):
        raise ValueError('specification and queries required')
    mode = request.get('optimization_only', False)
    if type(mode) is not bool: raise ValueError('optimization_only must be Boolean')
    if mode:
        if request['queries'] != [] or 'seed' in request: raise ValueError('optimization-only requests require empty queries and no seed')
        return optimize_allocation(request['specification'])
    planner = CompletionPlanner(request['specification'])
    queries = request['queries']
    if not isinstance(queries, list) or len(queries) > 256:
        raise ValueError('at most 256 queries required')
    seed = request.get('seed')
    if seed is not None and type(seed) is not int:
        raise ValueError('integer sampling seed required')
    rng = None if seed is None else Random(seed)
    answers = []
    for query in queries:
        if not isinstance(query, dict) or set(query)-{'method', 'args'} or query.get('method') not in METHODS:
            raise ValueError('known planner method required')
        args = query.get('args', {})
        if not isinstance(args, dict):
            raise ValueError('query args must be an object')
        if query['method'] == 'sample':
            if set(args)-{'optimal'}:
                raise ValueError('sample accepts only optimal')
            answer = planner.sample(rng=rng, **args)
        else:
            answer = getattr(planner, query['method'])(**args)
        answers.append(answer)
    return {'schema': 'pp-planning-request/1', 'summary': planner.summary(), 'answers': answers}


def add_commands(sub):
    parser = sub.add_parser('plan', help='compile resource allocations or action words and query completions')
    parser.add_argument('request', type=Path)
    parser.add_argument('--output', type=Path)


def cli(args):
    if args.command != 'plan':
        return False
    answer = execute(json.loads(args.request.read_text()))
    text = json.dumps(answer, indent=2, default=str)+'\n'
    if args.output:
        args.output.write_text(text)
    else:
        print(text, end='')
    return True
