// This program is free software; you can redistribute it and/or modify it
// under the terms of the GNU General Public License version 2 as published
// by the Free Software Foundation.

#ifndef __aes_share_h__
#define __aes_share_h__

#include "aes_unmasked.h"

void shiftrows_share(byte *stateshare[16],int n);
void mixcolumns_share(byte *stateshare[16],int n);
void addroundkey_share(byte *stateshare[16],byte *wshare[176],int round,int n);

int run_aes_share(byte in[16],byte out[16],byte key[16],int n,void (*subbyte_share_call)(byte *,int),int nt);
int run_aes_common_share(byte in[16],byte out[16],byte key[16],int n,void (*subbyte_common_share_call)(byte *,byte *,int),int nt);



#endif
