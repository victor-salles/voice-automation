#!/usr/bin/env python3
"""Detect whether stdin text is Portuguese or English.

Usage: echo "Hello world" | python3 detect_lang.py
Output: en
"""
import re
import sys

# Words that exist in both languages are excluded (no, com, a, ou)
PT_ONLY = re.compile(
    r'\b(da|do|das|dos|na|nas|nos|uma|uns|umas|não|são|está'
    r'|isso|também|você|ele|ela|esse|essa|este|esta|já|muito'
    r'|pode|seu|sua|ter|foi|havia|mas|ao|aos|até|pelo|pela'
    r'|pelos|pelas)\b'
)

# Common PT content words — not function words, but rarely appear in English
PT_CONTENT = re.compile(
    r'\b(testando|fazendo|usando|quando|porque|ainda|agora|depois'
    r'|antes|sempre|nunca|apenas|outro|outra|outros|outras|entre'
    r'|sobre|mesmo|mesma|cada|todos|todas|tudo|nada|aqui|onde'
    r'|como|mais|menos|dois|três|quatro|cinco|seis|sete|oito|nove|dez'
    r'|olá|obrigado|obrigada|bom|boa|bem|mal|sim|então|assim'
    r'|preciso|quero|tenho|estou|vamos|podemos|devemos|acho)\b'
)

EN_ONLY = re.compile(
    r'\b(the|is|are|was|were|have|has|had|been|will|would|could'
    r'|should|can|this|that|these|those|there|their|they|them'
    r'|with|from|into|which|when|where|what|while|because|then'
    r'|than|been|being|does|did|not|but|and|for|you|your)\b'
)

PT_CHARS = re.compile(r'[ãõçÃÕÇ]')
PT_ACCENTS = re.compile(r'[àáâéêíóôúÀÁÂÉÊÍÓÔÚ]')


def detect(text: str) -> str:
    lower = text.lower()
    pt_score = (
        len(PT_CHARS.findall(text)) * 3
        + len(PT_ACCENTS.findall(text)) * 2
        + len(PT_ONLY.findall(lower))
        + len(PT_CONTENT.findall(lower))
    )
    en_score = len(EN_ONLY.findall(lower))
    return "pt" if pt_score >= 2 and pt_score > en_score else "en"


if __name__ == "__main__":
    print(detect(sys.stdin.read()))
