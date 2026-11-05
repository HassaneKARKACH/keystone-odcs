# Extension « traitement de données »

Un consommateur ne lit pas une table de la même façon selon qu'elle est remplacée chaque nuit ou
complétée au fil de l'eau. Le contrat doit donc dire comment la table est alimentée. Toute la
question est de savoir **jusqu'où** : un contrat qui décrit le moteur et le planificateur devient
une configuration d'orchestrateur.

## La frontière entre le quoi et le comment

**Le contrat dit ce dont le consommateur dépend ; l'orchestrateur garde la façon de le produire.**

| Dans le contrat | Chez l'orchestrateur |
| --- | --- |
| Comment les lignes changent : le mode de chargement | Le moteur, le planificateur, les relances |
| Tous les combien : la fréquence | Le clustering, réglage physique propre au moteur |
| Avec quel retard : la fraîcheur | La gestion des rejets : les lignes perdues relèvent de la qualité |
| Comment lire vite : le partitionnement | Les connexions aux sources |

## Ce qu'ODCS couvre déjà

Le profil utilise d'abord les champs natifs d'ODCS.

| Besoin | Champ ODCS | Règle du profil |
| --- | --- | --- |
| Fréquence | `slaProperties`, `property: frequency` | Obligatoire, avec son `unit` |
| Fraîcheur | `slaProperties`, `property: latency` | Optionnelle ; si présente, un `unit` et un `element` qui est une colonne de la table |
| Partitionnement | `partitioned`, `partitionKeyPosition` sur les colonnes | Aucune |

```yaml
slaProperties:
  - property: frequency
    value: 1
    unit: d
  - property: latency
    value: 4
    unit: h
    element: updated_at
```

La **fréquence** dit au consommateur quand revenir, le **retard** lui dit si les données suffisent
à son usage. Une table chargée chaque matin avec les données de la veille a une fréquence d'un
jour, mais un retard qui peut atteindre trente heures.

Toute table chargée a une fréquence connue : l'exiger ne coûte rien. Un retard maximal est un
engagement qu'il faut surveiller : l'exiger partout produirait des promesses que personne ne
contrôle. Avec une seule table par contrat, `element` peut s'écrire avec ou sans le nom de la
table : `updated_at` ou `a_table.updated_at`.

## L'extension `loadMode`

ODCS n'a pas de champ pour le mode de chargement. Le profil l'ajoute dans les `customProperties`
de la table, avec la propriété `loadMode`.

**Le `vendor`.** ODCS 3.2.0 ajoute à chaque `customProperty` un champ `vendor`, qui dit à quel
système elle appartient. Le profil signe ses propriétés d'un vendor par plateforme, de la forme
**`<plateforme>-keystone`** : `db-keystone` pour une table en base, `kafka-keystone` pour un topic.
Il ne lit que les propriétés dont le vendor finit par `-keystone`, et laisse les autres
`customProperties` à leurs outils.

| `loadMode` | Ce qu'il dit au consommateur | Règle |
| --- | --- | --- |
| `append` | Les lignes sont seulement ajoutées, jamais modifiées | Aucune |
| `overwrite` | La table est remplacée à chaque chargement, sans historique | Aucune |
| `incremental` | Les lignes nouvelles ou modifiées sont fusionnées sur la clé : on peut ne relire que ce qui a changé | Une clé primaire, et une `watermarkColumn` |

**La watermark.** En mode `incremental`, `watermarkColumn` nomme la colonne qui dit quand une ligne
a changé pour la dernière fois. C'est une colonne de la table, de type `date` ou `timestamp`. Elle
porte une date **technique** : une ligne corrigée trois jours plus tard garde sa date métier, mais
sa date de modification change. C'est pourquoi la watermark ne se confond pas avec l'`element` de
`latency`, qui peut être une date métier.

```yaml
customProperties:
  - property: loadMode
    vendor: db-keystone
    value: incremental
  - property: watermarkColumn
    vendor: db-keystone
    value: updated_at
```

## Ce que le profil ne vérifie pas

- Que les promesses sont **tenues** : la fréquence et le retard réels se mesurent en production,
  c'est du monitoring.
- Les **synonymes** des propriétés SLA : ODCS accepte `fy` pour `frequency` et `ly` pour
  `latency`, sans tenir compte de la casse. Le profil ne lit que les noms `frequency` et `latency`.
- Le **nom de la plateforme** dans le vendor : tout vendor qui finit par `-keystone` est lu.

## Un contrat conforme

```yaml
apiVersion: v3.2.0
kind: DataContract
id: a_table
name: a_table
version: 1.0.0
domain: example
status: active
team:
  name: a_team
  members:
    - username: a_user
      role: owner
slaProperties:
  - property: frequency
    value: 1
    unit: d
  - property: latency
    value: 4
    unit: h
    element: updated_at
schema:
  - name: a_table
    physicalName: a_table
    description: One row per example.
    customProperties:
      - property: loadMode
        vendor: db-keystone
        value: incremental
      - property: watermarkColumn
        vendor: db-keystone
        value: updated_at
    properties:
      - name: a_column
        logicalType: string
        description: The key of an example.
        primaryKey: true
        required: true
      - name: updated_at
        logicalType: timestamp
        description: When the row last changed.
```
