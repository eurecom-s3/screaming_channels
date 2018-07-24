// This program is free software; you can redistribute it and/or modify it
// under the terms of the GNU General Public License version 2 as published
// by the Free Software Foundation.

#include "aes_share.h"
#include "share.h"
#include "aes.h"

#include <stdlib.h>
#include <time.h>

void shiftrows_share(byte *stateshare[16],int n)
{
  byte m;
  int i;
  for(i=0;i<n;i++)
  {
    m=stateshare[1][i];
    stateshare[1][i]=stateshare[5][i];
    stateshare[5][i]=stateshare[9][i];
    stateshare[9][i]=stateshare[13][i];
    stateshare[13][i]=m;

    m=stateshare[2][i];
    stateshare[2][i]=stateshare[10][i];
    stateshare[10][i]=m;
    m=stateshare[6][i];
    stateshare[6][i]=stateshare[14][i];
    stateshare[14][i]=m;

    m=stateshare[3][i];
    stateshare[3][i]=stateshare[15][i];
    stateshare[15][i]=stateshare[11][i];
    stateshare[11][i]=stateshare[7][i];
    stateshare[7][i]=m;
  }
}

void mixcolumns_share(byte *stateshare[16],int n)
{
  byte ns[16];
  int i,j;
  for(i=0;i<n;i++)
  {
    for(j=0;j<4;j++)
    {
      ns[j*4]=multx(stateshare[j*4][i]) ^ multx(stateshare[j*4+1][i]) ^ stateshare[j*4+1][i] ^ stateshare[j*4+2][i] ^ stateshare[j*4+3][i];
      ns[j*4+1]=stateshare[j*4][i] ^ multx(stateshare[j*4+1][i]) ^ multx(stateshare[j*4+2][i]) ^ stateshare[j*4+2][i] ^ stateshare[j*4+3][i];
      ns[j*4+2]=stateshare[j*4][i] ^ stateshare[j*4+1][i] ^ multx(stateshare[j*4+2][i]) ^ multx(stateshare[j*4+3][i]) ^ stateshare[j*4+3][i];
      ns[j*4+3]=multx(stateshare[j*4][i]) ^ stateshare[j*4][i] ^ stateshare[j*4+1][i] ^ stateshare[j*4+2][i] ^ multx(stateshare[j*4+3][i]) ;
    }
    for(j=0;j<16;j++)
      stateshare[j][i]=ns[j];
  }
}

void addroundkey_share(byte *stateshare[16],byte *wshare[176],int round,int n)
{
  int i,j;
  for(i=0;i<16;i++)
    for(j=0;j<n;j++)
      stateshare[i][j]^=wshare[16*round+i][j];
}

void subbytestate_share(byte *stateshare[16],int n,void (*subbyte_share_call)(byte *,int))
{
  int i;
  for(i=0;i<16;i++)
    subbyte_share_call(stateshare[i],n);
} 

// AES with shares. The subbyte computation with shares is given as parameter
void aes_share_subkeys(byte in[16],byte out[16],byte *wshare[176],int n,void (*subbyte_share_call)(byte *,int))
{
    //int i,j;
  int i;
  int round=0;

  byte *stateshare[16];

  for(i=0;i<16;i++)
  {
    stateshare[i]=(byte*) malloc(n*sizeof(byte));
    share(in[i],stateshare[i],n);
    refresh(stateshare[i],n);
  }  

  addroundkey_share(stateshare,wshare,0,n);

  for(round=1;round<10;round++)
  { 
    subbytestate_share(stateshare,n,subbyte_share_call);
    shiftrows_share(stateshare,n);
    mixcolumns_share(stateshare,n);
    addroundkey_share(stateshare,wshare,round,n);
  }
 
  subbytestate_share(stateshare,n,subbyte_share_call);
  shiftrows_share(stateshare,n);
  addroundkey_share(stateshare,wshare,10,n);

  for(i=0;i<16;i++)
  {
    out[i]=decode(stateshare[i],n);
    free(stateshare[i]);
  }
}

int run_aes_share(byte in[16],byte out[16],byte key[16],int n,void (*subbyte_share_call)(byte *,int),int nt)
{
  int i;
  byte w[176];
  byte *wshare[176];
  clock_t start,end;

  keyexpansion(key,w);

  for(i=0;i<176;i++)
  {
    wshare[i]=(byte *) malloc(n*sizeof(byte));
    share(w[i],wshare[i],n);
    refresh(wshare[i],n);
  }
 
  start=clock();

  for(i=0;i<nt;i++)
    aes_share_subkeys(in,out,wshare,n,subbyte_share_call);
  end=clock();

  for(i=0;i<176;i++)
    free(wshare[i]);

  return (int) (end-start);
}

void subbytestate_common_share(byte *stateshare[16],int n,void (*subbyte_common_share_call)(byte *,byte *,int))
{
  int i;
  for(i=0;i<16;i+=2)
    subbyte_common_share_call(stateshare[i],stateshare[i+1],n);
} 

// AES with shares. The subbyte computation with shares is given as parameter
void aes_common_share_subkeys(byte in[16],byte out[16],byte *wshare[176],int n,void (*subbyte_common_share_call)(byte *,byte *,int))
{
    //int i,j;
  int i;
  int round=0;

  byte *stateshare[16];

  for(i=0;i<16;i++)
  {
    stateshare[i]=(byte*) malloc(n*sizeof(byte));
    share(in[i],stateshare[i],n);
    refresh(stateshare[i],n);
  }  

  addroundkey_share(stateshare,wshare,0,n);

  for(round=1;round<10;round++)
  { 
    subbytestate_common_share(stateshare,n,subbyte_common_share_call);
    shiftrows_share(stateshare,n);
    mixcolumns_share(stateshare,n);
    addroundkey_share(stateshare,wshare,round,n);
  }
 
  subbytestate_common_share(stateshare,n,subbyte_common_share_call);
  shiftrows_share(stateshare,n);
  addroundkey_share(stateshare,wshare,10,n);

  for(i=0;i<16;i++)
  {
    out[i]=decode(stateshare[i],n);
    free(stateshare[i]);
  }
}


int run_aes_common_share(byte in[16],byte out[16],byte key[16],int n,void (*subbyte_common_share_call)(byte *,byte *,int),int nt)
{
  int i;
  byte w[176];
  byte *wshare[176];
  //clock_t start,end;

  keyexpansion(key,w);

  for(i=0;i<176;i++)
  {
    wshare[i]=(byte *) malloc(n*sizeof(byte));
    share(w[i],wshare[i],n);
    refresh(wshare[i],n);
  }
 
  //start=clock();

  for(i=0;i<nt;i++)
    aes_common_share_subkeys(in,out,wshare,n,subbyte_common_share_call);
  //end=clock();

  for(i=0;i<176;i++)
    free(wshare[i]);

  return 0;
}
  

