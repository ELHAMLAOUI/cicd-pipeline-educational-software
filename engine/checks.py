"""Bibliothèque de vérification des labs (utilisée par labs/labNN/check.py).

Chaque check.py déclare ses vérifications avec lab.check(points, description, indice, fonction).
La fonction renvoie True/False, ou (bool, détail). Le barème = somme des points déclarés :
une vérification qui ne peut pas s'exécuter compte 0 sans réduire le total.
"""
import datetime as _dt
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pipeline as eng  # noqa: E402


def _colors():
    if sys.stdout.isatty() and not os.environ.get("NO_COLOR"):
        return {"g": "\033[32m", "r": "\033[31m", "y": "\033[33m", "b": "\033[1m", "d": "\033[2m", "x": "\033[0m"}
    return dict.fromkeys("grybdx", "")


class Lab:
    def __init__(self, num, title):
        self.num, self.title = num, title
        self.ws = os.environ.get("PIPECTL_WORKSPACE") or os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "workspace", f"lab{num}")
        self.items = []

    def check(self, pts, desc, hint, fn):
        self.items.append((pts, desc, hint, fn))

    # ---------------------------------------------------- accès à l'espace de travail
    def exists(self):
        return os.path.isdir(os.path.join(self.ws, ".git"))

    def runs(self):
        return eng.load_runs(self.ws)

    def config(self):
        return eng.load_config(self.ws)

    def stage_cfg(self, name):
        for st in self.config()["stages"]:
            if st["name"] == name:
                return st
        return None

    def git(self, *args):
        return eng.git(self.ws, *args)

    def git_ok(self, *args):
        return subprocess.run(["git", "-C", self.ws, *args], capture_output=True).returncode == 0

    def head(self):
        return self.git("rev-parse", "HEAD")

    def read(self, rel):
        with open(os.path.join(self.ws, rel), encoding="utf-8") as fh:
            return fh.read()

    def meta(self):
        try:
            with open(os.path.join(self.ws, ".pipeline", "lab.json"), encoding="utf-8") as fh:
                return json.load(fh)
        except (OSError, ValueError):
            return {}

    def module(self, rel="src/prix.py"):
        """Importe le module de l'étudiant (version courante sur disque)."""
        spec = importlib.util.spec_from_file_location(f"m{len(self.items)}", os.path.join(self.ws, rel))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    def current(self, env):
        return eng.current_release(self.ws, env)

    def tests_fail_on_mutant(self, old, new, rel="src/prix.py"):
        """Test de mutation : copie l'espace de travail, introduit un défaut, les tests doivent échouer.
        old=None : « new » est ajouté en fin de fichier (redéfinit une fonction)."""
        tmp = tempfile.mkdtemp(prefix="mutant-")
        try:
            dst = os.path.join(tmp, "ws")
            shutil.copytree(self.ws, dst, ignore=shutil.ignore_patterns(".git", ".pipeline", "__pycache__"))
            p = os.path.join(dst, rel)
            with open(p, encoding="utf-8") as fh:
                src = fh.read()
            if old is None:  # ajout en fin de fichier (redéfinition d'une fonction)
                src += "\n\n" + new + "\n"
            elif old in src:
                src = src.replace(old, new, 1)
            else:
                return False, "code inattendu : mutation impossible"
            with open(p, "w", encoding="utf-8") as fh:
                fh.write(src)
            r = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-q"],
                               cwd=dst, capture_output=True, text=True, timeout=60)
            return r.returncode != 0, "le défaut introduit n'est détecté par aucun test"
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    # ---------------------------------------------------- exécution
    def run(self):
        c = _colors()
        print(f"\n{c['b']}Lab {self.num} — {self.title}{c['x']}")
        print(f"{c['d']}--------------------------------------------------------------{c['x']}")
        total = sum(p for p, *_ in self.items)
        pts, nb_ok, results = 0, 0, []
        present = self.exists()
        if not present:
            print(f"  {c['r']}[KO]{c['x']} Espace de travail absent")
            print(f"      {c['y']}Indice : lancez ./pipectl start {self.num}{c['x']}")
        else:
            for p, desc, hint, fn in self.items:
                try:
                    res = fn()
                    ok, detail = res if isinstance(res, tuple) else (bool(res), "")
                except Exception as e:  # noqa: BLE001
                    ok, detail = False, f"{type(e).__name__} : {e}"
                results.append({"description": desc, "points": p, "ok": bool(ok)})
                if ok:
                    pts += p
                    nb_ok += 1
                    print(f"  {c['g']}[OK]{c['x']} {desc} {c['d']}(+{p}){c['x']}")
                else:
                    print(f"  {c['r']}[KO]{c['x']} {desc} {c['d']}(0/{p}){c['x']}")
                    if detail:
                        print(f"      {c['d']}{detail}{c['x']}")
                    print(f"      {c['y']}Indice : {hint}{c['x']}")
        note = round(20 * pts / total, 1) if total else 0.0
        print(f"{c['d']}--------------------------------------------------------------{c['x']}")
        if present and nb_ok == len(self.items):
            print(f"{c['g']}{c['b']}Lab {self.num} réussi : {pts}/{total} points — note {note}/20{c['x']}")
        else:
            print(f"{c['y']}{c['b']}Lab {self.num} : {pts}/{total} points — note {note}/20 "
                  f"({nb_ok}/{len(self.items)} vérifications){c['x']}")
            print(f"{c['d']}Corrigez puis relancez : ./pipectl check {self.num}{c['x']}")
        rd = os.environ.get("RESULTS_DIR") or os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")
        os.makedirs(rd, exist_ok=True)
        with open(os.path.join(rd, f"lab{self.num}.json"), "w", encoding="utf-8") as fh:
            json.dump({"lab": self.num, "titre": self.title, "points": pts, "max": total, "note20": note,
                       "date": _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                       "checks": results}, fh, ensure_ascii=False)
        sys.exit(0 if present and nb_ok == len(self.items) else 1)


# ---------------------------------------------------- aides fréquentes

def stage(run, name):
    for s in run["stages"]:
        if s["name"] == name:
            return s
    return None


def commit_runs(runs):
    return [r for r in runs if r["trigger"] in ("commit", "merge")]
