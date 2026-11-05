# keystone-core

Bibliothèque qui vérifie un contrat de données contre ODCS v3.2.0, puis contre les règles du
profil Keystone.

| Fonction | Rôle |
| --- | --- |
| `load_contract(path)` | Lit un contrat YAML ou JSON ; lève `ContractLoadError` si le fichier est illisible |
| `validate_odcs(contract)` | Vérifie le contrat contre le schéma officiel d'ODCS, embarqué sans modification |
| `validate_profile(contract)` | Vérifie un contrat déjà valide ODCS contre les règles du profil |

Les deux vérifications renvoient une liste de `Violation`, chacune avec un `path` et un
`message`. La liste est vide quand le contrat est conforme.
