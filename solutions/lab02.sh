#!/usr/bin/env bash
# Solution du lab 02 — à exécuter dans workspace/lab02
set -e
sed -i.bak 's|pourcentage / 10), 2)|pourcentage / 100), 2)|' src/prix.py && rm -f src/prix.py.bak
git commit -q -am "Corrige la remise : diviser le pourcentage par 100"
