# Qualité des données

Le bloc `quality` d'ODCS décrit les **tests** à exécuter sur les données : une requête, et le
résultat qu'elle doit renvoyer. Un test se place sur la table ou sur une colonne. ODCS en accepte
de plusieurs sortes et laisse presque tout optionnel. Le profil en encadre la **forme**, pour que
chaque test s'exécute tel quel et se lise clairement quand il échoue.

## Tout en SQL

ODCS connaît quatre types de tests :

| Type | Ce que c'est | Dans le profil |
| --- | --- | --- |
| `sql` | Une requête dont le résultat est comparé | Seul type accepté |
| `library` | Une métrique prédéfinie : `nullValues`, `rowCount`… | Refusé |
| `custom` | Un test propre à un outil : Soda, Great Expectations… | Refusé |
| `text` | Une phrase, qui ne s'exécute pas | Refusé |

Le moteur qui exécute les tests lit le SQL : tous les tests s'écrivent dans ce format, et il n'a
rien à traduire. Sans `type`, ODCS considère un test comme `library` : le profil exige donc
`type: sql`, écrit explicitement.

ODCS impose déjà à un test SQL une `query` et un seul opérateur de comparaison : `mustBe`,
`mustBeGreaterThan`, `mustBeBetween`…

## Nom et sévérité

| Champ | Règle | Pourquoi |
| --- | --- | --- |
| `name` | Obligatoire | L'alerte dit quel test a échoué |
| `severity` | `warning` ou `error` | `error` arrête le chargement, `warning` prévient seulement |

ODCS cite aussi `info` en exemple. Le profil ne le retient pas : une sévérité qui ne déclenche
rien n'a pas sa place dans un test.

`dimension`, le type de qualité testée parmi les sept valeurs d'ODCS, et `description` restent
optionnels.

## Ce que le profil ne vérifie pas

- La **requête** elle-même : sa syntaxe et son résultat ne se vérifient que sur la base.
- Les tests placés dans les propriétés imbriquées d'une colonne `object` ou `array`.

## Un test conforme

```yaml
quality:
  - name: a_table_is_not_empty
    severity: error
    type: sql
    query: SELECT COUNT(*) FROM a_table
    mustBeGreaterThan: 0
```
