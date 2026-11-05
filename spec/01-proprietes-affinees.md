# Propriétés affinées

ODCS laisse la plupart de ses champs optionnels et beaucoup de ses valeurs libres. Le profil
durcit ce cadre : il **exige** des champs, **ferme** des listes de valeurs et **impose** des
conventions. Ces règles s'appliquent à un contrat déjà valide ODCS : elles ne changent le sens
d'aucun champ, elles en demandent davantage.

## Champs obligatoires

ODCS n'exige que quatre champs : `apiVersion`, `kind`, `id` et `version`. Le profil en exige
d'autres, à chaque niveau du contrat.

**Contrat**

| Champ | Règle | Pourquoi |
| --- | --- | --- |
| `name` | Obligatoire | Il porte le nom de la table décrite |
| `domain` | Obligatoire | Il rattache le contrat à un domaine métier |
| `status` | Obligatoire, parmi les valeurs autorisées | Il dit au consommateur s'il peut s'appuyer sur le contrat |
| `team` | Au format objet, avec un `name` et au moins un membre de rôle `owner` | ODCS n'a pas de champ « owner » : le rôle `owner` en tient lieu. L'ancien format tableau, déprécié depuis ODCS 3.1.0, est refusé |
| `schema` | Exactement une table | Un contrat décrit une table, et une seule |

**Table**

| Champ | Règle | Pourquoi |
| --- | --- | --- |
| `physicalName` | Obligatoire | C'est le nom de la table dans la base, et l'identifiant du contrat |
| `description` | Obligatoire | Elle dit ce que représente une ligne |

**Colonne**

| Champ | Règle | Pourquoi |
| --- | --- | --- |
| `logicalType` | Obligatoire | Il donne le type de la valeur, indépendamment de la base |
| `description` | Obligatoire | Elle dit ce que contient la colonne |

## Valeurs de `status`

Pour ODCS, `status` est un texte libre. Le profil n'accepte que trois valeurs, en minuscules :

| Valeur | Ce qu'elle dit au consommateur |
| --- | --- |
| `draft` | Le contrat peut encore changer : ne pas en dépendre |
| `active` | On peut s'appuyer dessus en production |
| `deprecated` | Les données sont encore servies mais vont s'arrêter : migrer |

ODCS cite aussi `proposed` et `retired` en exemple. Le profil ne les retient pas : pour un
consommateur, `proposed` dit la même chose que `draft`, et quand les données disparaissent, le
contrat est supprimé.

## Règles de cohérence

- **L'`id` du contrat, son `name` et le `physicalName` de sa table sont identiques.** On retrouve
  ainsi un contrat par le nom de sa table.
- **Si la table porte un `id`, il est égal à son `name`.** ODCS désigne une colonne soit par les
  noms, soit par les `id` : les deux notations mènent alors au même endroit.
- **Une colonne `primaryKey: true` déclare `required: true`.** ODCS ne lie pas les deux champs,
  et `required` vaut `false` par défaut : sans cette règle, une clé primaire peut être nulle.

## Nommage

Les noms du contrat, de la table et des colonnes sont en **`snake_case`** : lettres minuscules et
chiffres, mots séparés par un seul `_`, en commençant par une lettre. L'`id` du contrat et le
`physicalName` de la table, qui portent le même nom, le sont aussi.

Le nom physique d'une table sert d'identifiant : il est **unique dans toute l'organisation**,
sans préfixe de domaine.

## Ce que le profil ne vérifie pas

Le validateur lit un contrat à la fois. Il ne vérifie donc pas :

- l'**unicité des noms physiques** entre contrats ;
- l'**évolution d'un contrat** d'une version à l'autre, par exemple un passage de `active` à
  `draft`.

Les règles de colonne portent sur les colonnes de la table, pas sur les propriétés imbriquées
dans une colonne `object` ou `array`.

## Un contrat conforme

Il porte aussi la fréquence et le mode de chargement qu'exige
l'[extension « traitement de données »](03-extension-traitement.md).

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
schema:
  - name: a_table
    physicalName: a_table
    description: One row per example.
    customProperties:
      - property: loadMode
        vendor: db-keystone
        value: overwrite
    properties:
      - name: a_column
        logicalType: string
        description: The key of an example.
        primaryKey: true
        required: true
```
