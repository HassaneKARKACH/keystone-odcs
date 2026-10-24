# keystone-odcs — Brief projet

> *An opinionated ODCS profile: fine-tuned and trimmed fields, plus extensions for data
> processing and semantic modeling — still 100 % ODCS-compliant.*

Projet personnel de portfolio (GitHub : `HassaneKARKACH/keystone-odcs`), orienté **Data Architecte**.

---

## 1. Objectif

Montrer **comment adapter un standard ouvert — l'Open Data Contract Standard (ODCS) — en un
standard maison**, sans le casser.

Le projet doit répondre à une question d'architecte :

> Comment une organisation encadre-t-elle l'usage d'ODCS (ce qu'elle exige, ce qu'elle
> interdit, ce qu'elle ajoute), tout en restant compatible avec l'écosystème du standard ?

La valeur du projet est dans **la conception et la justification des choix** (spécification +
ADR). Le code (schéma, validateur) ne sert qu'à appliquer le standard et à prouver qu'il tient.

---

## 2. Principe directeur : un *profil*, pas un fork

**Tout contrat conforme à Keystone est un contrat ODCS valide.**

- Keystone **restreint** ODCS : champs rendus obligatoires, énumérations réduites, conventions,
  champs interdits.
- Keystone **étend** ODCS uniquement par les mécanismes prévus par le standard
  (`customProperties`).
- Keystone ne **contredit** jamais ODCS : pas de champ renommé, pas de sémantique détournée.
- Le schéma JSON officiel d'ODCS est embarqué **tel quel, non modifié**.

Analogies : profils FHIR (santé), extensions `x-` d'OpenAPI.

---

## 3. Les quatre axes du standard maison

### Axe 1 — Affiner des propriétés

Durcir ce qu'ODCS laisse optionnel ou ouvert. Pistes :

- rendre obligatoires : `description`, owner / équipe, `classification`, contact support ;
- restreindre des énumérations : sous-ensemble de `logicalType`, statuts autorisés, niveaux de
  classification ;
- imposer des conventions : identifiant `domaine.table`, colonnes en `snake_case`, format des
  `tags`.

### Axe 2 — Supprimer (interdire) des propriétés

Dans un profil, on ne supprime pas un champ du standard : on **l'interdit**. Le document reste
du ODCS, il n'utilise simplement pas ce champ.

- Interdire les blocs non gouvernés dans l'organisation (ex. pricing, certains types de
  serveurs).
- Chaque exclusion est **justifiée** (ADR) : « pas de processus pour ça chez nous, donc pas de
  promesse vide dans les contrats ».

### Axe 3 — Extension « traitement de données »

Propriétés custom décrivant **comment la table est alimentée** :

- mode de chargement : append / overwrite / incrémental (colonne de watermark) / SCD2 ;
- fréquence ;
- partitionnement, clustering ;
- fraîcheur attendue ;
- gestion des rejets.

Point à argumenter : la frontière entre le **quoi** (le contrat) et le **comment**
(l'orchestrateur). Qu'est-ce qui a sa place dans un contrat ?

### Axe 4 — Extension « modèle sémantique »

**Règle : utiliser au maximum les champs natifs d'ODCS ; n'ajouter des `customProperties`
que pour ce qui manque réellement.**

Ce que le standard couvre déjà :

| Notion sémantique | Champ ODCS natif |
|---|---|
| Entité | objet de `schema` + `businessName` + `description` |
| Attribut | `property` + `businessName`, `logicalType`, `examples`, `criticalDataElement` |
| Identifiant | `primaryKey` / `primaryKeyPosition` |
| Relations entre entités | `relationships` (depuis ODCS 3.1.0) |
| Lien glossaire / référentiel | `authoritativeDefinitions` |
| Classement | `tags`, `classification` |

Ce qui manque (→ extension minimale) :

- rôle d'une colonne : **mesure** ou **dimension** ;
- **agrégation** par défaut d'une mesure ;
- **grain** d'une entité ;
- **métriques** calculées (formule, grain).

Ne pas inventer une syntaxe isolée : s'aligner explicitement sur un standard voisin de couche
sémantique (dbt MetricFlow, Cube, Open Semantic Interchange) — choix à acter dans un ADR.

---

## 4. Livrables

1. **Spécification** du standard maison (`spec/`, Markdown, un exemple par règle).
2. **JSON Schema du profil** : `allOf [ODCS officiel] + restrictions + extensions`.
3. **Validateur** en ligne de commande (`keystone validate <fichier>`), qui distingue
   erreurs ODCS de base et erreurs Keystone.
4. **Exemples** sur un domaine fictif : `valid/` + `invalid/` (un contrat par règle
   enfreinte, nommé d'après la règle) — ils servent aussi de tests.
5. **ADR** : une décision forte = un fichier.
6. *(Optionnel, très parlant)* un **générateur** : contrat → DDL, modèle sémantique dbt ou
   fiche de documentation.
7. **CI** GitHub Actions : tests + validation des exemples à chaque push.

---

## 5. Structure du dépôt

Monorepo Python géré par **uv workspace**.

```text
keystone-odcs/
├── pyproject.toml              # racine du workspace ([tool.uv] package = false)
├── uv.lock
├── .python-version             # version épinglée pour le dev
├── README.md                   # thèse, architecture du profil, exemple, choix forts
├── LICENSE                     # Apache 2.0, comme ODCS
│
├── spec/                       # LE STANDARD MAISON (cœur du projet)
│   ├── 00-principes.md
│   ├── 01-proprietes-affinees.md
│   ├── 02-proprietes-exclues.md
│   ├── 03-extension-traitement.md
│   └── 04-modele-semantique.md
│
├── schemas/
│   ├── odcs-<version>.json     # schéma officiel, NON modifié
│   └── keystone-profile.json   # profil = ODCS + restrictions + extensions
│
├── examples/
│   ├── valid/
│   └── invalid/
│
├── adr/
│   ├── 0001-profil-et-non-fork.md
│   ├── 0002-version-odcs-ciblee.md
│   ├── 0003-ou-placer-les-extensions.md
│   └── ...
│
├── packages/
│   ├── keystone-core/          # bibliothèque : profil, règles, validation, rapport
│   │   └── src/keystone_core/
│   └── keystone-cli/           # application : commande `keystone`
│       └── src/keystone_cli/
│
├── tests/
└── .github/workflows/ci.yml
```

Choix structurants :

- `spec/` passe **avant** le code.
- Les exemples invalides **documentent et testent** chaque règle.
- Le schéma officiel reste **intact** : le profil s'appuie dessus.

### Initialisation (commandes)

```powershell
uv init --bare --pin-python --name keystone-odcs --vcs git --python 3.15 ./keystone-odcs
cd keystone-odcs

uv init --lib     --name keystone-core --python 3.15 packages/keystone-core
uv init --package --name keystone-cli  --python 3.15 packages/keystone-cli

uv add --package keystone-cli keystone-core
uv add --dev pytest
uv sync --all-packages
```

Puis, dans le `pyproject.toml` racine :

```toml
[tool.uv]
package = false
```

Notes :

- `.python-version` (épinglage) = version utilisée pour **développer** ; `requires-python`
  = **promesse** faite aux utilisateurs. On peut épingler 3.15 et promettre `>=3.12`, en
  testant la plage en CI.
- Si des dépendances n'ont pas encore de wheels pour Python 3.15, repli sur 3.14.

---

## 6. Règles du projet

- **Aucun élément client.** Le projet est conçu de zéro : pas de code, de schéma, de nom
  d'infrastructure, d'URL, de contrat réel ni de doc issus d'une mission.
- **Ne pas reprendre les noms ni la structure des propriétés maison d'un projet client**
  (ex. `secretRef`, `jdbcOptions`, `fileOptions`, `dataProcessing`, `clusteringKeys`,
  `customType`). L'extension Keystone est conçue avec son propre raisonnement.
- **Domaine fictif** uniquement pour les exemples.
- **Identité Git perso** : les commits partent avec `karkach.hassane@gmail.com` (règle
  `includeIf` sur `github.com/HassaneKARKACH/**` → `~/.gitconfig-perso`). Vérifier avec
  `git config user.email --show-origin` une fois le remote ajouté.

---

## 7. Décisions ouvertes

| Décision | Options / état |
|---|---|
| Version d'ODCS ciblée | dernière **stable** officielle : v3.1.0 au moment du cadrage — à revérifier sur le dépôt Bitol (une v3.2.0 circule) |
| Domaine fictif | vélos en libre-service · boulangerie en ligne · bibliothèque municipale |
| Standard sémantique de référence | dbt MetricFlow · Cube · Open Semantic Interchange |
| Langue du README / de la spec | FR · EN · les deux (EN recommandé pour la visibilité) |
| `requires-python` | `>=3.15` ou plage plus large (`>=3.12`) |

---

## 8. Prochaines étapes

1. Initialiser le dépôt (section 5) et créer le dépôt GitHub `HassaneKARKACH/keystone-odcs`.
2. Trancher la version d'ODCS et le domaine fictif.
3. Rédiger `spec/00-principes.md` et `adr/0001-profil-et-non-fork.md` (caler le ton et le
   niveau de détail).
4. Rédiger les axes 1 et 2 (`spec/01`, `spec/02`) + premiers exemples valides/invalides.
5. Construire `schemas/keystone-profile.json` et le validateur minimal.
6. Axes 3 et 4, puis CI, puis générateur optionnel.

---

## Références

- ODCS (Bitol / Linux Foundation) : <https://github.com/bitol-io/open-data-contract-standard>
- Annonce ODCS v3.1.0 : <https://bitol.io/bitol-announces-odcs-v3-1-0-stronger-smarter-and-stricter/>
