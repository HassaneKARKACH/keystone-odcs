# Propriétés exclues

Dans un profil, on ne supprime pas un champ d'ODCS : on l'**interdit**. Le contrat doit s'en
passer, et il reste un contrat ODCS valide. Le profil interdit deux sortes de champs : ceux
qu'ODCS a **dépréciés**, et ceux qu'aucun **processus** ne gouverne.

## Champs dépréciés

ODCS garde ses champs dépréciés pour la compatibilité, puis les retire. Un contrat qui les
utilise cassera le jour de ce retrait : le profil les refuse dès maintenant.

| Champ | Dans ODCS | À la place |
| --- | --- | --- |
| `dataProduct` | Déprécié depuis 3.1.0 | Rien |
| `slaDefaultElement` | Déprécié depuis 3.1, retrait prévu en 4.0 | `element` dans `slaProperties` |
| `rule` d'une règle qualité `library` | Déprécié | `metric`, déjà obligatoire |

Le format tableau de `team`, lui aussi déprécié, est déjà refusé par les
[propriétés affinées](01-proprietes-affinees.md) : le profil exige `team` au format objet.

## Le prix

Le bloc `price` donne le prix d'abonnement à un jeu de données : un montant, une devise et une
unité. Il suppose un processus de refacturation entre équipes. Sans ce processus, le prix est
une promesse que personne ne tient : le profil interdit le bloc.

## Ce que le profil ne vérifie pas

Le champ `rule` est cherché dans les règles qualité de la table et de ses colonnes, pas dans
les propriétés imbriquées dans une colonne `object` ou `array`.
