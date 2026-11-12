# Agent sémantique

Un agent IA qui interroge une table sans consignes devine : ce que représente une ligne, l'unité
d'un montant, la question qu'on lui pose vraiment. Le profil part d'un principe, **data agentique
first** : chaque table doit pouvoir être interrogée par un agent. Il s'appuie sur le bloc `context`
natif d'ODCS et n'ajoute aucun champ.

https://github.com/user-attachments/assets/8365d32b-682c-43c0-877f-b0064c106b81

## Ce qu'ODCS prévoit

| Champ | Ce que c'est |
| --- | --- |
| `instructions` | Un texte libre qui dit à l'agent comment utiliser la table, comme un prompt système |
| `verifiedStatements` | Des questions métier. Sans `answer`, ce sont des exemples qui aident l'agent à écrire son SQL ; avec `answer`, l'agent renvoie cette réponse telle quelle quand on lui pose une question proche |
| `constraints` | Ce que l'agent ne doit pas faire |

ODCS accepte `context` sur le contrat et sur la table, et le laisse entièrement optionnel. Une
simple chaîne de caractères vaut `instructions`.

## Les règles

| Règle | Pourquoi |
| --- | --- |
| La table porte un `context` avec des `instructions` | Sans consignes, l'agent devine ce que la table veut dire |
| Le `context` contient au moins une question avec sa réponse dans `verifiedStatements` | Un exemple validé montre à l'agent ce qu'on peut demander et comment y répondre |

Un contrat ne décrit qu'une table : tout se place sur la table, et rien n'est exigé au niveau du
contrat. La forme courte en chaîne compte comme des `instructions`, mais elle ne porte pas de
question : seule, elle ne suffit pas.

**Une réponse décrit comment obtenir le résultat, pas le résultat lui-même.** L'agent la renvoie
telle quelle : un chiffre écrit dans la réponse deviendrait faux dès que les données changent.

```yaml
# Se périme : le total change tous les mois
answer: 1.2 million euros in October.

# Reste vraie
answer: Sum an_amount by month of a_date.
```

## Ce qui reste libre

- **Les autres questions** : elles peuvent rester sans réponse, comme simples exemples pour
  l'agent.
- **`constraints`** : toutes les tables n'ont pas d'interdit à écrire.

## Ce que le profil ne vérifie pas

Que les consignes, les questions et les réponses sont utiles : le validateur vérifie qu'elles
existent, pas ce qu'elles disent. `instructions: TODO` passe, comme une réponse qui donne un
chiffre au lieu d'une méthode.

## Un exemple

```yaml
schema:
  - name: a_table
    context:
      instructions: One row per example. Amounts are in euros, without taxes.
      verifiedStatements:
        - question: What is the total amount per month?
        - question: How many examples are there?
          answer: Count the rows of a_table.
      constraints:
        - constraint: Do not show a_column to users outside the team.
```
