# -*- coding: utf-8 -*-
from kesi.susia.POJ import toPOJ
from kesi.susia.TL import toTL
from kesi.butkian.kongiong import is_lomaji


class Ji:
    
    def __init__(self, hanlo, lomaji=None, is_neutral=False):
        self.hanlo = hanlo
        # si_khinsiann 是輕聲
        if not lomaji:
            lomaji = hanlo
        self.CJK = not all(is_lomaji(c) for c in hanlo)
        # print(hanlo, lomaji, self.CJK)
        self.lomaji = lomaji
        self.is_neutral = is_neutral

    def __eq__(self, other):
        return (
            self.hanlo == other.hanlo
            and self.lomaji == other.lomaji
            and self.is_neutral == other.is_neutral
        )

    @property
    def kiphanlo(self):
        if self.is_neutral and not is_lomaji(self.hanlo[2]):
            return self.hanlo[2:]
        return self.hanlo
    
    def convert_system(self, convert_func):
        hanlo = self.hanlo
        lomaji = self.lomaji
        return Ji(
            convert_func(hanlo), convert_func(lomaji),
            is_neutral=self.is_neutral
        )
    def POJ(self):
        return self.convert_system(toPOJ)

    def TL(self):
        return self.convert_system(toTL)

    KIP = TL
