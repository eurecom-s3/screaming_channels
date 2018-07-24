// This program is free software; you can redistribute it and/or modify it
// under the terms of the GNU General Public License version 2 as published
// by the Free Software Foundation.

#include "aes_unmasked.h"

#include <stdio.h>
//#include <time.h>

byte sbox[256]={
0x63,0x7c,0x77,0x7b,0xf2,0x6b,0x6f,0xc5,
0x30,0x01,0x67,0x2b,0xfe,0xd7,0xab,0x76,
0xca,0x82,0xc9,0x7d,0xfa,0x59,0x47,0xf0,
0xad,0xd4,0xa2,0xaf,0x9c,0xa4,0x72,0xc0,
0xb7,0xfd,0x93,0x26,0x36,0x3f,0xf7,0xcc,
0x34,0xa5,0xe5,0xf1,0x71,0xd8,0x31,0x15,
0x04,0xc7,0x23,0xc3,0x18,0x96,0x05,0x9a,
0x07,0x12,0x80,0xe2,0xeb,0x27,0xb2,0x75,
0x09,0x83,0x2c,0x1a,0x1b,0x6e,0x5a,0xa0,
0x52,0x3b,0xd6,0xb3,0x29,0xe3,0x2f,0x84,
0x53,0xd1,0x00,0xed,0x20,0xfc,0xb1,0x5b,
0x6a,0xcb,0xbe,0x39,0x4a,0x4c,0x58,0xcf,
0xd0,0xef,0xaa,0xfb,0x43,0x4d,0x33,0x85,
0x45,0xf9,0x02,0x7f,0x50,0x3c,0x9f,0xa8,
0x51,0xa3,0x40,0x8f,0x92,0x9d,0x38,0xf5,
0xbc,0xb6,0xda,0x21,0x10,0xff,0xf3,0xd2,
0xcd,0x0c,0x13,0xec,0x5f,0x97,0x44,0x17,
0xc4,0xa7,0x7e,0x3d,0x64,0x5d,0x19,0x73,
0x60,0x81,0x4f,0xdc,0x22,0x2a,0x90,0x88,
0x46,0xee,0xb8,0x14,0xde,0x5e,0x0b,0xdb,
0xe0,0x32,0x3a,0x0a,0x49,0x06,0x24,0x5c,
0xc2,0xd3,0xac,0x62,0x91,0x95,0xe4,0x79,
0xe7,0xc8,0x37,0x6d,0x8d,0xd5,0x4e,0xa9,
0x6c,0x56,0xf4,0xea,0x65,0x7a,0xae,0x08,
0xba,0x78,0x25,0x2e,0x1c,0xa6,0xb4,0xc6,
0xe8,0xdd,0x74,0x1f,0x4b,0xbd,0x8b,0x8a,
0x70,0x3e,0xb5,0x66,0x48,0x03,0xf6,0x0e,
0x61,0x35,0x57,0xb9,0x86,0xc1,0x1d,0x9e,
0xe1,0xf8,0x98,0x11,0x69,0xd9,0x8e,0x94,
0x9b,0x1e,0x87,0xe9,0xce,0x55,0x28,0xdf,
0x8c,0xa1,0x89,0x0d,0xbf,0xe6,0x42,0x68,
0x41,0x99,0x2d,0x0f,0xb0,0x54,0xbb,0x16};

byte multx(byte x)
{
  byte y=x;
  y=y << 1;
  // if((x & 0x80)!=0)  y=y ^ 0x1b;
  byte m[]={0,0x1b};
  y^=m[x >> 7];
  return y;
}

// slow multiplication in GF(2^8)
byte mult(byte x,byte y)
{
  int i;
  byte z=0;
  byte a=128;
  for(i=7;i>=0;i--)
  {
    z=multx(z);
    if((y & a)!=0) z^=x;
    a=a >> 1;
  }
  return z;
}

// slow inverse
byte inverse(byte x)
{
  int i;
  byte y=0;
  if(x==0) return 0;
  for(i=0;i<255;i++)
  {
    y++;
    if(mult(x,y)==1) return y;
  }
  return y;
}

byte bit(byte x,int i)
{
  return (x >> i) & 1;
}

// affine transform in AES Sbox
byte affine(byte x)
{
  byte y=0;
  int i;
  byte z;
  for(i=7;i>=0;i--)
  {
    z=bit(x,i) ^ bit(x,(i+4) %8) ^ bit(x,(i+5) %8) ^ bit(x,(i+6) % 8) ^ bit(x,(i+7) % 8);
    y=(y << 1) ^ z;
  }
  y=y ^ 99;
  return y;
}

// Generation of the AES Sbox
void gensbox()
{
  int i;
  byte x=0;
  printf("byte sbox[256]={");
  for(i=0;i<256;i++)
  {
    if((i%8)==0) printf("\n");
    printf("0x%02x",affine(inverse(x)));
    x++;
    if(i<255) printf(",");
  }
  printf("};\n");
}

byte subbyte(byte x)
{
  return sbox[x];
}

// slow invsubbyte
byte invsubbyte(byte x)
{
  int i;
  byte y=0;
  for(i=0;i<256;i++)
  {
    if(sbox[y]==x) return y;
    y++;
  }
  return y;
}

void invsubbytestate(byte state[16])
{
  int i;
  for(i=0;i<16;i++) state[i]=invsubbyte(state[i]);
}

void printstate(byte state[16])
{
  int i;
  int j;
  for(i=0;i<4;i++)
  {
    for(j=0;j<4;j++)
      printf("%02x ",state[i+4*j]);
    printf("\n");
  }
  printf("\n");
}

void addroundkey(byte *state,byte *w,int round)
{
  int i;
  for(i=0;i<16;i++)
    state[i]^=w[16*round+i];
}

void swap(byte *a,byte *b)
{
  byte m=*a;
  *a=*b;
  *b=m;
}

void cycle4(byte *a,byte *b,byte *c,byte *d)
{
  byte m=*a;
  *a=*b;
  *b=*c;
  *c=*d;
  *d=m;
}

void shiftrows(byte state[16])
{
    //byte m;
  cycle4(&state[1],&state[5],&state[9],&state[13]);
  cycle4(&state[3],&state[15],&state[11],&state[7]);
  swap(&state[2],&state[10]);
  swap(&state[6],&state[14]);
}

void mixcolumns(byte *state)
{
  byte ns[16];
  int i,j;
  for(j=0;j<4;j++)
  {
    ns[j*4]=multx(state[j*4]) ^ multx(state[j*4+1]) ^ state[j*4+1] ^ state[j*4+2] ^ state[j*4+3];
    ns[j*4+1]=state[j*4] ^ multx(state[j*4+1]) ^ multx(state[j*4+2]) ^ state[j*4+2] ^ state[j*4+3];
    ns[j*4+2]=state[j*4] ^ state[j*4+1] ^ multx(state[j*4+2]) ^ multx(state[j*4+3]) ^ state[j*4+3];
    ns[j*4+3]=multx(state[j*4]) ^ state[j*4] ^ state[j*4+1] ^ state[j*4+2] ^ multx(state[j*4+3]) ;
  }
  for(j=0;j<4;j++)
    for(i=0;i<4;i++)
      state[j*4+i]=ns[j*4+i];
}

void setrcon(byte rcon[10])
{
  int i;
  byte x=1;

  for(i=0;i<10;i++)
  {
    rcon[i]=x;
    x=multx(x);
  }
}

void keyexpansion(byte *key,byte *w)
{
  int i,j;
  byte temp[4];
  
  byte rcon[10];
  setrcon(rcon);
 
  for(i=0;i<16;i++)
    w[i]=key[i];

  for(i=16;i<176;i+=4)
  {
    for(j=0;j<4;j++)
      temp[j]=w[i-4+j];

    if((i % 16)==0)
    {
      temp[0]=subbyte(w[i-3]) ^ rcon[i/16-1];
      temp[1]=subbyte(w[i-2]);
      temp[2]=subbyte(w[i-1]);
      temp[3]=subbyte(w[i-4]);
    }

    for(j=0;j<4;j++)
      w[i+j]=w[i+j-16] ^ temp[j];
  }
}

void subbytestate(byte *state)
{
  int i;
  for(i=0;i<16;i++) 
    state[i]=subbyte(state[i]);
}

void aes(byte in[16],byte out[16],byte w[176])
{
    //int i,j;
  int i;
  int round=0;
  byte state[16];

  for(i=0;i<16;i++)
    state[i]=in[i];

  addroundkey(state,w,0);

  for(round=1;round<10;round++)
  { 
    subbytestate(state);
    shiftrows(state);
    mixcolumns(state);
    addroundkey(state,w,round);
  }
 
  subbytestate(state);
  shiftrows(state);
  addroundkey(state,w,10);

  for(i=0;i<16;i++)
    out[i]=state[i];
}

int run_aes(byte in[16],byte out[16],byte key[16],int nt)
{
  int i;
  byte w[176];
  //clock_t start,end;

  keyexpansion(key,w);
  
  //start=clock();
  for(i=0;i<nt;i++)
    aes(in,out,w);
  //end=clock();

  //return (int) (end-start);
 return 1;
}
