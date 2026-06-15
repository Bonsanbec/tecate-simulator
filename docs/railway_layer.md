# Capa Ferroviaria Incremental — Documentación Técnica

Ver: `src/minecraft_pipeline/railway_layer.py`

## Resumen

Implementa el Ferrocarril de Tecate como una capa incremental que se aplica sobre
regiones MCA ya generadas sin regenerar el terreno, el agua, las vialidades ni las manzanas.

Reutiliza el 100 % de los mecanismos arquitectónicos del pipeline de vialidades.
