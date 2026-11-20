#ifndef VECINOS_H
#define VECINOS_H

/*
 * Cuenta cuántos de los 8 vecinos del píxel (x, y) valen v.
 *
 *   d     imagen de etiquetas, guardada como arreglo de UNA dimensión:
 *         el píxel (x, y) está en la posición d[y*xmax + x]
 *   xmax  ancho de la imagen (cantidad de columnas)
 *   ymax  alto de la imagen (cantidad de filas)
 *   v     valor que se busca (en Cell-ID, la etiqueta de una célula)
 *
 * Los vecinos que caen fuera de la imagen no se cuentan.
 */
int contar_vecinos(const int *d, int xmax, int ymax, int x, int y, int v);

/* La función original de Cell-ID 1.5.0, adaptada a la misma firma (original.c). */
int original_neighboring_points(const int *d, int xmax, int ymax, int x, int y, int v);

#endif
