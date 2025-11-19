#!/usr/bin/env python3
"""pipectl — pilote du simulateur de pipeline CI/CD (labs guidés)."""
import argparse
import datetime as _dt
import importlib.util
import json
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
import webbrowser
import zipfile

ENGINE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(ENGINE)
LABS = os.path.join(ROOT, "labs")
sys.path.insert(0, ENGINE)

import pipeline as eng  # noqa: E402


def ws_root():
    return os.environ.get("PIPECTL_WORKSPACE_ROOT") or os.path.join(ROOT, "workspace")


def results_dir():
    return os.environ.get("RESULTS_DIR") or os.path.join(ROOT, "results")


def lab_ids():
    return sorted(d[3:] for d in os.listdir(LABS) if d.startswith("lab") and os.path.isdir(os.path.join(LABS, d)))


def norm(n):
    if not str(n).isdigit():
        sys.exit(f"Numéro de lab invalide : « {n} » (ex. : 01)")
    n = f"{int(n):02d}"
    if n not in lab_ids():
        sys.exit(f"Lab {n} introuvable. Voir : ./pipectl list")
    return n


def lab_module(n):
    spec = importlib.util.spec_from_file_location(f"lab{n}", os.path.join(LABS, f"lab{n}", "lab.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def workspace(n):
    return os.path.join(ws_root(), f"lab{n}")


# ----------------------------------------------------------------- outils pour les setup des labs

class Ctx:
    """Fonctions mises à disposition de setup() dans labs/labNN/lab.py."""

    def __init__(self, ws):
        self.ws = ws

    def git(self, *args):
        r = subprocess.run(["git", "-C", self.ws, *args], capture_output=True, text=True)
        if r.returncode != 0:
            raise RuntimeError(f"git {' '.join(args)} : {r.stderr.strip()}")
        return r.stdout.strip()

    def write(self, rel, text):
        p = os.path.join(self.ws, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as fh:
            fh.write(text)

    def read(self, rel):
        with open(os.path.join(self.ws, rel), encoding="utf-8") as fh:
            return fh.read()

    def replace(self, rel, old, new):
        txt = self.read(rel)
        if old not in txt:
            raise RuntimeError(f"motif introuvable dans {rel}")
        self.write(rel, txt.replace(old, new, 1))

    def commit(self, message):
        """Commit qui déclenche le hook (donc le pipeline), comme pour l'étudiant."""
        subprocess.run(["git", "-C", self.ws, "commit", "-q", "-am", message])
        return self.git("rev-parse", "HEAD")

    def run_pipeline(self, trigger="manual", show=True):
        run = eng.run_pipeline(self.ws, trigger)
        if show:
            eng.print_run(run)
        return run

    def save_meta(self, **kw):
        p = os.path.join(eng.pipeline_dir(self.ws), "lab.json")
        meta = {}
        if os.path.exists(p):
            with open(p, encoding="utf-8") as fh:
                meta = json.load(fh)
        meta.update(kw)
        with open(p, "w", encoding="utf-8") as fh:
            json.dump(meta, fh, indent=1)


HOOK = """#!/bin/sh
# Installé par pipectl : déclenche le pipeline CI/CD après chaque {event}.
exec {py} {pipectl} run --workspace "$(git rev-parse --show-toplevel)" --trigger {trigger}
"""


def install_hooks(ws):
    hooks = os.path.join(ws, ".git", "hooks")
    for name, event, trigger in (("post-commit", "commit", "commit"), ("post-merge", "fusion (merge)", "merge")):
        p = os.path.join(hooks, name)
        with open(p, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(HOOK.format(event=event, py=shlex.quote(sys.executable),
                                 pipectl=shlex.quote(os.path.join(ENGINE, "pipectl.py")), trigger=trigger))
        os.chmod(p, 0o755)


def copy_tree(src, dst):
    for dirpath, _, files in os.walk(src):
        rel = os.path.relpath(dirpath, src)
        if "__pycache__" in rel.split(os.sep):
            continue
        os.makedirs(os.path.join(dst, rel), exist_ok=True)
        for f in files:
            shutil.copy2(os.path.join(dirpath, f), os.path.join(dst, rel, f))


# ----------------------------------------------------------------- commandes

def cmd_list(_):
    for n in lab_ids():
        print(f"  {n}  {lab_module(n).TITLE}")


def cmd_start(a):
    n = norm(a.lab)
    ws = workspace(n)
    if os.path.exists(ws):
        sys.exit(f"Le lab {n} est déjà démarré ({ws}).\nPour repartir de zéro : ./pipectl reset {n}")
    os.makedirs(ws)
    copy_tree(os.path.join(LABS, "_app"), ws)
    files = os.path.join(LABS, f"lab{n}", "files")
    if os.path.isdir(files):
        copy_tree(files, ws)
    os.replace(os.path.join(ws, "gitignore"), os.path.join(ws, ".gitignore"))
    ctx = Ctx(ws)
    ctx.git("init", "-q")
    ctx.git("symbolic-ref", "HEAD", "refs/heads/main")
    if not subprocess.run(["git", "-C", ws, "config", "user.email"], capture_output=True, text=True).stdout.strip():
        ctx.git("config", "user.name", "Étudiant")
        ctx.git("config", "user.email", "etudiant@example.com")
    ctx.git("add", "-A")
    ctx.git("commit", "-q", "-m", "Version initiale")
    install_hooks(ws)
    ctx.save_meta(initial=ctx.git("rev-parse", "HEAD"))
    mod = lab_module(n)
    print(f"Lab {n} — {mod.TITLE}")
    print(f"Espace de travail : {os.path.relpath(ws, os.getcwd())}")
    if hasattr(mod, "setup"):
        mod.setup(ctx)
    from status_page import write_status_page
    write_status_page(ws, eng.load_runs(ws))
    print(f"\nLisez l'énoncé : labs/lab{n}/README.md")
    print(f"Puis : cd {os.path.relpath(ws, os.getcwd())}")


def cmd_run(a):
    ws = a.workspace or workspace(norm(a.lab))
    if not os.path.isdir(os.path.join(ws, ".git")):
        sys.exit("Espace de travail introuvable.")
    eng.print_run(eng.run_pipeline(ws, a.trigger))


def cmd_status(a):
    ws = workspace(norm(a.lab))
    runs = eng.load_runs(ws)
    if not runs:
        print("Aucun pipeline exécuté pour l'instant.")
        return
    print(f"{'#':>3}  {'Statut':<7} {'Commit':<8} {'Branche':<24} Étapes / message")
    for r in runs[-15:]:
        marks = " ".join({"success": "OK", "failed": "KO", "skipped": "--"}[s["status"]] + ":" + s["name"]
                         for s in r["stages"])
        print(f"{r['id']:>3}  {'SUCCÈS' if r['status'] == 'success' else 'ÉCHEC':<7} {r['short']:<8} "
              f"{r['branch'][:24]:<24} {marks}\n{'':>22}« {r['message']} »")
    envs = os.path.join(ws, ".pipeline", "env")
    if os.path.isdir(envs):
        print("\nEnvironnements :", ", ".join(f"{e} -> {eng.current_release(ws, e)}" for e in sorted(os.listdir(envs))))
    if a.last:
        eng.print_run(runs[-1])


def cmd_open(a):
    ws = workspace(norm(a.lab))
    page = os.path.join(ws, ".pipeline", "status.html")
    print(f"Page de suivi : {page}")
    try:
        webbrowser.open("file://" + os.path.abspath(page))
    except Exception:  # noqa: BLE001
        pass


def cmd_check(a):
    n = norm(a.lab)
    r = subprocess.run([sys.executable, os.path.join(LABS, f"lab{n}", "check.py")],
                       env=dict(os.environ, PIPECTL_WORKSPACE=workspace(n), RESULTS_DIR=results_dir()))
    return r.returncode


def cmd_hint(a):
    with open(os.path.join(LABS, f"lab{norm(a.lab)}", "hints.md"), encoding="utf-8") as fh:
        print(fh.read())


def cmd_reset(a):
    n = norm(a.lab)
    if os.path.exists(workspace(n)):
        shutil.rmtree(workspace(n))
    cmd_start(a)


def cmd_report(_):
    rd = results_dir()
    os.makedirs(rd, exist_ok=True)
    rows, tot, mx = [], 0, 0
    for n in lab_ids():
        f = os.path.join(rd, f"lab{n}.json")
        if os.path.exists(f):
            os.remove(f)
        cmd_check(argparse.Namespace(lab=n))
        if os.path.exists(f):
            with open(f, encoding="utf-8") as fh:
                d = json.load(fh)
            rows.append(f"{n};{d['titre']};{d['points']};{d['max']};{d['note20']}")
            tot += d["points"]
            mx += d["max"]
    note = round(20 * tot / mx, 1) if mx else 0
    with open(os.path.join(rd, "rapport.csv"), "w", encoding="utf-8") as fh:
        fh.write("lab;titre;points;max;note20\n" + "\n".join(rows) + f"\nTOTAL;;{tot};{mx};{note}\n")
    print(f"\nRapport global : {tot}/{mx} points — note {note}/20 ({os.path.join(rd, 'rapport.csv')})")


def cmd_pack(a):
    root = ws_root()
    if not os.path.isdir(root):
        sys.exit("Aucun lab démarré : rien à rendre.")
    name = a.output or f"rendu-{_dt.date.today().isoformat()}.zip"
    with zipfile.ZipFile(name, "w", zipfile.ZIP_DEFLATED) as z:
        for dirpath, _, files in os.walk(root):
            for f in files:
                p = os.path.join(dirpath, f)
                z.write(p, os.path.join("workspace", os.path.relpath(p, root)))
    print(f"Rendu créé : {name} (à déposer sur la plateforme du cours)")


def cmd_grade(a):
    tmp = tempfile.mkdtemp(prefix="pipectl-grade-")
    try:
        with zipfile.ZipFile(a.archive) as z:
            z.extractall(tmp)
        os.environ["PIPECTL_WORKSPACE_ROOT"] = os.path.join(tmp, "workspace")
        os.environ["RESULTS_DIR"] = a.results or os.path.join(os.getcwd(), "notes-" + os.path.splitext(
            os.path.basename(a.archive))[0])
        cmd_report(a)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def cmd_clean(_):
    if os.path.isdir(ws_root()):
        shutil.rmtree(ws_root())
    print("Espaces de travail supprimés.")


def main():
    try:
        sys.stdout.reconfigure(line_buffering=True)
    except AttributeError:
        pass
    p = argparse.ArgumentParser(prog="pipectl", description="Simulateur de pipeline CI/CD — labs guidés")
    sp = p.add_subparsers(dest="cmd", metavar="commande")
    for name, fn, help_ in (("start", cmd_start, "prépare l'espace de travail du lab"),
                            ("check", cmd_check, "vérifie le travail et donne une note sur 20"),
                            ("status", cmd_status, "historique des pipelines du lab"),
                            ("open", cmd_open, "ouvre la page de suivi dans le navigateur"),
                            ("hint", cmd_hint, "affiche les indices"),
                            ("reset", cmd_reset, "repart de zéro sur le lab")):
        s = sp.add_parser(name, help=help_)
        s.add_argument("lab")
        if name == "status":
            s.add_argument("--last", action="store_true", help="détaille le dernier pipeline")
        s.set_defaults(fn=fn)
    s = sp.add_parser("run", help="lance le pipeline à la main (sans commit)")
    s.add_argument("lab", nargs="?")
    s.add_argument("--workspace")
    s.add_argument("--trigger", default="manual")
    s.set_defaults(fn=cmd_run)
    sp.add_parser("list", help="liste les labs").set_defaults(fn=cmd_list)
    sp.add_parser("report", help="vérifie tous les labs -> results/rapport.csv").set_defaults(fn=cmd_report)
    s = sp.add_parser("pack", help="crée l'archive de rendu (tous les labs)")
    s.add_argument("-o", "--output")
    s.set_defaults(fn=cmd_pack)
    s = sp.add_parser("grade", help="(enseignant) note l'archive de rendu d'un étudiant")
    s.add_argument("archive")
    s.add_argument("--results")
    s.set_defaults(fn=cmd_grade)
    sp.add_parser("clean", help="supprime tous les espaces de travail").set_defaults(fn=cmd_clean)
    a = p.parse_args()
    if not a.cmd:
        p.print_help()
        return 0
    if a.cmd == "run" and not a.workspace and not a.lab:
        p.error("indiquez un numéro de lab")
    return a.fn(a) or 0


if __name__ == "__main__":
    sys.exit(main())
