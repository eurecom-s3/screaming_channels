// This program is free software; you can redistribute it and/or modify it
// under the terms of the GNU General Public License version 2 as published
// by the Free Software Foundation.

#include "aes_htable.h"
#include "share.h"

#include <string.h>
#include <stdint.h>

#define K 256

typedef uint32_t word;

void shift_table(byte a,byte Tp[][K],byte T[][K],int n)
{
  for(int j=0;j<n;j++)
    for(int k=0;k<K;k++)
      Tp[j][k]=T[j][k ^ a];
}

void refresh_table(byte T[][K],byte Tp[][K],int ind)
{
  for(int j=0;j<ind;j++)
  {
    for(int k=0;k<K;k++)
    {
      byte tmp=xorshf96();
      T[j][k]=Tp[j][k] ^ tmp;
      T[ind][k]=T[ind][k] ^ tmp;
    }
  }
}

void read_htable(byte a,byte *b,byte T[][K],int n)
{
  for(int j=0;j<n;j++)
    b[j]=T[j][a];

  refresh(b,n);
}

void htable(byte *a,int lam,byte T[][K],int n)
{
  byte Tp[n][K];
  //int i,j,k;
  int i,k;
  
  for(i=0;i<lam;i++)
  {
    shift_table(a[i],Tp,T,n);

    for(k=0;k<K;k++)
      T[n-1][k]=Tp[n-1][k];

    refresh_table(T,Tp,n-1);
  }
}

void subbyte_htable(byte *a,int n)
{
  //byte T[n][K],Tp[n][K],b[n];
  //int i,j,k;
  byte T[n][K];
  int j,k;
 
  for(k=0;k<K;k++)
    T[0][k]=sbox[k];

  for(j=1;j<n;j++)
    for(k=0;k<K;k++)
      T[j][k]=0;
  
  htable(a,n-1,T,n);

  read_htable(a[n-1],a,T,n);
}

void subbyte_htable_inc(byte *a,int n)
{
  byte T[n][K];
  byte Tp[n][K];
  //byte b[n];
  //int i,j,k;
  int i,k;
 
  for(k=0;k<K;k++)
    T[0][k]=sbox[k];

  for(i=0;i<(n-1);i++)
  {
    shift_table(a[i],Tp,T,i+1);

    for(k=0;k<K;k++)
      T[i+1][k]=0;

    refresh_table(T,Tp,i+1);
  }
  
  read_htable(a[n-1],a,T,n);
}


void refreshword(word a[],int n)
{
  int i;
  word tmp;
  for(i=1;i<n;i++)
  {
    tmp=xorshf96(); //rand();
    a[0]=a[0] ^ tmp;
    a[i]=a[i] ^ tmp;
  }
}

void init_table_word(word T[][K/4])
{
  int w=4;
  for(int k=0;k<K/w;k++)
  {
    word r=0;
    for(int j=w-1;j>=0;j--)
    {
      r=r << 8;
      r^=sbox[k*w+j];
    }
    T[0][k]=r;
  }
}

void shift_table_word(byte a,word Tp[][K/4],word T[][K/4],int n)
{
  for(int j=0;j<n;j++)
    for(int k=0;k<K/4;k++)
      Tp[j][k]=T[j][k ^ a];
}


void refresh_table_word(word T[][K/4],word Tp[][K/4],int ind)
{
  for(int j=0;j<ind;j++)
  {
    for(int k=0;k<K/4;k++)
    {
      word tmp=xorshf96();
      T[j][k]=Tp[j][k] ^ tmp;
      T[ind][k]=T[ind][k] ^ tmp;
    }
  }
}

void read_htable_word(byte a,word *b,word T[][K/4],int n)
{
  for(int j=0;j<n;j++)
    b[j]=T[j][a];

  refreshword(b,n);
}

void htable_small(byte *a,word *b,int n)
{
  int w=4;
  byte Ts[n][w];   // 4*n bytes
  byte Tsp[n][w];  // 4*n bytes

  for(int i=0;i<n;i++)
    for(int k=0;k<w;k++)
      Ts[i][k]=b[i] >> (k*8);

  for(int i=0;i<(n-1);i++)
  {
    byte s=a[i] & (w-1);
    for(int j=0;j<n;j++)
      for(int k=0;k<w;k++)
	Tsp[j][k]=Ts[j][k^s];

    for(int k=0;k<w;k++)
      Ts[0][k]=Tsp[0][k];

    for(int j=1;j<n;j++)
    {
      for(int k=0;k<w;k++)
      {
	byte tmp=xorshf96();
	Ts[j][k]=Tsp[j][k] ^ tmp;
	Ts[0][k]=Ts[0][k] ^ tmp;
      }
    }
  }

  for(int j=0;j<n;j++)
    a[j]=Ts[j][a[n-1] & (w-1)];

  refresh(a,n);
}

void htable_word(byte *a,int lam,word T[][K/4],int n)
{
  int w=4;
  word Tp[n][K/4];
  //int i,j,k,k2;
  int i,k,k2;
  
  for(i=0;i<lam;i++)
  {
    k2=a[i]/w;

    shift_table_word(k2,Tp,T,n);

    for(k=0;k<K/w;k++)
      T[n-1][k]=Tp[n-1][k];

    refresh_table_word(T,Tp,n-1);
  }
}

void subbyte_htable_word(byte *a,int n)  // n+4 bytes
{
  int w=4;
  word T[n][K/w];  // n*256 bytes
  //word Tp[n][K/w];  // n*256 bytes
  //int i,k,k2,j;    // 16 bytes
  int i,k;    // 16 bytes

  init_table_word(T);

  for(i=1;i<n;i++)
    for(k=0;k<K/w;k++)
      T[i][k]=0;
  
  htable_word(a,n-1,T,n);

  word b[n];
  read_htable_word(a[n-1]/4,b,T,n);
  
  htable_small(a,b,n);
}

void htable_word_inc(byte *a,int ell,int lam,word T[][K/4],int n)
{
  int w=4;
  word Tp[n][K/4];
  //int i,j,k,k2;
  int k2;
  
  int ind=ell;

  for(int i=0;i<lam;i++)
  {
    k2=a[i]/w;

    shift_table_word(k2,Tp,T,ind);

    if (ind<n)
    {
      for(int k=0;k<K/w;k++)
	T[ind][k]=0;
      refresh_table_word(T,Tp,ind);
    }
    else
    {
      for(int k=0;k<K/w;k++)
	T[n-1][k]=Tp[n-1][k];
      refresh_table_word(T,Tp,n-1);
    }    

    ind+=1;
    if(ind>n)
      ind=n;
  }
}

void subbyte_htable_word_inc(byte *a,int n)  // n+4 bytes
{
  int w=sizeof(word); // number of bytes to store in a word w=4
  word T[n][K/w];  // n*256 bytes
  //word Tp[n][K/w]; // n*256 bytes
  //int i,k,k2,j;    // 16 bytes
  word b[n];       // 4*n bytes (for 32-bit registers)

  init_table_word(T);

  htable_word_inc(a,1,n-1,T,n);

  read_htable_word(a[n-1]/4,b,T,n);
  
  htable_small(a,b,n);
}

void common_shares(byte *a,byte *b,byte *r,byte *ap,byte *bp,int n)
{
  for(int i=0;i<n/2;i++)
  {
    r[i]=xorshf96();
    ap[i]=(a[i+n/2] ^ r[i]) ^ a[i];
    bp[i]=(b[i+n/2] ^ r[i]) ^ b[i];
  }
  
  if ((n & 1)==1)
  {
    ap[n/2]=a[n-1];
    bp[n/2]=b[n-1];
  }
}


void subbyte_cs_htable_basic(byte *a,byte *b,int n)
{
  subbyte_htable(a,n);
  subbyte_htable(b,n);
}

void subbyte_cs_htable(byte *a,byte *b,int n)
{
  int n2=(n+1)/2;
  byte r[n/2];
  byte ap[n2],bp[n2];

  common_shares(a,b,r,ap,bp,n);

  byte T[n][K];
  
  for(int k=0;k<K;k++)
    T[0][k]=sbox[k];

  for(int j=1;j<n;j++)
    for(int k=0;k<K;k++)
      T[j][k]=0;
  
  htable(r,n/2,T,n);
  
  byte T2[n][K];

  for(int j=0;j<n;j++)
    for(int k=0;k<K;k++)
      T2[j][k]=T[j][k];

  htable(ap,n2-1,T,n);
  htable(bp,n2-1,T2,n);

  read_htable(ap[n2-1],a,T,n);
  read_htable(bp[n2-1],b,T2,n);
}

void subbyte_cs_htable_word(byte *a,byte *b,int n)
{
  int w=4;
  int n2=(n+1)/2;
  byte r[n/2];
  byte ap[n2],bp[n2];

  common_shares(a,b,r,ap,bp,n);

  word T[n][K/w];
  
  init_table_word(T);

  for(int i=1;i<n;i++)
    for(int k=0;k<K/w;k++)
      T[i][k]=0;

  htable_word(r,n/2,T,n);
  
  word T2[n][K/w];

  for(int j=0;j<n;j++)
    for(int k=0;k<K/w;k++)
      T2[j][k]=T[j][k];

  htable_word(ap,n2-1,T,n);
  htable_word(bp,n2-1,T2,n);

  word u[n];
  read_htable_word(ap[n2-1]/4,u,T,n);

  word v[n];
  read_htable_word(bp[n2-1]/4,v,T2,n);

  htable_small(a,u,n);
  htable_small(b,v,n);
}

void subbyte_cs_htable_word_inc(byte *a,byte *b,int n)
{
  int w=4;
  int n2=(n+1)/2;
  byte r[n/2];
  byte ap[n2],bp[n2];

  common_shares(a,b,r,ap,bp,n);

  word T[n][K/w];
  
  init_table_word(T);

  // we start with two output shares
  int ell=2;

  for(int j=1;j<ell;j++)
    for(int k=0;k<K/w;k++)
      T[j][k]=0;

  htable_word_inc(r,ell,n/2,T,n);

  int ell2=ell+n/2;
  if(ell2>n) ell2=n;

  word T2[n][K/w];

  for(int j=0;j<ell2;j++)
    for(int k=0;k<K/w;k++)
      T2[j][k]=T[j][k];

  htable_word_inc(ap,ell2,n2-1,T,n);
  htable_word_inc(bp,ell2,n2-1,T2,n);

  word u[n];
  read_htable_word(ap[n2-1]/4,u,T,n);

  word v[n];
  read_htable_word(bp[n2-1]/4,v,T2,n);

  htable_small(a,u,n);
  htable_small(b,v,n);
}


