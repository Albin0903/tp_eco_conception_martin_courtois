#!/bin/bash
set -e

# Lancer le dump sans s'arrêter aux erreurs (ignore les warnings OWNER TO)
psql -v ON_ERROR_STOP=0 -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f /tmp/dump.sql

# Réinitialiser les séquences pour correspondre aux données existantes
psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" <<'SQL'
SELECT setval('pokemon_id_seq',         (SELECT COALESCE(MAX(id), 1) FROM pokemon));
SELECT setval('pokemon_species_id_seq', (SELECT COALESCE(MAX(id), 1) FROM pokemon_species));
SELECT setval('pokemon_colors_id_seq',  (SELECT COALESCE(MAX(id), 1) FROM pokemon_colors));
SELECT setval('pokemon_shapes_id_seq',  (SELECT COALESCE(MAX(id), 1) FROM pokemon_shapes));
SELECT setval('pokemon_types_id_seq',   (SELECT COALESCE(MAX(id), 1) FROM pokemon_types));
SELECT setval('types_id_seq',           (SELECT COALESCE(MAX(id), 1) FROM types));
SQL
