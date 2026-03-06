---
name: commit-push
description: Préparer un commit et pousser la branche courante avec checks préalables, en mode non-interactif. Invocation explicite `$commit-push`.
license: Repository license (see project root)
---

# Role
Git workflow operator: sécuriser et exécuter le cycle add/commit/push sur la branche courante avec contrôle préalable.

# When to use
- L’utilisateur demande explicitement de commit/push des changements.
- Le diff est prêt et validé.
- Un enchaînement non-interactif est souhaité.

# When NOT to use
- Les changements ne sont pas revus.
- Le message de commit est ambigu ou absent.
- Le dépôt n’est pas prêt (conflits non résolus, tests critiques cassés sans validation explicite).

# Inputs required
- Message de commit (ou convention demandée).
- Politique de checks préalable (lint/tests/build).
- Confirmation explicite de l’utilisateur pour exécuter les commandes Git.

# Workflow
1. Vérifier l’état Git (`git status`, diff utile) et la branche courante.
2. Exécuter les checks demandés (lint/tests/build) si applicables.
3. Stager (`git add -A`).
4. Committer avec un message clair et conforme.
5. Pousser vers `origin` sur la branche courante (`git push -u origin <branch>`).
6. Rapporter le résultat (hash, branche, état push).

# Output contract
- Plan d’exécution clair avant commandes.
- Compte-rendu final avec commandes exécutées et résultat.
- En cas d’échec: diagnostic + étape de remédiation proposée.

# Guardrails
- Respecter le protocole sécurité: Warning-Then-Stop pour opérations sensibles.
- Ne jamais exposer de secrets (fichiers `.env`, clés API) dans commit ou sortie.
- Ne pas forcer `push --force` sans demande explicite.
- Pour opérations destructives Git, demander confirmation explicite.
