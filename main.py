import os
from subprocess import run, PIPE, STDOUT
from threading import Thread
from time import sleep
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

def move(id, d, p, s):
    runex(["wmctrl", "-i", "-r", id, "-t", str(d)])
    mvarg = "0,%s" % ",".join([str(int(i)) for i in (*p, *s)])
    runex(["wmctrl", "-i", "-r", id, "-e", mvarg])

def launch(app, to=2):
    def run_app(app):
        run(["gtk-launch", app], env=os.environ)
    thread = Thread(target=run_app, args=(app,))
    thread.daemon = True
    thread.start()
    sleep(to)
    print("'%s' app launched" % app)

    id = find_id(0)
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

def params(geom, grid, xp, yp, xs=1, ys=1):
    grid = [g + [1.0 - sum(g)] for g in grid]
    pos = (
        (geom[0]*sum(grid[0][0:xp])),
        (geom[1]*sum(grid[1][0:yp])),
    )
    if xs < 0:
        xs = len(grid[0]) - xs
    if ys < 0:
        ys = len(grid[1]) - ys
    size = (
        (geom[0]*sum(grid[0][xp:(xp+xs)])),
        (geom[1]*sum(grid[1][yp:(yp+ys)])),
    )
    return (pos, size)

def make_develop(desk=1):
    geom = geometry(desk)
    grid = [[0.35, 0.35], [0.4]]

    App("firefox-esr").move(desk, *params(geom, grid, 0, 0, ys=-1))
    #App("sublime_text")
    App("firefox-esr").move(desk, *params(geom, grid, 1, 0, ys=-1))
    App("nemo").move(desk, *params(geom, grid, 2, 0))
    App("org.gnome.Terminal").move(desk, *params(geom, grid, 2, 1))

if __name__ == "__main__":
    make_develop()
