/*
 * Tests del ejercicio 2.
 *
 * Genera imágenes de prueba con valores parecidos a los de un campo claro real
 * (alrededor de 36000, con desvío cercano a 9000) y calcula el valor exacto de
 * la media y el desvío con long double en dos pasadas. Después compara cada
 * método contra ese valor exacto y muestra el error relativo.
 *
 * Solo estadisticas_double() y estadisticas_welford() tienen que pasar:
 * float y el original se muestran para comparar.
 */
#include <math.h>
#include <stdio.h>
#include <stdlib.h>

#include "umbral.h"

typedef void (*metodo)(const float *, int, double *, double *);

/* Generador de números pseudoaleatorios simple y reproducible (xorshift). */
static unsigned long long estado = 88172645463325252ULL;

static double uniforme(void)
{
    estado ^= estado << 13;
    estado ^= estado >> 7;
    estado ^= estado << 17;
    return (estado >> 11) * (1.0 / 9007199254740992.0);
}

/* Aproximación de una normal estándar: suma de 12 uniformes menos 6. */
static double normal(void)
{
    double s = 0.0;
    for (int i = 0; i < 12; i++) {
        s += uniforme();
    }
    return s - 6.0;
}

/* Valores enteros (como los de una cámara de 16 bits) con media y desvío dados. */
static void generar(float *x, int n, double media, double desvio)
{
    for (int i = 0; i < n; i++) {
        double v = round(media + desvio * normal());
        if (v < 1.0) {
            v = 1.0;
        }
        x[i] = (float)v;
    }
}

/* Valor de referencia: long double y dos pasadas (sin cancelación). */
static void exacto(const float *x, int n, long double *media, long double *desvio)
{
    long double s = 0.0L;
    for (int i = 0; i < n; i++) {
        s += x[i];
    }
    long double m = s / n;
    long double ss = 0.0L;
    for (int i = 0; i < n; i++) {
        long double d = x[i] - m;
        ss += d * d;
    }
    *media = m;
    *desvio = sqrtl(ss / n);
}

static double error_relativo(double valor, long double referencia)
{
    return (double)fabsl((valor - referencia) / referencia);
}

/* Prueba un método sobre un conjunto de datos. Devuelve 1 si falla y debía pasar. */
static int probar(const char *nombre, metodo f, const float *x, int n, long double m_ref,
                  long double d_ref, int debe_pasar, double tolerancia)
{
    double m = 0.0;
    double d = 0.0;
    f(x, n, &m, &d);
    double em = error_relativo(m, m_ref);
    double ed = error_relativo(d, d_ref);
    int ok = em <= tolerancia && ed <= tolerancia;
    const char *estado_txt = debe_pasar ? (ok ? "OK   " : "FALLA") : "     ";
    printf("  %s %-10s media %.6f (error %.1e)   desvío %.6f (error %.1e)\n", estado_txt, nombre, m,
           em, d, ed);
    return debe_pasar && !ok;
}

static int caso(const char *titulo, int n, double media, double desvio)
{
    float *x = malloc((size_t)n * sizeof(float));
    if (x == NULL) {
        printf("No hay memoria para %d valores\n", n);
        return 1;
    }
    generar(x, n, media, desvio);
    long double m_ref = 0.0L;
    long double d_ref = 0.0L;
    exacto(x, n, &m_ref, &d_ref);

    printf("\n== %s (n = %d) ==\n", titulo, n);
    printf("  referencia  media %.6Lf                  desvío %.6Lf\n", m_ref, d_ref);
    int fallas = 0;
    probar("float", estadisticas_float, x, n, m_ref, d_ref, 0, 1e-9);
    /* En el caso de valores enormes, double en una pasada no tiene por qué pasar */
    int double_debe_pasar = desvio > 100.0;
    fallas += probar("double", estadisticas_double, x, n, m_ref, d_ref, double_debe_pasar, 1e-9);
    fallas += probar("welford", estadisticas_welford, x, n, m_ref, d_ref, 1, 1e-9);
    probar("welford_float", estadisticas_welford_float, x, n, m_ref, d_ref, 0, 1e-9);
    probar("original", original_calculate_cut, x, n, m_ref, d_ref, 0, 1e-9);
    free(x);
    return fallas;
}

int main(void)
{
    int fallas = 0;
    /* Como un campo claro: media 36000, desvío 9000, distintos tamaños de imagen */
    fallas += caso("Campo claro chico", 1000, 36000.0, 9000.0);
    fallas += caso("Campo claro 100x100", 10000, 36000.0, 9000.0);
    fallas += caso("Campo claro 512x512", 512 * 512, 36000.0, 9000.0);
    fallas += caso("Campo claro 1024x1024", 1024 * 1024, 36000.0, 9000.0);
    /* Cancelación catastrófica: valores enormes con muy poca variación */
    fallas += caso("Valores enormes y casi iguales", 512 * 512, 3.0e7, 2.0);

    printf("\n%s\n", fallas == 0 ? "Todos los métodos que debían pasar, pasaron."
                                 : "Hay métodos que debían pasar y fallaron.");
    return fallas == 0 ? 0 : 1;
}
