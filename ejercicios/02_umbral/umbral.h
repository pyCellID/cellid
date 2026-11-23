#ifndef UMBRAL_H
#define UMBRAL_H

/**
 * @file umbral.h
 * @brief Ejercicio 2: media y desvío estándar de una imagen, como en calculate_cut().
 *
 * Las tres funciones reciben los mismos datos y devuelven la media y el desvío
 * estándar poblacional (dividido por n, como Cell-ID) a través de punteros.
 */

/**
 * @brief Media y desvío acumulando las sumas en float (como Cell-ID <= 1.4.6).
 *
 * @param x       Valores de los píxeles.
 * @param n       Cantidad de valores.
 * @param media   Dirección donde se guarda la media.
 * @param desvio  Dirección donde se guarda el desvío estándar.
 */
void estadisticas_float(const float *x, int n, double *media, double *desvio);

/**
 * @brief Media y desvío acumulando las sumas en double (como Cell-ID 1.5.0).
 *
 * Mismos parámetros que estadisticas_float().
 */
void estadisticas_double(const float *x, int n, double *media, double *desvio);

/**
 * @brief Media y desvío con el algoritmo de Welford (en una pasada, sin cancelación).
 *
 * Mismos parámetros que estadisticas_float().
 */
void estadisticas_welford(const float *x, int n, double *media, double *desvio);

/**
 * @brief Media y desvío con el algoritmo de Welford (utilizando float).
 *
 * Mismos parámetros que estadisticas_float().
 */
void estadisticas_welford_float(const float *x, int n, double *media, double *desvio);

/**
 * @brief El cálculo de calculate_cut() de Cell-ID 1.5.0, adaptado (original.c).
 *
 * Igual que el original: ignora los píxeles <= 0.1 y eleva al cuadrado en float
 * antes de pasar a double. Mismos parámetros que estadisticas_float().
 */
void original_calculate_cut(const float *x, int n, double *media, double *desvio);

#endif
