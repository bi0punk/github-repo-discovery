#!/usr/bin/env python3
"""
Detecta repositorios Git/GitHub dentro de un directorio base
y mueve los que tengan remoto de GitHub a github_repos.

Uso:
    python3 mover_github_repos.py /ruta/directorio/base
"""

import sys
import shutil
import subprocess
from pathlib import Path


def es_repo_git(path: Path) -> bool:
    return (path / ".git").is_dir()


def obtener_remote_origin(path: Path) -> str:
    try:
        result = subprocess.run(
            ["git", "-C", str(path), "remote", "get-url", "origin"],
            capture_output=True,
            text=True,
            check=False
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return ""


def es_repo_github(remote: str) -> bool:
    return "github.com" in remote.lower()


def mover_repo(origen: Path, destino_base: Path) -> bool:
    destino = destino_base / origen.name

    if destino.exists():
        print(f"  [WARN] Ya existe en destino: {destino}")
        return False

    try:
        shutil.move(str(origen), str(destino))
        print(f"  [OK] Movido a: {destino}")
        return True
    except Exception as e:
        print(f"  [ERROR] No se pudo mover: {e}")
        return False


def main():
    if len(sys.argv) != 2:
        print("Uso: python3 mover_github_repos.py /ruta/directorio/base")
        sys.exit(1)

    base_dir = Path(sys.argv[1]).expanduser().resolve()

    if not base_dir.exists() or not base_dir.is_dir():
        print(f"[ERROR] Ruta inválida: {base_dir}")
        sys.exit(1)

    destino_base = base_dir / "github_repos"
    destino_base.mkdir(exist_ok=True)

    total = 0
    repos_git = 0
    repos_github = 0
    movidos = 0

    print(f"\n[INFO] Revisando directorio base: {base_dir}\n")

    for item in sorted(base_dir.iterdir()):
        if not item.is_dir():
            continue

        if item.name == "github_repos":
            continue

        total += 1
        print(f"[DIR] {item.name}")

        if not es_repo_git(item):
            print("  [SKIP] No es repositorio Git\n")
            continue

        repos_git += 1
        remote = obtener_remote_origin(item)

        if remote:
            print(f"  [REMOTE] {remote}")
        else:
            print("  [REMOTE] Sin remote origin configurado")

        if es_repo_github(remote):
            repos_github += 1
            print("  [TYPE] Repo GitHub detectado")
            if mover_repo(item, destino_base):
                movidos += 1
        else:
            print("  [SKIP] Repo Git, pero no GitHub")

        print()

    print("========== RESUMEN ==========")
    print(f"Directorios revisados: {total}")
    print(f"Repos Git detectados: {repos_git}")
    print(f"Repos GitHub detectados: {repos_github}")
    print(f"Repos movidos: {movidos}")
    print(f"Destino: {destino_base}")


if __name__ == "__main__":
    main()
