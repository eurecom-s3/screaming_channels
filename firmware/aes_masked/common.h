#ifndef __common_h__
#define __common_h__

typedef unsigned char byte;

void report_time(int dt,int nt,int base,unsigned int nrand);
void check_ciphertext(byte *out,byte *outex,int nbyte);
int runalgo(void (*algo)(byte *,byte *,byte *),byte *in,byte *out,byte *key,byte *outex,int nbyte,int nt,int base);

#endif
