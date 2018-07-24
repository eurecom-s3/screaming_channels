// This program is free software; you can redistribute it and/or modify it
// under the terms of the GNU General Public License version 2 as published
// by the Free Software Foundation.

#include "aes_unmasked.h"

void subbyte_htable(byte *a,int n);
void subbyte_htable_inc(byte *a,int n);
void subbyte_htable_word(byte *a,int n);
void subbyte_htable_word_inc(byte *a,int n);

void subbyte_cs_htable(byte *a,byte *b,int n);
void subbyte_cs_htable_word(byte *a,byte *b,int n);
void subbyte_cs_htable_word_inc(byte *a,byte *b,int n);
