/*
 * Tests del ejercicio 1.
 *
 * Cada caso es una imagen chica de 0 y 1. Se cuenta cuántos vecinos del
 * píxel (x, y) valen 1 y se compara con el valor esperado.
 * Los mismos casos se aplican a tu función y a la original de Cell-ID.
 */
#include <stdio.h>
#include "vecinos.h"

typedef int (*contador)(const int *, int, int, int, int, int);

typedef struct {
    const char *nombre;
    int xmax, ymax;
    int d[9];
    int x, y;
    int esperado;
} caso;

static const caso CASOS[] = {
    /* 3x3, píxel central (1,1) */
    {"todos los vecinos",       3, 3, {1,1,1, 1,0,1, 1,1,1}, 1, 1, 8},
    {"sin vecinos",             3, 3, {0,0,0, 0,0,0, 0,0,0}, 1, 1, 0},
    {"solo arriba",             3, 3, {0,1,0, 0,0,0, 0,0,0}, 1, 1, 1},
    {"solo arriba-izquierda",   3, 3, {1,0,0, 0,0,0, 0,0,0}, 1, 1, 1},
    {"solo izquierda",          3, 3, {0,0,0, 1,0,0, 0,0,0}, 1, 1, 1},
    {"solo abajo",              3, 3, {0,0,0, 0,0,0, 0,1,0}, 1, 1, 1},
    {"solo abajo-derecha",      3, 3, {0,0,0, 0,0,0, 0,0,1}, 1, 1, 1},
    {"solo abajo-izquierda",    3, 3, {0,0,0, 0,0,0, 1,0,0}, 1, 1, 1},
    {"fila de abajo completa",  3, 3, {0,0,0, 0,0,0, 1,1,1}, 1, 1, 3},
    /* bordes de la imagen */
    {"esquina (0,0)",           3, 3, {0,1,0, 1,1,0, 0,0,0}, 0, 0, 3},
    {"borde inferior (1,2)",    3, 3, {0,0,0, 1,1,1, 1,0,1}, 1, 2, 5},
    {"imagen de 1 píxel",       1, 1, {1},                   0, 0, 0},
};
static const int N_CASOS = sizeof(CASOS) / sizeof(CASOS[0]);

static int probar(const char *titulo, contador f)
{
    int fallas = 0;
    printf("\n== %s ==\n", titulo);
    for (int i = 0; i < N_CASOS; i++) {
        const caso *c = &CASOS[i];
        int obtenido = f(c->d, c->xmax, c->ymax, c->x, c->y, 1);
        if (obtenido == c->esperado) {
            printf("  OK     %-24s %d\n", c->nombre, obtenido);
        } else {
            printf("  FALLA  %-24s esperado %d, obtenido %d\n", c->nombre, c->esperado, obtenido);
            fallas++;
        }
    }
    printf("  %d de %d casos correctos\n", N_CASOS - fallas, N_CASOS);
    return fallas;
}

int main(void)
{
    int fallas = probar("Tu función: contar_vecinos()", contar_vecinos);
    probar("Cell-ID 1.5.0: neighboring_points() (referencia, no cuenta como falla)",
           original_neighboring_points);
    return fallas == 0 ? 0 : 1;
}
