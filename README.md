# GitHub Repo Discovery

Escanea un directorio base en busca de repositorios Git, detecta cuáles tienen remote en GitHub y los mueve a `github_repos/`.

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11+-blue)](https://python.org)

## Tabla de Contenidos

- [Características](#características)
- [Stack](#stack)
- [Estructura](#estructura)
- [Requisitos](#requisitos)
- [Instalación](#instalación)
- [Uso](#uso)
- [Tests](#tests)
- [Configuración](#configuración)
- [CI](#ci)
- [Limitaciones / Roadmap](#limitaciones--roadmap)
- [Licencia](#licencia)

## Características

- Escaneo recursivo de directorios buscando carpetas `.git`
- Detección de remote `origin` apuntando a GitHub
- Movimiento automático de repositorios a `github_repos/`
- Reporte resumen con estadísticas (totales, Git, GitHub, movidos)
- No requiere dependencias externas — solo standard library
- Manejo seguro de colisiones (no sobrescribe destinos existentes)

## Stack

- **Python 3.11+** (standard library: `os`, `shutil`, `subprocess`, `pathlib`)
- Sin dependencias externas
- Linting: Ruff | Tests: pytest

## Estructura

```
github-repo-discovery/
├── app.py              # CLI principal
├── pyproject.toml      # Configuración del proyecto
├── requirements.txt    # Dependencias (vacío, sin externas)
├── .env.example        # Variables de entorno placeholder
├── .github/
│   └── workflows/
│       └── ci.yml      # CI: Ruff + pytest
├── tests/
│   └── test_smoke.py   # Tests de humo
├── LICENSE
└── README.md
```

## Requisitos

- Python >= 3.11
- Git instalado en el sistema

## Instalación

```bash
git clone https://github.com/tu-usuario/github-repo-discovery.git
cd github-repo-discovery
# Sin dependencias externas — solo standard library
```

## Uso

```bash
python app.py /ruta/a/escanear
```

Ejemplo real:

```bash
python app.py /home/usuario/proyectos
```

El script imprime cada directorio revisado, detecta si es repo Git, obtiene la URL del remote, y mueve los repositorios con remote GitHub a `github_repos/`. Al final muestra un resumen:

```
[INFO] Revisando directorio base: /home/usuario/proyectos

[DIR] mi-proyecto
  [REMOTE] https://github.com/usuario/mi-proyecto.git
  [TYPE] Repo GitHub detectado
  [OK] Movido a: /home/usuario/proyectos/github_repos/mi-proyecto

[DIR] otro-repo
  [SKIP] No es repositorio Git

========== RESUMEN ==========
Directorios revisados: 10
Repos Git detectados: 5
Repos GitHub detectados: 3
Repos movidos: 3
Destino: /home/usuario/proyectos/github_repos
```

## Tests

```bash
# Instalar pytest
pip install pytest

# Ejecutar tests
python -m pytest tests/ -v
```

## Configuración

No requiere variables de entorno. El archivo `.env.example` es un placeholder sin configuración funcional.

## CI

GitHub Actions ejecuta Ruff linting y pytest en cada push y pull request:

```yaml
- name: Ruff check
  run: uv run ruff check .
- name: Pytest
  run: uv run pytest -q
```

## Limitaciones / Roadmap

- Solo mueve repos con remote `origin` apuntando a `github.com` (no soporta otros forges)
- No maneja repos con submodules
- No preserva atributos extendidos de archivos
- No soporta dry-run (simulación sin mover)
- Futuro: --dry-run, --include-gitlab, --parallel-scan

## Licencia

MIT
