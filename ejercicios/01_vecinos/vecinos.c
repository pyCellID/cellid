#include "vecinos.h"
#include "stdbool.h"

/*
 * EJERCICIO 1: completá esta función.
 *
 * Pistas:
 *  - Los 8 vecinos de (x, y) son (x+dx, y+dy) con dx y dy en {-1, 0, 1},
 *    salvo dx = dy = 0 (el propio píxel).
 *  - Antes de leer d[...], verificá que el vecino esté dentro de la imagen:
 *    0 <= columna < xmax  y  0 <= fila < ymax.
 *  - Recordá cómo se pasa de (columna, fila) a la posición en el arreglo.
 *
 * Probala con:  make ejercicio1   (desde la raíz del repositorio)
 */

/*
* Adición: creo una función auxilizar valid_pos:
* Devolverá ture si la posición está dentro de los límites
*/
static bool pos_valida(int x, int y, int xmax, int ymax){
    return x >= 0 && x < xmax && y >= 0 && y < ymax;
}


int contar_vecinos(const int *d, int xmax, int ymax, int x, int y, int v)
{
    int n = 0;
    
    for (int dy = -1; dy <= 1; dy++){        /*fila*/
        for (int dx = -1; dx <= 1; dx++){   /*columna*/
            if (dx == 0 && dy == 0){
                continue;
            }
            int vx = x + dx;
            int vy = y + dy;
            
            if (pos_valida(vx, vy, xmax, ymax) && d[vy*xmax+vx]== v){
                n++;
            }
        }
    }
    return n;
}
