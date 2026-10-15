# Cómo correr tests y procesos en este repo

Ver la sección "Tests" del README.

- Una sola corrida de pytest a la vez, en una sola terminal, desde `kimun/`:
  `.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider --durations=10` (menos de 1 minuto).
- No usar `Start-Sleep` ni lanzar comandos nuevos para "esperar" a otra corrida: quedan en cola en la misma terminal y bloquean todo.
- Antes de una corrida nueva, cerrar terminales y procesos de fondo que sigan vivos y revisar que no queden procesos `python`.
- Para iterar, correr solo el archivo de tests que cambió.
- En tests que necesitan la demo, usar el fixture `cargada` de `test_cargar_demo.py` (carga una vez por módulo), no llamar `cargar_demo` en cada test.
- No dejar archivos de salida temporales en el repo.
