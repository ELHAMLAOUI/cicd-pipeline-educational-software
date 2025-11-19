"""
Moteur du simulateur de pipeline CI/CD.

Un « espace de travail » est un dépôt Git (l'application de l'étudiant) qui contient
un fichier pipeline.yml. À chaque commit, un hook Git appelle run_pipeline() :
les étapes sont exécutées dans l'ordre, l'historique est enregistré dans
.pipeline/runs/, et la page .pipeline/status.html est régénérée.

Format de pipeline.yml :

    name: boutique
    stages:
      - name: build
        run: python -m compileall -q src
      - name: test
        run: python -m unittest discover -s tests
        coverage_min: 80          # facultatif : seuil de couverture (%)
      - name: deploy-staging
        deploy: staging           # déploiement intégré (copie + contrôle de santé)
        when: branch == main      # facultatif : condition sur la branche
        on_failure: rollback      # facultatif : retour à la version précédente
"""
import datetime as _dt
import fnmatch
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import time

try:
    import yaml
except ImportError:  # pragma: no cover
    sys.exit("Module PyYAML absent : pip install pyyaml")

PY = sys.executable
STAGE_TIMEOUT = 120


# ----------------------------------------------------------------- utilitaires

def git(ws, *args, check=False):
    r = subprocess.run(["git", "-C", ws, *args], capture_output=True, text=True)
    if check and r.returncode != 0:
        raise RuntimeError(r.stderr.strip())
    return r.stdout.strip()


def pipeline_dir(ws):
    d = os.path.join(ws, ".pipeline")
    os.makedirs(os.path.join(d, "runs"), exist_ok=True)
    return d


def load_runs(ws):
    d = os.path.join(ws, ".pipeline", "runs")
    if not os.path.isdir(d):
        return []
    runs = []
    for f in sorted(os.listdir(d)):
        if f.endswith(".json"):
            try:
                with open(os.path.join(d, f), encoding="utf-8") as fh:
                    runs.append(json.load(fh))
            except (OSError, ValueError):
                pass
    return sorted(runs, key=lambda r: r["id"])


def load_config(ws):
    with open(os.path.join(ws, "pipeline.yml"), encoding="utf-8") as fh:
        cfg = yaml.safe_load(fh) or {}
    if not isinstance(cfg.get("stages"), list) or not cfg["stages"]:
        raise ValueError("pipeline.yml doit contenir une liste « stages » non vide")
    for i, st in enumerate(cfg["stages"]):
        if not isinstance(st, dict) or "name" not in st:
            raise ValueError(f"l'étape n° {i + 1} n'a pas de champ « name »")
        if ("run" in st) == ("deploy" in st):
            raise ValueError(f"l'étape « {st['name']} » doit avoir soit « run », soit « deploy »")
    return cfg


def current_release(ws, env):
    f = os.path.join(ws, ".pipeline", "env", env, "current")
    try:
        with open(f, encoding="utf-8") as fh:
            return fh.read().strip() or None
    except OSError:
        return None


def _set_current(ws, env, release):
    d = os.path.join(ws, ".pipeline", "env", env)
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "current"), "w", encoding="utf-8") as fh:
        fh.write((release or "") + "\n")


def _python_cmd(cmd):
    """Remplace « python » en tête de commande par l'interpréteur courant (python3 / Windows)."""
    m = re.match(r"^\s*python3?(\s|$)", cmd)
    return shlex.quote(PY) + cmd[m.end() - len(m.group(1)):] if m else cmd


def _sh(ws, cmd, env_extra):
    env = dict(os.environ, **env_extra)
    try:
        r = subprocess.run(cmd, shell=True, cwd=ws, capture_output=True, text=True,
                           timeout=STAGE_TIMEOUT, env=env)
        return r.returncode, (r.stdout + r.stderr)
    except subprocess.TimeoutExpired:
        return 124, f"Délai dépassé ({STAGE_TIMEOUT} s)"


def eval_when(cond, branch):
    m = re.match(r"^\s*branch\s*(==|!=)\s*(\S+)\s*$", str(cond))
    if not m:
        raise ValueError(f"condition « {cond} » invalide (attendu : branch == <nom> ou branch != <nom>)")
    match = fnmatch.fnmatch(branch, m.group(2))
    return match if m.group(1) == "==" else not match


# ----------------------------------------------------------------- étapes

def _stage_run(ws, st, env_extra):
    out = {}
    cmd = _python_cmd(str(st["run"]))
    cov_min = st.get("coverage_min")
    if cov_min is not None:
        if not re.match(r"^\s*\S*python\S*\s+-m\s+unittest", cmd.replace(shlex.quote(PY), "python")):
            return "failed", "coverage_min n'est possible que sur une commande « python -m unittest ... »", out
        import importlib.util
        if importlib.util.find_spec("coverage") is None:
            return "failed", "Module coverage absent : pip install coverage", out
        cmd = re.sub(r"-m\s+unittest", "-m coverage run --source=src -m unittest", cmd, count=1)
    code, log = _sh(ws, cmd, env_extra)
    if code != 0:
        return "failed", log, out
    if cov_min is not None:
        _, rep = _sh(ws, f"{shlex.quote(PY)} -m coverage report", env_extra)
        m = re.search(r"^TOTAL.*?(\d+)%\s*$", rep, re.M)
        pct = int(m.group(1)) if m else 0
        out["coverage"] = pct
        out["coverage_min"] = cov_min
        log += "\n" + rep
        if pct < float(cov_min):
            return "failed", log + f"\nQuality gate : couverture {pct} % inférieure au seuil de {cov_min} %", out
        log += f"\nQuality gate : couverture {pct} % (seuil {cov_min} %)"
    return "success", log, out


def _stage_deploy(ws, st, short, env_extra):
    env = str(st["deploy"])
    base = os.path.join(pipeline_dir(ws), "env", env)
    rel = os.path.join(base, "releases", short)
    previous = current_release(ws, env)
    if os.path.isdir(rel):
        shutil.rmtree(rel)
    os.makedirs(rel)
    for item in ("src", "config", "healthcheck.py"):
        p = os.path.join(ws, item)
        if os.path.isdir(p):
            shutil.copytree(p, os.path.join(rel, item), ignore=shutil.ignore_patterns("__pycache__"))
        elif os.path.isfile(p):
            shutil.copy2(p, rel)
    _set_current(ws, env, short)
    out = {"env": env, "release": short, "previous": previous, "rollback": False}
    log = f"Déploiement de la version {short} en {env} (précédente : {previous or 'aucune'})\n"
    hc = os.path.join(rel, "healthcheck.py")
    if os.path.isfile(hc):
        code, hlog = _sh(rel, f"{shlex.quote(PY)} healthcheck.py . {shlex.quote(env)}", env_extra)
        log += "Contrôle de santé : " + hlog.strip() + "\n"
        out["healthcheck"] = "OK" if code == 0 else "KO"
    else:
        code = 0
        out["healthcheck"] = "absent"
    if code == 0:
        log += f"{env} sert maintenant la version {short}"
        return "success", log, out
    if st.get("on_failure") == "rollback" and previous:
        _set_current(ws, env, previous)
        out["rollback"] = True
        log += f"ROLLBACK : {env} revient à la version {previous}"
    else:
        log += f"ATTENTION : {env} sert une version en panne ({short}), aucun rollback configuré"
    out["current_after"] = current_release(ws, env)
    return "failed", log, out


# ----------------------------------------------------------------- pipeline

def run_pipeline(ws, trigger="commit"):
    ws = os.path.abspath(ws)
    pdir = pipeline_dir(ws)
    runs = load_runs(ws)
    sha = git(ws, "rev-parse", "HEAD")
    short = sha[:7]
    branch = git(ws, "rev-parse", "--abbrev-ref", "HEAD")
    run = {
        "id": (runs[-1]["id"] + 1) if runs else 1,
        "commit": sha, "short": short, "branch": branch,
        "message": git(ws, "log", "-1", "--format=%s"),
        "trigger": trigger,
        "date": _dt.datetime.now().isoformat(timespec="seconds"),
        "stages": [], "status": "success", "error": None,
    }
    env_extra = {"PIPELINE_BRANCH": branch, "PIPELINE_COMMIT": sha}
    t_run = time.time()
    try:
        cfg = load_config(ws)
    except Exception as e:  # configuration invalide : le pipeline échoue immédiatement
        run["status"] = "failed"
        run["error"] = f"pipeline.yml invalide : {e}"
        cfg = {"stages": []}
    failed = run["status"] == "failed"
    for st in cfg["stages"]:
        rec = {"name": st["name"], "status": "skipped", "duration": 0.0, "log": ""}
        run["stages"].append(rec)
        if failed:
            rec["reason"] = "étape précédente en échec"
            continue
        if "when" in st:
            try:
                ok = eval_when(st["when"], branch)
            except ValueError as e:
                rec.update(status="failed", log=str(e))
                failed = True
                continue
            if not ok:
                rec["reason"] = f"condition non remplie ({st['when']})"
                continue
        t0 = time.time()
        if "deploy" in st:
            status, log, extra = _stage_deploy(ws, st, short, env_extra)
        else:
            status, log, extra = _stage_run(ws, st, env_extra)
        rec.update(status=status, log=log[-4000:], duration=round(time.time() - t0, 2), **extra)
        if status != "success":
            failed = True
    if failed:
        run["status"] = "failed"
    run["duration"] = round(time.time() - t_run, 2)
    with open(os.path.join(pdir, "runs", f"{run['id']:04d}.json"), "w", encoding="utf-8") as fh:
        json.dump(run, fh, ensure_ascii=False, indent=1)
    from status_page import write_status_page
    write_status_page(ws, load_runs(ws))
    return run


# ----------------------------------------------------------------- affichage

def _colors():
    if sys.stdout.isatty() and not os.environ.get("NO_COLOR"):
        return {"g": "\033[32m", "r": "\033[31m", "y": "\033[33m", "b": "\033[1m", "d": "\033[2m", "x": "\033[0m"}
    return dict.fromkeys("grybdx", "")


def print_run(run, verbose_failures=True):
    c = _colors()
    print()
    print(f"{c['b']}Pipeline #{run['id']} — commit {run['short']} ({run['branch']}) « {run['message']} »{c['x']}")
    if run.get("error"):
        print(f"  {c['r']}[KO]{c['x']} {run['error']}")
    for st in run["stages"]:
        name = st["name"].ljust(18)
        if st["status"] == "success":
            extra = []
            if "coverage" in st:
                extra.append(f"couverture {st['coverage']} %")
            if "env" in st:
                extra.append(f"{st['env']} -> {st['release']}")
            print(f"  {c['g']}[OK]{c['x']} {name}{st['duration']:>5.1f} s  {c['d']}{' · '.join(extra)}{c['x']}")
        elif st["status"] == "failed":
            print(f"  {c['r']}[KO]{c['x']} {name}{st['duration']:>5.1f} s")
            if verbose_failures:
                lines = [ln for ln in st["log"].strip().splitlines() if ln.strip()][-12:]
                for ln in lines:
                    print(f"       {c['d']}{ln}{c['x']}")
        else:
            print(f"  {c['y']}[--]{c['x']} {name}  ignorée : {st.get('reason', '')}")
    if run["status"] == "success":
        print(f"{c['g']}{c['b']}Résultat : SUCCÈS{c['x']}  ({run['duration']} s)")
    else:
        print(f"{c['r']}{c['b']}Résultat : ÉCHEC{c['x']}  ({run['duration']} s)")
    print(f"{c['d']}Page de suivi : .pipeline/status.html{c['x']}")
