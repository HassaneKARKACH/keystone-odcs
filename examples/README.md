# Exemples

Les exemples appliquent le profil au datalake de **Cyclomatic**, une enseigne fictive qui vend
des vélos en ligne et dans ses magasins.

https://github.com/user-attachments/assets/34564604-96fe-4c87-bfe3-ba32671cf92b

## Le cas d'usage

Cyclomatic charge dans son datalake les données de ses systèmes : la boutique en ligne, les
caisses des magasins, le référentiel produits, l'entrepôt et l'outil de relation client. L'équipe
**data-platform** copie ces sources telles quelles : ce sont les contrats d'**ingestion**. Les
équipes métier construisent ensuite, à partir de ces tables, les **produits de données** qu'utilisent
les analystes et les agents IA : ventes du jour, disponibilité en magasin, valeur client.

Chaque table a son contrat, conforme à ODCS et au profil Keystone.

## L'arborescence

```text
examples/
├── cyclomatic/
│   ├── ingestion/          une source copiée dans le datalake
│   ├── data-products/      une table construite dans le datalake
│   └── invalid/            un contrat valide, avec une seule erreur
├── simulate.py             un catalogue de données simulé, avec la bibliothèque keystone-core
├── validate_datalake.sh    la validation du datalake avec la commande keystone
└── validate_invalid.sh     les erreurs renvoyées sur les contrats invalides
```

## Les contrats d'ingestion

Une ingestion déclare deux serveurs : sa **source** et sa **destination**, le datalake Iceberg. Les
hôtes, ports, bases et schémas sont des variables `${...}`, résolues à l'exécution.

| Contrat | Source | Chargement | Fréquence |
| --- | --- | --- | --- |
| `raw_web_orders` | Boutique en ligne, `postgres` | `incremental` | Chaque heure |
| `raw_store_sales` | Caisses des magasins, `sqlserver` | `append` | Chaque jour |
| `raw_products` | Référentiel produits, `api` | `overwrite` | Chaque jour |
| `raw_stock_snapshots` | Entrepôt, fichiers `sftp` | `append` | Chaque jour |
| `raw_customers` | Relation client, `api` | `incremental` | Chaque jour |

## Les produits de données

Un produit de données déclare au plus un serveur : celui où il est construit, **BigQuery**. Ses
colonnes portent des mesures et des dimensions, et son contexte des questions pour les agents IA.

| Contrat | Équipe | Statut | Ce qu'il donne |
| --- | --- | --- | --- |
| `products` | catalog | `active` | La liste des produits, référence pour nommer un produit |
| `daily_sales` | sales-analytics | `active` | Le chiffre d'affaires et les unités vendues par jour, magasin et produit |
| `stock_availability` | supply-chain | `active` | Les unités disponibles par jour, magasin et produit |
| `customer_value` | customer-insights | `draft` | Ce que chaque client a acheté depuis son premier achat |

## Les contrats invalides

Chacun reprend `raw_products` ou `products` avec une seule erreur, et porte le nom de la règle
qu'il enfreint.

| Contrat | Règle enfreinte | Erreur |
| --- | --- | --- |
| `odcs_version_missing` | Un contrat a une `version` | ODCS |
| `status_not_allowed` | Un statut vaut `draft`, `active` ou `deprecated` | Keystone, affiner |
| `team_without_owner` | L'équipe a un membre de rôle `owner` | Keystone, affiner |
| `price_forbidden` | Le profil interdit `price` | Keystone, interdire |
| `ingestion_without_source` | Une ingestion déclare sa source | Keystone, traitement |
| `data_product_with_two_servers` | Un produit de données a au plus un serveur | Keystone, traitement |
| `quality_check_not_sql` | Un test qualité est écrit en SQL | Keystone, qualité |
| `measure_without_logic` | Une mesure déclare son calcul | Keystone, modèle sémantique |
| `question_without_answer` | Le contexte donne une question avec sa réponse | Keystone, agent sémantique |

## Les scripts

Ils se lancent depuis la racine du dépôt, après `uv sync --all-packages`.

```console
$ uv run python examples/simulate.py
$ bash examples/validate_datalake.sh
$ bash examples/validate_invalid.sh
```

`simulate.py` utilise la bibliothèque sans la CLI : un catalogue de données n'enregistre que les
contrats conformes, puis lit leur domaine, leur statut et leur owner sans les vérifier, puisque le
profil les garantit. Les scripts shell appellent la commande `keystone` sur chaque contrat :
`validate_datalake.sh` échoue si un contrat du datalake n'est pas conforme, `validate_invalid.sh`
affiche l'erreur de chaque contrat invalide.
