"""Run TUNAMI-EVAC1 and capture agent positions for the side-by-side animation.

Positions are read with `map [t -> ... of t] sort <breed>` rather than
`[...] of <breed>`: the latter shuffles and consumes the random stream, which
would change the very run being recorded.
"""
import os, sys, glob, json
import numpy as np
import jpype

#: Override with NETLOGO_622_HOME / NETLOGO_JVM if installed elsewhere.
NL = os.environ.get("NETLOGO_622_HOME", "/Applications/NetLogo 6.2.2")
MODEL, OUT = sys.argv[1], sys.argv[2]
EVERY = 20                      # sample every 20 ticks == 20 simulated seconds

jars = glob.glob(os.path.join(NL, "Java", "*.jar"))
JVM = os.environ.get(
    "NETLOGO_JVM",
    "/Applications/NetLogo 7.0.4/runtime/Contents/Home/lib/server/libjvm.dylib")
# NetLogo 6.2.2 ships an x86_64 JRE; on Apple Silicon its own JVM cannot be
# loaded, so an arm64 JVM runs its (pure Java) jars instead.
jpype.startJVM(JVM,
               "-Xmx4096m", "-Djava.awt.headless=true", classpath=jars, convertStrings=True)
jpype.java.lang.System.setProperty("netlogo.extensions.dir", os.path.join(NL, "extensions"))
ws = jpype.JClass("org.nlogo.headless.HeadlessWorkspace").newInstance()
ws.open(MODEL, True)

for cmd in ("set #-of-adults 2271", "set #-of-kids 0", "set #-of-teens 0",
            "set #-of-elders 0", "set #-of-cars 0", "set u 14", "set ETA 67",
            "set TS 70", "set tsunami? true", "set random-shelter? false",
            "set %-of-handicap 0", "set movie? false", "set snapshots? false",
            "set output-files? false", "set run-number 1", "random-seed 65620156"):
    ws.command(cmd)
ws.command("setup")

def to_rows(logolist):
    """NetLogo LogoList -> list of [x, y]. JPype cannot iterate it directly."""
    n = int(logolist.size())
    out = []
    for i in range(n):
        inner = logolist.get(i)
        out.append([float(inner.get(0)), float(inner.get(1))])
    return out


def patch_xy(which):
    n = int(float(ws.report(f"count {which}")))
    if n == 0:
        return np.empty((0, 2))
    rows = ws.report(f"map [ p -> [ (list pxcor pycor) ] of p ] sort {which}")
    return np.asarray(to_rows(rows), dtype=float)

static = {"street": patch_xy("street-patches"),
          "exit": patch_xy("exit-patches"),
          "teb": patch_xy("teb-patches")}

SAFE = "safe-kids + safe-teens + safe-adults + safe-elders + (safe-cars * 4)"
CAS = "casualty-kids + casualty-teens + casualty-adults + casualty-elders + (casualty-cars * 4)"
TOTAL = 2271
frames, ticks_list, safe_list, cas_list = [], [], [], []
MAX = 70 * 60

while True:
    t = float(ws.report("ticks"))
    if int(t) % EVERY == 0:
        n = int(float(ws.report("count (turtle-set kids teens adults elders)")))
        if n:
            rows = ws.report("map [ a -> [ (list xcor ycor) ] of a ] "
                             "sort (turtle-set kids teens adults elders)")
            xy = np.asarray(to_rows(rows), dtype=float)
        else:
            xy = np.empty((0, 2))
        frames.append(xy)
        ticks_list.append(t)
        safe_list.append(float(ws.report(SAFE)))
        cas_list.append(float(ws.report(CAS)))
    if t >= MAX or (float(ws.report(SAFE)) + float(ws.report(CAS))) >= TOTAL:
        break
    ws.command("go")

payload = {"ticks": np.array(ticks_list), "safe": np.array(safe_list),
           "casualty": np.array(cas_list), "total": TOTAL,
           "counts": np.array([len(f) for f in frames]),
           "xy": np.concatenate(frames) if frames else np.empty((0, 2))}
payload.update({f"static_{k}": v for k, v in static.items()})
np.savez_compressed(OUT, **payload)
print(f"  {len(frames)} frames to {ticks_list[-1]/60:.1f} min; "
      f"final safe {safe_list[-1]:.0f}/{TOTAL}; "
      f"streets {len(static['street'])} exits {len(static['exit'])} teb {len(static['teb'])}")
sys.stdout.flush()
os._exit(0)
