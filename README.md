# Keystone ODCS

Monorepo uv qui regroupe :

| Paquet | Rôle |
| --- | --- |
| `keystone-core` | Librairie cœur (module `keystone_core`) |
| `keystone-cli` | Ligne de commande `keystone` (module `keystone_cli`) |

## Installation

```console
$ uv sync --all-packages
```

`--all-packages` installe tous les paquets du workspace ; sans lui, `uv sync` ne garde que la racine et
ses dépendances de dev.

## Dépendances

Tout se gère depuis la racine, avec un seul `uv.lock` :

```console
$ uv add --package keystone-core <dépendance>   # dépendance d'un paquet
$ uv add --dev <outil>                          # outil de dev partagé
```

## Utilisation

```console
$ uv run keystone
$ uv run pytest
```
