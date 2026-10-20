#!/usr/bin/env python3
"""Test extras/spoolman_slots.py with stand-ins for Klipper's objects.

usage: test_spoolman_slots.py
"""
import ast
import importlib.util
import os
import sys

REPO = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("spoolman_slots", os.path.join(
    REPO, "extras", "spoolman_slots.py"))
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
ok = True


def check(name, cond):
    global ok
    print("%-58s %s" % (name, "PASS" if cond else "FAIL"))
    ok &= bool(cond)


class Error(Exception):
    pass


class GCode:
    def __init__(self):
        self.cmds, self.scripts = {}, []

    def register_command(self, n, f, desc=None):
        self.cmds[n] = f

    def run_script_from_command(self, s):
        self.scripts.append(s)


class GCmd:
    error = Error

    def __init__(self, **p):
        self.p, self.info = p, []

    def get_int(self, n, d=None, minval=None, maxval=None):
        v = int(self.p.get(n, d))
        if v < minval or v > maxval:
            raise Error(n)
        return v

    def get(self, n, d=None):
        return self.p.get(n, d)

    def respond_info(self, m):
        self.info.append(m)


class Webhooks:
    def __init__(self, fail=False):
        self.calls, self.fail = [], fail

    def call_remote_method(self, m, **kw):
        if self.fail:
            raise Error("Remote method not registered")
        self.calls.append((m, kw))


class Obj:
    def __init__(self, st=None, **a):
        self.st = st
        self.__dict__.update(a)

    def get_status(self, e):
        return self.st


class Printer:
    def __init__(self, objs):
        self.objs, self.h = objs, {}

    def lookup_object(self, n, d=None):
        return self.objs.get(n, d)

    def register_event_handler(self, e, f):
        self.h[e] = f


class Config:
    def __init__(self, p):
        self.p = p

    def get_printer(self):
        return self.p


def setup(saved=None, fail=False, channel=0):
    g, wh = GCode(), Webhooks(fail)
    objs = {'gcode': g, 'webhooks': wh, 'ifs': Obj({'channel': channel}),
            'save_variables': Obj(allVariables=saved or {})}
    p = Printer(objs)
    m = mod.load_config(Config(p))
    p.h["klippy:connect"]()
    return p, m, g, wh


p, m, g, wh = setup()
p.h["ifs:loaded"](2)
check("no spools set: active spool left alone", wh.calls == [])
g.cmds["SPOOLMAN_SET_SLOT"](GCmd(SLOT=3, SPOOL="12"))
check("SET_SLOT saved as spoolman_slots",
      g.scripts[-1].startswith("SAVE_VARIABLE VARIABLE=spoolman_slots")
      and ast.literal_eval(g.scripts[-1].split("VALUE=", 1)[1].strip('"'))
      == [None, None, 12, None])
p.h["ifs:loaded"](3)
p.h["ifs:loaded"](1)
p.h["ifs:loaded"](0)
check("slot 3 loaded: spool 12 active; slot 1 / empty: none",
      wh.calls == [("spoolman_set_active_spool", {"spool_id": 12}),
                   ("spoolman_set_active_spool", {"spool_id": None}),
                   ("spoolman_set_active_spool", {"spool_id": None})])
check("status", m.get_status(0)['slots'] == {"1": None, "2": None,
                                             "3": 12, "4": None})
try:
    g.cmds["SPOOLMAN_SET_SLOT"](GCmd(SLOT=1, SPOOL="x"))
    check("bad SPOOL refused", False)
except Error:
    check("bad SPOOL refused", True)
p, m, g, wh = setup(saved={"spoolman_slots": [5, None, 7, None]}, channel=3)
check("loaded from variables", m.spools == [5, None, 7, None])
g.cmds["SPOOLMAN_SET_SLOT"](GCmd(SLOT=3, SPOOL="9"))
check("setting the loaded slot activates it at once",
      wh.calls == [("spoolman_set_active_spool", {"spool_id": 9})])
p, m, g, wh = setup(saved={"spoolman_slots": [5, 6, 7, 8]}, fail=True)
p.h["ifs:loaded"](1)
check("Moonraker without [spoolman]: no error", True)
print("ALL PASS" if ok else "FAILURES")
sys.exit(0 if ok else 1)
