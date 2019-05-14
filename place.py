import os
import sys
from subprocess import run, PIPE, STDOUT
from threading import Thread
from time import sleep
import json
import re

_rrsre = re.compile("[ \t]+")
def rrs(text):
    return re.sub(_rrsre, " ", text)

def runex(args, **kwargs):
    cp = run(
        args,
        stdout=PIPE, stderr=STDOUT, text=True,
        env=os.environ,
        **kwargs,
    )
    rc = cp.returncode
    assert rc == 0, "%s returned %s: %s" % (args, rc, cp.stdout)
    return cp.stdout

def find_id(desk):
    text = runex(["wmctrl", "-l"]).strip()
    lines = [rrs(l).split(" ") for l in text.split("\n")]
    line = [l for l in lines if int(l[1]) == desk][-1]
    return line[0]

_props = "fullscreen,maximized_vert,maximized_horz"
def move(id, d, p, s):
    runex(["wmctrl", "-i", "-r", id, "-b", "remove,%s" % _props])
    runex(["wmctrl", "-i", "-r", id, "-t", str(d)])
    mvarg = "0,%s" % ",".join([str(int(i)) for i in (*p, *s)])
    runex(["wmctrl", "-i", "-r", id, "-e", mvarg])

def current():
    text = runex(["wmctrl", "-d"]).strip()
    lines = [rrs(l).split(" ") for l in text.split("\n")]
    return int([l[0] for l in lines if l[1] == "*"][0])

def launch(app, to=1):
    def run_app(app):
        run(["gtk-launch", app], env=os.environ)
    thread = Thread(target=run_app, args=(app,))
    thread.daemon = True
    desk = current()
    thread.start()
    sleep(to)
    print("'%s' app launched" % app)

    id = find_id(desk)
    print("app id is %s" % id)
    return id


def geometry(desk):
    text = runex(["wmctrl", "-d"]).strip()
    line = rrs(text.split("\n")[desk]).split(" ")
    res = tuple([int(x) for x in line[8].split("x")])
    print("desk %s geometry is %s" % (desk, res))
    return res

class App:
    def __init__(self, name):
        self.name = name
        self.id = launch(self.name)

    def move(self, desk, pos, size):
        move(self.id, desk, pos, size)

def check_int2(v):
    assert len(v) == 2
    assert all([int(x) == x for x in v])

def place(cfg):
    desk = cfg["desktop"]
    geom = cfg["resolution"]
    if geom == "auto":
        geom = geometry(desk)
    else:
        check_int2(geom)

    brd = (cfg["borders"]["h"], cfg["borders"]["v"])
    check_int2(brd[0])
    check_int2(brd[1])

    for app in cfg["apps"]:
        mode = app["mode"]
        pos = app["pos"]
        size = app["size"]

        if mode == "absolute":
            pass
        elif mode == "proportional":
            for i, g, p, s in zip(range(2), geom, pos, size):
                pos[i] = int(g*p)
                size[i] = int(g*(p + s)) - pos[i]
        else:
            raise TypeError("Unknown mode: %s" % mode)
        check_int2(pos)
        check_int2(size)

        size = [x - (b[0] + b[1]) for x, b in zip(size, brd)]

        App(app["launch"]).move(desk, pos, size)

if __name__ == "__main__":
    with open(sys.argv[1], "r") as file:
        config = json.loads(file.read())
    place(config)
