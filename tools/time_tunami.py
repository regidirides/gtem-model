"""Time TUNAMI-EVAC1 on the Arahama scenario, with minimal instrumentation.

The simulation loop reads nothing per tick - completion is checked every 60
ticks - so the measurement is the model's own cost, not JPype round-trips.
"""
import os, sys, glob, json, time
import jpype

#: Override with NETLOGO_622_HOME / NETLOGO_JVM if installed elsewhere.
NL = os.environ.get("NETLOGO_622_HOME", "/Applications/NetLogo 6.2.2")
MODEL, OUT, REPS = sys.argv[1], sys.argv[2], int(sys.argv[3])
SEEDS = [65620156 + i for i in range(REPS)]

jars = glob.glob(os.path.join(NL, "Java", "*.jar"))
t_jvm0 = time.perf_counter()
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
jvm_open = time.perf_counter() - t_jvm0

SAFE = "safe-kids + safe-teens + safe-adults + safe-elders + (safe-cars * 4)"
CAS = "casualty-kids + casualty-teens + casualty-adults + casualty-elders + (casualty-cars * 4)"
TOTAL, runs = 2271, []

for seed in SEEDS:
    for cmd in ("set #-of-adults 2271", "set #-of-kids 0", "set #-of-teens 0",
                "set #-of-elders 0", "set #-of-cars 0", "set u 14", "set ETA 67",
                "set TS 70", "set tsunami? true", "set random-shelter? false",
                "set %-of-handicap 0", "set movie? false", "set snapshots? false",
                "set output-files? false", "set run-number 1", f"random-seed {seed}"):
        ws.command(cmd)
    t0 = time.perf_counter()
    ws.command("setup")               # includes GIS load and A* preparation
    t_setup = time.perf_counter() - t0
    t1 = time.perf_counter()
    ticks = 0
    while True:
        ws.command("repeat 60 [ go ]")
        ticks += 60
        if ticks >= 70 * 60:
            break
        if float(ws.report(SAFE)) + float(ws.report(CAS)) >= TOTAL:
            break
    t_sim = time.perf_counter() - t1
    runs.append({"seed": seed, "setup_s": t_setup, "sim_s": t_sim,
                 "total_s": t_setup + t_sim, "ticks": ticks,
                 "safe": float(ws.report(SAFE))})
    print(f"  seed {seed}: setup {t_setup:6.1f}s  sim {t_sim:7.1f}s  "
          f"total {t_setup+t_sim:7.1f}s  ticks {ticks}")
    sys.stdout.flush()

json.dump({"jvm_open_s": jvm_open, "runs": runs, "agents": TOTAL}, open(OUT, "w"))
print(f"  JVM+model open: {jvm_open:.1f}s (once per session)")
sys.stdout.flush()
os._exit(0)
