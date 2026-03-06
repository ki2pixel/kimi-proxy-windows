---
name: end-session
description: Clôturer une session en synchronisant la Memory Bank (activeContext/progress) selon le protocole projet. Invocation explicite `$end-session`.
license: Repository license (see project root)
---

# Role
Session closer et memory-bank synchronizer: finalise la session, met à jour le contexte actif et confirme l’état neutre.

# When to use
- Fin de session de travail.
- Besoin de synchroniser l’état courant dans Memory Bank.
- Clôture explicite demandée par l’utilisateur.

# When NOT to use
- Session en cours avec tâches non validées.
- Demande de développement/diagnostic encore active.
- Mise à jour memory-bank partielle en dehors d’une clôture.

# Inputs required
- Résumé des changements de la session.
- Fichiers modifiés/impacts clés.
- Décisions prises durant la session.

# Workflow
1. Lire uniquement:
   - `C:/Users/kidpixel/Documents/kimi-proxy/memory-bank/activeContext.md`
   - `C:/Users/kidpixel/Documents/kimi-proxy/memory-bank/progress.md`
2. Résumer la session courante et vérifier les points ouverts.
3. Mettre à jour la Memory Bank avec timestamps `[YYYY-MM-DD HH:MM:SS]` via édition ciblée.
4. Vérifier l’état final:
   - `progress.md` indique qu’il n’y a plus de tâche active.
   - `activeContext.md` revient à un état neutre.
5. Rendre un récapitulatif de clôture concis.

# Output contract
- Résumé de clôture de session.
- Confirmation explicite de synchronisation Memory Bank.
- Liste courte des principaux éléments finalisés.

# Guardrails
- Respect strict de `.clinerules/memorybankprotocol.md`.
- Lecture mémoire sélective (pas de chargement massif inutile).
- Pas de modifications hors Memory Bank dans ce workflow de clôture.
- Appliquer Warning-Then-Stop pour toute action destructive/sensible hors périmètre.
