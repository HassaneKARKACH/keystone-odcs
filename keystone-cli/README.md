# keystone-cli

Ligne de commande qui vérifie un contrat de données contre ODCS v3.2.0, puis contre le profil
Keystone. Toute la logique vient de `keystone-core`.

```console
$ keystone validate contrat.yaml
```

| Code de sortie | Sens |
| --- | --- |
| 0 | Contrat conforme : `Contract validated` |
| 1 | `Contract is not valid ODCS` ou `Contract breaks the Keystone profile`, puis une ligne par erreur |
| 2 | Fichier illisible ou YAML invalide |
