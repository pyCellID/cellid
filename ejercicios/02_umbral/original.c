#include <math.h>

#include "umbral.h"

/*
 * Núcleo de calculate_cut() de Cell-ID 1.5.0 (src/segment.c), adaptado para
 * probarlo solo: recibe los píxeles como parámetro en lugar del arreglo global
 * c[] y devuelve la media y el desvío en lugar de los umbrales. Se quitaron las
 * ramas de FRET. La aritmética es la del original:
 *   - ignora los píxeles con valor <= 0.1,
 *   - acumula en double, pero calcula tmp*tmp en float antes de convertirlo.
 */
void original_calculate_cut(const float *x, int n, double *media, double *desvio)
{
    double mu = 0.0;
    double sig = 0.0;
    double scale = 0.0;
    float tmp;

    for (int i = 0; i < n; i++) {
        tmp = x[i];
        if (tmp <= 0.1) {
            continue;
        }
        mu += (double)(tmp);
        sig += (double)(tmp * tmp);
        scale += 1.0;
    }
    mu /= scale;
    sig /= scale;
    sig = (float)sqrt((double)(sig - mu * mu));

    *media = mu;
    *desvio = sig;
}
