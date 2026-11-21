#include "vecinos.h"

/*
 * Copia de neighboring_points() de Cell-ID 1.5.0 (src/segment.c), con dos
 * cambios para poder probarla sola: recibe d, xmax e ymax como parámetros
 * (en el original son variables globales) y se renombró.
 * La lógica, incluido el error en la fila de abajo, está intacta.
 */
int original_neighboring_points(const int *d, int xmax, int ymax, int x, int y, int v)
{
    int n;
    int u1, u2, u3;

    n = 0;

    u1 = y * xmax + x;
    u2 = u1 - xmax;
    u3 = u1 + xmax;

    if ((x + 1) < xmax) {
        if (d[u1 + 1] == v) {
            n++;
        }
    }
    if ((x - 1) >= 0) {
        if (d[u1 - 1] == v) {
            n++;
        }
    }

    if ((y - 1) >= 0) {
        if (d[u2] == v) {
            n++;
        }
        if ((x + 1) < xmax) {
            if (d[u2 + 1] == v) {
                n++;
            }
        }
        if ((x - 1) >= 0) {
            if (d[u2 - 1] == v) {
                n++;
            }
        }
    }

    if ((y + 1) < ymax) {
        if (d[u3] == v) {
            n++;
        }
        if ((x + 1) < xmax) {
            if (d[u3] == v) {
                n++;
            }
        }
        if ((x - 1) >= 0) {
            if (d[u3] == v) {
                n++;
            }
        }
    }

    return n;
}
