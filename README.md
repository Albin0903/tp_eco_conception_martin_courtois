# TP Éco-Conception : API REST Pokémon

Albin Martin, Hugo Courtois, Fazia Mahmoud

Polytech Lyon, Info 5A

Nous avons opté pour une stack moderne :

*   **Langage :** Python 3.12
*   **Framework API :** FastAPI (hautes performances, validation automatique avec Pydantic)
*   **Base de données :** PostgreSQL 17
*   **ORM Asynchrone :** SQLAlchemy + `asyncpg` (driver asynchrone pour maximiser la concurrence I/O)
*   **Sérialisation Rapide :** `ORJSON` (remplace le sérialiseur JSON standard pour plus de vitesse)
*   **Conteneurisation :** Docker

## Lancement

Pour démarrer l'app :

```bash
docker compose up --build -d
```

L'API accessible sur [http://localhost:8000](http://localhost:8000).