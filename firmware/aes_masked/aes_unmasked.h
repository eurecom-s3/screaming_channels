// This program is free software; you can redistribute it and/or modify it
// under the terms of the GNU General Public License version 2 as published
// by the Free Software Foundation.

#ifndef __aes_h__
#define __aes_h__

#include "common.h"

extern byte sbox[256];

byte multx(byte x);
byte mult(byte x,byte y);
byte inverse(byte x);

byte bit(byte x,int i);
byte affine(byte x);

byte subbyte(byte x);
void printstate(byte state[16]);

void shiftrows(byte state[16]);
void mixcolumns(byte *state);
void subbytestate(byte *state);
void addroundkey(byte *state,byte *w,int round);

void keyexpansion(byte *key,byte *w);

void aes(byte in[16],byte out[16],byte key[16]);
int run_aes(byte in[16],byte out[16],byte key[16],int nt);

void testaes();

#endif
