# -*- coding: utf-8 -*-
"""Устранение дубля первой записи оглавления (add_toc_placeholders.py вставляет
гиперссылочный абзац без кэшированного номера + плоскую копию той же записи).
Патч: в гиперссылочном абзаце заменяем содержимое после fldChar=separate на
простые runs (текст + таб + кэш номера «1»), плоский дубль удаляем целиком."""
import re, shutil, sys, zipfile

DOCX = sys.argv[1] if len(sys.argv) > 1 else "/home/z/my-project/download/ДОЛГОВАЯ_ЯМА_ХРОНИКА_5000_ЛЕТ_v1_0.docx"
TMP = DOCX + ".tmp"

zin = zipfile.ZipFile(DOCX, "r")
xml = zin.read("word/document.xml").decode("utf-8")

# 1) Гиперссылочный абзац первой записи (anchor=_Toc1) — вынимаем его тело
m = re.search(r'<w:p>(?:(?!</w:p>).)*?w:anchor="_Toc1"(?:(?!</w:p>).)*?</w:p>', xml, re.S)
assert m, "гиперссылочный абзац _Toc1 не найден"
para = m.group(0)
title_m = re.search(r'<w:t xml:space="preserve">([^<]+)</w:t>', para)
title = title_m.group(1)
ppr_m = re.search(r'<w:pPr>.*?</w:pPr>', para, re.S)
ppr = ppr_m.group(0) if ppr_m else ""
# Разбираем поле: begin/instrText/separate остаются (вплоть до закрытия </w:r>), после — plain runs с кэшем номера
sep_idx = para.find('<w:fldChar w:fldCharType="separate"/>')
head_end = para.index('</w:r>', sep_idx) + len('</w:r>')   # закрываем рану separate-ран
head = para[:head_end]
new_para = (head
            + '<w:r><w:t xml:space="preserve">' + title + '</w:t></w:r>'
            + '<w:r><w:tab/></w:r>'
            + '<w:r><w:t>1</w:t></w:r>'
            + '<w:r><w:fldChar w:fldCharType="end"/></w:r></w:p>')
xml = xml.replace(para, new_para, 1)
print("гиперссылочная запись №1 заменена на плоскую с кэшем номера 1:", repr(title[:50]))

# 2) Плоский дубль первой записи — следующий абзац с тем же текстом и номером 1
dup_pat = re.compile(r'<w:p>(?:(?!</w:p>).)*?<w:t>' + re.escape(title) + r'</w:t>(?:(?!</w:p>).)*?<w:t>1</w:t>(?:(?!</w:p>).)*?</w:p>', re.S)
m2 = dup_pat.search(xml)
assert m2, "плоский дубль первой записи не найден"
xml = xml[:m2.start()] + xml[m2.end():]
print("плоский дубль первой записи удалён")

zout = zipfile.ZipFile(TMP, "w", zipfile.ZIP_DEFLATED)
for item in zin.infolist():
    data = zin.read(item.filename)
    if item.filename == "word/document.xml":
        data = xml.encode("utf-8")
    zout.writestr(item, data)
zout.close(); zin.close()
shutil.move(TMP, DOCX)
print("OK:", DOCX)
