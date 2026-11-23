#include <math.h>

#include "umbral.h"

/*
 * EJERCICIO 2: completá las tres funciones.
 *
 * Las tres calculan lo mismo, la media y el desvío estándar poblacional:
 *
 *     media  = suma(x) / n
 *     desvio = sqrt( suma(x*x) / n  -  media*media )
 *
 * La diferencia está en el tipo de las variables que acumulan las sumas.
 * Los resultados se devuelven escribiendo en *media y *desvio.
 *
 * Probalas con:  make ejercicio2   (desde la raíz del repositorio)
 */

void estadisticas_float(const float *x, int n, double *media, double *desvio)
{

    float x_sum = 0;
    float x_sq = 0;

    for (int i = 0; i < n; i++) {
        x_sum += x[i];
        x_sq += x[i] * x[i];
    }

    float mean = x_sum / n;

    *media = mean;
    *desvio = sqrt(x_sq / n - mean * mean);
}

void estadisticas_double(const float *x, int n, double *media, double *desvio)
{
    double x_sum = 0;
    double x_sq = 0;

    for (int i = 0; i < n; i++) {
        double value_i = x[i];
        x_sum += value_i;
        x_sq += value_i * value_i;
    }

    double mean = x_sum / n;

    *media = mean;
    *desvio = sqrt(x_sq / n - mean * mean);
}

void estadisticas_welford(const float *x, int n, double *media, double *desvio)
{
    double s = 0;
    double mean = 0;

    for (int i = 0; i < n; i++) {
        int k = i + 1;
        double value_k = x[i];
        double delta = value_k - mean; /*Distancia a la media*/
        mean += delta / k;
        s += delta * (value_k - mean); /*(x₁ − media)² + (x₂ − media)² + ... + (xₙ − media)²*/
    }

    *media = mean;
    *desvio = sqrt(s / n);
}

void estadisticas_welford_float(const float *x, int n, double *media, double *desvio)
{
    float s = 0;
    float mean = 0;

    for (int i = 0; i < n; i++) {
        int k = i + 1;
        float value_k = x[i];
        float delta = value_k - mean; /*Distancia a la media*/
        mean += delta / k;
        s += delta * (value_k - mean); /*(x₁ − media)² + (x₂ − media)² + ... + (xₙ − media)²*/
    }

    *media = mean;
    *desvio = sqrtf(s / n);
}