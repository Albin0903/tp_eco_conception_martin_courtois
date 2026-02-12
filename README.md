# TP Éco-Conception : API REST Pokémon

Albin Martin, Hugo Courtois, Fazia Mahmoud

Polytech Lyon, Info 5A

Nous avons opté pour une stack moderne, légère et performante :

*   **Langage :** Python 3.12 (optimisé pour la lisibilité et la rapidité de développement)
*   **Framework API :** FastAPI (hautes performances, validation automatique avec Pydantic)
*   **Base de données :** PostgreSQL 17 (robuste et standard industriel)
*   **ORM Asynchrone :** SQLAlchemy + `asyncpg` (driver asynchrone pour maximiser la concurrence I/O)
*   **Sérialisation Rapide :** `ORJSON` (remplace le sérialiseur JSON standard pour plus de vitesse)
*   **Conteneurisation :** Docker & Docker Compose (déploiement reproductible et isolé)

## Lancement

Pour démarrer l'application (API + Base de données) :

```bash
docker compose up --build -d
```

L'API sera accessible sur [http://localhost:8000](http://localhost:8000).