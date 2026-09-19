#include <math.h>
#include <stddef.h>
#define L 3
#define MAX(a,b) ((a)>(b)?(a):(b))
#define MIN(a,b) ((a)<(b)?(a):(b))
typedef ptrdiff_t npy_intp;
/*
# This file is part of the Astrometry.net suite.
# Licensed under a 3-clause BSD style license - see LICENSE
 */

// L must be defined before including this file; L=3 or L=5 in practice.

// Preprocessor magic to glue together function names with L (3 or 5)
#define MOREGLUE(x, y) x ## y
#define GLUE(x, y) MOREGLUE(x, y)
// and for 3 tokens
#define MOREGLUE3(x, y, z) x ## y ## z
#define GLUE3(x, y, z) MOREGLUE3(x, y, z)

// lanczos_kernelf_[L]
static
float GLUE(lanczos_kernelf_, L)(float x) {
    static const float pif = M_PI;
    static const float pi2f = M_PI * M_PI;
    if (x <= -L || x >= L)
        return 0.0;
    if (x == 0)
        return 1.0;
    return L * sinf(pif * x) * sinf(pif / L * x) / (pi2f * x * x);
}
#define lanczos_kernelf(L, x) GLUE(lanczos_kernelf_, L)(x)

// Nlutunit is number of bins per unit x
// NOTE that this is share across different L values.
#ifndef LANCZOS_NLUT
#define LANCZOS_NLUT 1024
#endif

// We add an extra row to LANCZOS_NLUT so that we can compute the
// slope across each bin.
static float (GLUE(lut_, L))[2*(L+1)*(LANCZOS_NLUT+1)];
// Have we initialized the Look-up Table?
static int GLUE(lut_initialized_,L) = 0;

// Init look-up table
static void GLUE(lut_init_, L)(void) {
    if (GLUE(lut_initialized_,L))
        return;
    /*
     dx,dy are in [-0.5, 0.5].

     Lanczos-3 kernel is zero outside [-3,3].

     We build a look-up table where [0] is L(-3.5).

     And organized so that:
     lut[0] = L(-3.5)
     lut[1] = L(-2.5)
     lut[2] = L(-1.5)
     lut[3] = L(-0.5)
     lut[4] = L( 0.5)
     lut[5] = L( 1.5)
     lut[6] = L( 2.5)
     lut[7] stores sum(lut[0:7])

     lut[8]  = L(-3.499)
     lut[9]  = L(-2.499)
     lut[10] = L(-1.499)
     ...
     ...
     lut[8184] = L(-2.501)
     lut[8185] = L(-1.501)
     lut[8186] = L(-0.501)
     ...

     This is annoying because [-3.5,3] and [3,3.5] are zero so we
     have to sum 7 elements rather than 6.  But the alternatives
     seem worse.

     LANCZOS_NLUT aka Nlutunit is number of bins per unit x.
     Nunits is the number of units, ie the support of the kernel.
     */
    static const float lut0 = -(L + 0.5);
    static const int Nunits = 2*(L+1);
    // this table has the elements you need to use together
    // stored together: L(x[0]), L(x[0]+1), L(x[0]+2), ...;
    // L(x[1]), L(x[1]+1), L(x[2]+2), ...
    int i, j;
    float* lut = GLUE(lut_,L);
    //for (i=0; i<=Nlutunit; i++) {
    for (i=0; i<=LANCZOS_NLUT; i++) {
        float x,f;
        float acc = 0.;
        //x = lut0 + i / (float)(Nlutunit);
        x = lut0 + i / (float)(LANCZOS_NLUT);
        for (j=0; j<Nunits; j++, x+=1.0) {
            f = lanczos_kernelf(L, x);
            lut[i * Nunits + j] = f;
            acc += f;
        }
        // last column contains the sum
        lut[i*Nunits + Nunits-1] = acc;
    }
}
#define lut_init(L) GLUE(lut_init_, L)()

static float GLUE(lanczos_resample_one_, L)
     (int ix,
      float dx,
      int iy,
      float dy,
      const float* inimg,
      const int W,
      const int H) {

    const float* lut = GLUE(lut_, L);
    const float lut0 = -(L + 0.5);
    const int Nunits = 2*(L+1);

    float acc = 0.;
    float accx;
    float nacc;
    const float* ly;
    float fx,fy;
    float slope, slopey;
    npy_intp u,v;
    int tx0, ty0;

    // float bin
    fx = (-(dx+L) - lut0) * LANCZOS_NLUT;
    fy = (-(dy+L) - lut0) * LANCZOS_NLUT;
    tx0 = (int)fx;
    ty0 = (int)fy;
    // clip int bins
    tx0 = MAX(0, MIN(LANCZOS_NLUT-1, tx0));
    ty0 = MAX(0, MIN(LANCZOS_NLUT-1, ty0));
    // what fraction of the way through the bin are we?
    fx = fx - tx0;
    fy = fy - ty0;

    // find start of LUT row for this bin.
    tx0 *= Nunits;
    ty0 *= Nunits;

    ly = lut + ty0;
    // special-case pixels near the image edges.
    // (this is the same code except for the "clip" checks on X,Y coords)
    if (ix < L || ix >= (W-L) || iy < L || iy >= (H-L)) {
        iy -= L;
        // Lanczos kernel in y direction
        for (v=0; v<2*L+1; v++, iy++, ly++) {
            int clipiy = MAX(0, MIN((int)(H-1), iy));
            int x = ix - L;
            const float* lx = lut + tx0;
            const float* inpix = inimg + clipiy * W;
            // Lanczos kernel in x direction
            accx = 0.;
            for (u=0; u<2*L+1; u++, x++, lx++) {
                int clipix = MAX(0, MIN((int)(W-1), x));
                slope = lx[Nunits] - (*lx);
                accx  += ((*lx) + slope*fx) * (inpix[clipix]);

                //printf("weighting input (%i, %i) by kernel %f\n",
                //clipix, clipiy, (*lx) + slope*fx);
            }
            slope = ly[Nunits] - (*ly);
            acc  += ((*ly) + slope*fy) * accx;
        }
    } else {
        iy -= L;
        // Lanczos kernel in y direction
        for (v=0; v<2*L+1; v++, iy++, ly++) {
            const float* lx = lut + tx0;
            const float* inpix = inimg + iy * W + ix - L;
            accx = 0;
            // Lanczos kernel in x direction
            for (u=0; u<2*L+1; u++, lx++, inpix++) {
                slope = lx[Nunits] - (*lx);
                accx  += ((*lx) + slope*fx) * (*inpix);

                //printf("weighting input (%i, %i) by kernel %f\n",
                //ix, clipiy, (*lx) + slope*fx);
            }
            slope = ly[Nunits] - (*ly);
            acc  += ((*ly) + slope*fy) * accx;
        }
    }
    // Compute the slope across the X,Y normalizers as well.
    slope = lut[tx0 + Nunits-1 + Nunits] - lut[tx0 + Nunits-1];
    slopey = lut[ty0 + Nunits-1 + Nunits] - lut[ty0 + Nunits-1];
    nacc = ((lut[tx0 + Nunits-1] + slope  * fx) *
            (lut[ty0 + Nunits-1] + slopey * fy));
    return acc / nacc;
}
#define lanczos_resample_one GLUE(lanczos_resample_one_, L)



void evaluate(int n,const int *ix,const int *iy,const float *dx,const float *dy,
              const float *img,int w,int h,float *out) {
 lut_init_3();
 for(int k=0;k<n;k++)out[k]=lanczos_resample_one_3(ix[k],dx[k],iy[k],dy[k],img,w,h);
}
