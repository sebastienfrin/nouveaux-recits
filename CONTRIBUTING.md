# Guide de contribution

Merci de vouloir contribuer à **Nouveaux Récits d'Entreprise** ! Ce guide vous accompagne pas à pas, même si vous n'avez jamais utilisé GitHub.

## Pré-requis

- Un compte GitHub (gratuit) : [github.com/signup](https://github.com/signup)
- C'est tout !

## Ajouter un nouveau cas d'entreprise

### Étape 1 : Ouvrir le fichier de données

Cliquez sur le fichier `data/projects.json` dans la liste des fichiers du repo.

### Étape 2 : Passer en mode édition

Cliquez sur l'icône **✏️ crayon** en haut à droite du fichier.

### Étape 3 : Ajouter votre cas

Copiez le modèle ci-dessous et collez-le **juste avant le dernier `]`** du fichier. N'oubliez pas la virgule après l'accolade `}` du cas précédent.

```json
  ,
  {
    "id": 99,
    "company": "Nom de l'entreprise",
    "title": "Titre accrocheur résumant le projet",
    "sector": "Choisir parmi : Industrie lourde | Énergie | Transport | Agroalimentaire | Tech & Numérique | BTP & Immobilier | Finance | Mode & Textile",
    "region": "Choisir parmi : Europe | Amérique du Nord | Asie | Afrique | Amérique latine",
    "scope": "Choisir parmi : Scope 1 & 2 | Scope 3 | Net Zero",
    "source": "Choisir parmi : SBTi | CDP | Climate Action 100+ | ADEME | Rapports RSE",
    "country": "Pays",
    "countryFlag": "🇫🇷",
    "year": 2025,
    "logo": "Un emoji représentatif",
    "summary": "Résumé de 2-3 phrases. Contexte, actions clés, résultats chiffrés.",
    "actions": [
      "Action concrète 1 avec chiffres",
      "Action concrète 2 avec chiffres",
      "Action concrète 3 avec chiffres",
      "Action concrète 4 avec chiffres"
    ],
    "stats": [
      { "value": "-XX%", "label": "description courte", "color": "#059669" },
      { "value": "XX", "label": "description courte", "color": "#0284C7" },
      { "value": "XX", "label": "description courte", "color": "#7C3AED" }
    ],
    "target": "Objectif climat de l'entreprise",
    "difficulty": "Niveau et explication courte",
    "roi": "Impact économique positif",
    "sourceUrl": "https://lien-vers-la-source",
    "lastUpdated": "2025-04-25",
    "contributors": ["Votre prénom + initiale"],
    "verified": false
  }
```

### Étape 4 : Proposer votre modification

1. En bas de la page, dans **"Propose changes"**
2. Écrivez un titre court : ex. "Ajout cas Renault décarbonation usines"
3. Ajoutez une description si besoin
4. Cliquez sur **"Propose changes"**
5. Sur la page suivante, cliquez sur **"Create pull request"**

C'est fait ! L'équipe recevra une notification et validera sous 48h.

## Règles de qualité

- **Sources obligatoires** : chaque cas doit citer au moins une source vérifiable (rapport RSE, base SBTi/CDP, article de presse sérieux)
- **Chiffres datés** : préciser l'année de référence des données
- **Neutralité** : décrire les faits, pas faire de la publicité pour l'entreprise
- **Pas de greenwashing** : si les résultats sont partiels ou contestés, le mentionner

## Questions ?

Ouvrez une [Issue](../../issues/new) ou contactez l'équipe.
