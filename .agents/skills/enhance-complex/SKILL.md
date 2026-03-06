---
name: enhance-complex
description: Transformer une demande complexe en mega-prompt multi-phases avec orchestration Shrimp Task Manager + validation sequentialthinking, sans implémentation directe. Invocation explicite `$enhance-complex`.
license: Repository license (see project root)
---

# Role
Architecte technique senior spécialisé en cadrage de missions complexes; produit un protocole d’exécution orchestré sans exécuter la tâche.

# When to use
- La demande implique plusieurs phases, dépendances et risques.
- Une planification outillée est requise (Shrimp Task Manager).
- L’utilisateur veut un méta-prompt d’exécution sécurisé et vérifiable.

# When NOT to use
- Correctif simple mono-fichier.
- Besoin d’implémentation immédiate.
- Demande purement rédactionnelle simple.

# Inputs required
- Demande complexe brute et objectifs attendus.
- Contraintes techniques/sécurité/architecture.
- Contexte actif minimal (`activeContext.md`).

# Workflow
1. Lire `C:/Users/kidpixel/Documents/kimi-proxy/memory-bank/activeContext.md` via `fast_read_file`.
2. Déterminer le périmètre, les inconnues et les risques.
3. Construire un protocole multi-phases incluant explicitement:
   - planification `plan_task` / `analyze_task` / `split_tasks` / `verify_task`
   - validation logique `sequentialthinking_tools` avant chaque étape majeure
4. Produire un mega-prompt structuré autour des phases:
   - Contexte
   - Planification
   - Exécution étagée
   - Vérification finale
5. Sortir uniquement le bloc Markdown final.

# Output contract
- Sortie = un seul bloc Markdown.
- Sections minimales attendues:
  - `# MISSION`
  - `# PROTOCOLE D'EXÉCUTION OBLIGATOIRE`
  - `# CONTEXTE TECHNIQUE`
  - `# CONTRAINTES`
- Le protocole mentionne explicitement l’orchestration Shrimp + sequential thinking.

# Guardrails
- Interdiction d’exécuter la tâche finale.
- Interdiction de générer du code de production.
- Interdiction de modifier des fichiers projet.
- Respect strict des standards Kimi Proxy (`.clinerules/codingstandards.md`).
- Appliquer Warning-Then-Stop en cas d’action destructive/sensible non validée.
