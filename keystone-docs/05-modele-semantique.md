# Modèle sémantique

Un modèle sémantique dit ce que les colonnes veulent dire pour le métier : quelles valeurs on
additionne, selon quels axes on les découpe, sous quels noms on les cherche. ODCS 3.2.0 porte déjà
cette couche : le profil n'utilise que ses **champs natifs** et n'ajoute **aucune extension**.

## Ce qu'ODCS couvre déjà

| Notion | Champ ODCS |
| --- | --- |
| Rôle d'une colonne | `semanticType` : `column` (par défaut), `measure` ou `dimension` |
| Calcul d'une mesure | `transformLogic`, par exemple `SUM(an_amount)` ; un ratio s'écrit en une seule expression |
| Expression d'une dimension | `transformLogic`, par exemple `DATE_TRUNC('MONTH', a_date)` |
| Synonymes métier | `synonyms`, sur les tables et les colonnes |
| Relations entre tables | `relationships`, des clés étrangères |
| Nom métier, lien vers un glossaire | `businessName`, `authoritativeDefinitions` |

Les mesures et les dimensions sont des colonnes comme les autres, dans les `properties` de la
table.

## Les mesures

| Règle | Pourquoi |
| --- | --- |
| Une `measure` déclare son calcul dans `transformLogic` | ODCS y range l'agrégation mais ne l'exige pas : sans calcul, une mesure ne veut rien dire |
| Une `measure` est de type `number` ou `integer` | Une somme, un comptage ou un ratio donnent un nombre |

Une `dimension` sans `transformLogic` reste valide : elle désigne alors la colonne elle-même.

## Ce que le profil n'ajoute pas

- **Le grain** : la clé primaire donne les colonnes qui identifient une ligne, et la
  `description` de la table dit ce qu'elle représente.
- **Les jointures, les filtres et la matérialisation** : ODCS les laisse aux extensions propres
  à chaque outil. Le profil n'en définit pas.

## Ce que le profil ne vérifie pas

- Que le `transformLogic` d'une mesure est une expression SQL valide.
- Les mesures placées dans les propriétés imbriquées d'une colonne `object` ou `array`.

## Un exemple

```yaml
properties:
  - name: a_date
    logicalType: date
    description: The day of the row.
    semanticType: dimension
  - name: a_month
    logicalType: date
    description: The month of the row.
    semanticType: dimension
    transformLogic: DATE_TRUNC('MONTH', a_date)
  - name: an_amount
    logicalType: number
    description: The amount of the row.
  - name: total_amount
    logicalType: number
    description: The sum of the amounts.
    semanticType: measure
    transformLogic: SUM(an_amount)
```
