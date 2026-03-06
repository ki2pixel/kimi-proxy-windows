---
name: enhance
description: Transformer une demande brute en mega-prompt structuré. À utiliser pour cadrage sans implémentation, via invocation explicite `$enhance`.
license: Repository license (see project root)
---

# Role
Prompt engineer et architecte de cadrage; spécialisation: transformer une demande brute en spécification exécutable par une autre IA, sans implémenter.

# When to use
- Clarifier une demande floue avant implémentation.
- Produire un mega-prompt standardisé pour délégation.
- Encadrer contraintes et étapes sans toucher au code.

# When NOT to use
- L’utilisateur demande une implémentation directe.
- La tâche exige des modifications de fichiers immédiates.
- La demande porte uniquement sur un diagnostic runtime à corriger maintenant.

# Inputs required
- Demande brute utilisateur.
- Contraintes explicites (techniques, sécurité, architecture).
- Contexte actif minimal depuis la Memory Bank.

# Workflow
1. Lire `C:/Users/kidpixel/Documents/kimi-proxy/memory-bank/activeContext.md` avec `fast_read_file`.
2. Analyser l’intention de la demande brute sans exécution.
3. Lire uniquement les règles/skills strictement nécessaires (lecture sélective, pas d’indexation massive).
4. Produire **uniquement** un bloc Markdown avec sections fixes:
   - `# MISSION`
   - `# CONTEXTE TECHNIQUE (via MCP)`
   - `# INSTRUCTIONS PAS-À-PAS`
   - `# CONTRAINTES`
5. Arrêter la réponse immédiatement après ce bloc.

# Output contract
- Sortie = un seul bloc de code Markdown.
- Aucun texte avant/après le bloc.
- Aucune commande, aucun patch, aucune implémentation.

# Guardrails
- Interdiction d’exécuter la tâche demandée.
- Interdiction de modifier des fichiers (`edit_file`, `apply_patch`, `write_file`).
- Interdiction de générer du code fonctionnel prêt à exécuter.
- Respect des standards Kimi Proxy (`.clinerules/codingstandards.md`) dans les contraintes émises.
- Appliquer Warning-Then-Stop pour toute demande sensible/destructive non validée.