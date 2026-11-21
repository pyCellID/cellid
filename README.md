# cellid

Código fuente de **Cell-ID**, el programa de segmentación y cuantificación de células
en imágenes de microscopía (Gordon et al., *Nature Methods* 4:175-181, 2007), con
compilación, tests y CI. Es la fuente común para
[pyCellID](https://github.com/pyCellID/pyCellID) y
[rcell2-cellid](https://github.com/darksideoftheshmoo/rcell2-cellid).

## Origen

`src/` es una copia de Cell-ID 1.5.0 tal como está en `rcell2-cellid`
(`src/cellID`, commit `93e7f09`, 26/06/2025), sin modificaciones.

## Compilar y testear

Dependencias (Debian/Ubuntu): `sudo apt install build-essential libtiff-dev zlib1g-dev`

```bash
make          # compila ./cell
make test     # corre los tests
./cell -h     # ayuda del programa
```

## Tests

`make test` corre:

- `tests/test_smoke.sh`: Cell-ID encuentra las 25 células de una imagen sintética.
- `tests/test_golden.sh`: `out_all` coincide con la referencia guardada (mismas filas y columnas; números con tolerancia relativa de 1e-5).
- `tests/test_threshold.sh`: los umbrales de segmentación se calculan en doble precisión
  (detecta la versión con `float` de Cell-ID ≤ 1.4.6).

`make check-unchanged` verifica que `src/` compile al mismo código que `main`: sirve para
comprobar que un cambio solo agrega documentación.

Las imágenes de `tests/data/` y sus referencias se generan con `tests/generar_datos.py`.

## Documentación

`make docs` genera el manual en HTML con Doxygen (`docs/build/html/index.html`), con todas
las funciones, sus gráficos de llamadas y la lista de errores conocidos (*Bug List*).
Requiere `doxygen` y `graphviz`.

## Cómo contribuir

Ver `CONTRIBUTING.md`: estilo de código, documentación y tests.

## Ejercicios de C

`ejercicios/` contiene ejercicios para aprender C con el propio código de Cell-ID.
No forman parte del CI.

- `01_vecinos`: reescribir `neighboring_points()` (`make ejercicio1`).

## Problemas conocidos

- `neighboring_points()` (`src/segment.c`) no cuenta los vecinos diagonales de la fila
  de abajo y cuenta tres veces el de abajo. Está presente desde la versión 1.0 y afecta el
  trazado de contornos. Se mantiene sin corregir porque es el comportamiento de referencia.

## Licencia

GNU LGPL 2.1 (ver `LICENSE`), como el código original de Cell-ID.
