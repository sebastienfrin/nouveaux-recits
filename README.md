# 🌱 Nouveaux Récits d'Entreprise

**La plateforme libre des trajectoires de décarbonation corporate qui fonctionnent.**

Cas réels, chiffrés, sourcés — pour inspirer professeurs, conférenciers et décideurs.

🌐 **Site** : [nouveaux-recits.eu](https://nouveaux-recits.eu)

---

## 🎯 C'est quoi ?

Une base de données ouverte et collaborative de cas concrets d'entreprises qui réussissent leur décarbonation. Chaque fiche contient :

- **L'entreprise** et son secteur
- **Les actions concrètes** menées
- **Les chiffres d'impact** vérifiés (émissions, ROI, emplois…)
- **La source** (SBTi, CDP, Climate Action 100+, ADEME…)
- **L'historique des contributions** (qui a écrit/modifié quoi)

## 🤝 Contribuer

### Ajouter un nouveau cas

1. Ouvrir le fichier `data/projects.json`
2. Cliquer sur l'icône ✏️ (crayon) en haut à droite
3. Copier-coller un cas existant à la fin du tableau
4. Modifier les informations (entreprise, chiffres, sources…)
5. Cliquer sur **"Propose changes"** en bas
6. Remplir un court message expliquant votre ajout
7. Cliquer sur **"Create pull request"**

L'équipe validera votre contribution sous 48h.

### Corriger une fiche existante

Même procédure — modifiez directement le champ concerné dans `data/projects.json`.

### Signaler une erreur

Ouvrir une [Issue](../../issues/new) en décrivant l'erreur et la source correcte.

## 🏗️ Architecture

```
nouveaux-recits/
├── index.html          ← Le site complet (fichier unique)
├── data/
│   └── projects.json   ← Les fiches projets (ce que vous modifiez)
├── README.md           ← Ce fichier
├── CONTRIBUTING.md     ← Guide de contribution détaillé
└── LICENSE             ← Licence CC BY-SA 4.0
```

**Zéro backend. Zéro base de données. Zéro coût d'hébergement.**

Le site est un fichier HTML unique qui charge les données depuis `projects.json`. Il est hébergé gratuitement sur Netlify et se met à jour automatiquement à chaque modification sur GitHub.

## 📊 Sources de données

| Source | Description | Accès |
|--------|------------|-------|
| **SBTi** | 10 000+ entreprises avec objectifs validés | [target-dashboard](https://sciencebasedtargets.org/target-dashboard) |
| **CDP** | Scores A-F, Open Data Portal | [data.cdp.net](https://data.cdp.net) |
| **Climate Action 100+** | 169 plus gros émetteurs évalués | [climateaction100.org](https://www.climateaction100.org) |
| **ADEME** | Base Carbone®, Plans de Transition Sectoriels | [data.ademe.fr](https://data.ademe.fr) |

## 📄 Licence

Contenu sous [Creative Commons BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) — libre de partage et d'adaptation, y compris à des fins commerciales, à condition de créditer et de partager sous la même licence.

## 💚 Projet pro bono

Ce projet est entièrement bénévole. Pas de publicité, pas de tracking, pas de cookies. Juste des récits qui donnent envie d'agir.
