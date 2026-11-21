#ifndef VECINOS_H
#define VECINOS_H

/**
 * @file vecinos.h
 * @brief Ejercicio 1: contar los vecinos de un píxel que tienen un valor dado.
 */

/**
 * @brief Cuenta los vecinos de un píxel que tienen un valor dado.
 *
 * Revisa los 8 vecinos (vecindad de Moore) del píxel (x, y) y cuenta cuántos
 * valen v. Los vecinos que caen fuera de la imagen no se cuentan.
 *
 * @param d     Imagen de etiquetas guardada por filas: el píxel (x, y) está
 *              en d[y * xmax + x].
 * @param xmax  Ancho de la imagen (cantidad de columnas).
 * @param ymax  Alto de la imagen (cantidad de filas).
 * @param x     Columna del píxel.
 * @param y     Fila del píxel.
 * @param v     Valor buscado (en Cell-ID, la etiqueta de una célula).
 * @return      Cantidad de vecinos que valen v, entre 0 y 8.
 */
int contar_vecinos(const int *d, int xmax, int ymax, int x, int y, int v);

/**
 * @brief neighboring_points() de Cell-ID 1.5.0, adaptada a la misma firma.
 *
 * Copia del original (src/segment.c) que recibe la imagen y su tamaño como
 * parámetros en lugar de variables globales. Conserva el error del original.
 *
 * @bug No cuenta los vecinos diagonales de la fila de abajo y cuenta tres
 *      veces el de abajo.
 */
int original_neighboring_points(const int *d, int xmax, int ymax, int x, int y, int v);

#endif
