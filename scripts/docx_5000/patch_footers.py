# -*- coding: utf-8 -*-
"""Постобработка DOCX по toc.md: патч instrText футеров (ROMAN/arabic) + удаление пустых <w:pgNumType/>.
Разделы: 1 обложка (без футера) → 2 фронт-материя (ROMAN) → 3 тело (arabic)."""
import re, shutil, sys, zipfile

DOCX = sys.argv[1] if len(sys.argv) > 1 else "/home/z/my-project/download/ДОЛГОВАЯ_ЯМА_ХРОНИКА_5000_ЛЕТ_v1_0.docx"
TMP = DOCX + ".tmp"

zin = zipfile.ZipFile(DOCX, "r")
docxml = zin.read("word/document.xml").decode("utf-8")
rels = zin.read("word/_rels/document.xml.rels").decode("utf-8")

# rId → target
rel_map = dict(re.findall(r'<Relationship[^>]*Id="([^"]+)"[^>]*Target="([^"]+)"', rels))
rel_map.update(dict((m[0], m[1]) for m in re.findall(r'<Relationship[^>]*Target="([^"]+)"[^>]*Id="([^"]+)"', rels) if False))

# footerReference default по порядку появления в document.xml (секции 2 и 3)
foot_ids = re.findall(r'<w:footerReference w:type="default" r:id="([^"]+)"/>', docxml)
print("footerReference (default) по порядку:", foot_ids)
assert len(foot_ids) >= 2, "ожидались футеры двух секций"
roman_target = rel_map[foot_ids[0]].split("/")[-1]
arabic_target = rel_map[foot_ids[1]].split("/")[-1]
print("ROMAN →", roman_target, "| arabic →", arabic_target)

def patch_footer(xml: str, fmt: str) -> str:
    # PAGE → PAGE \* ROMAN|arabic \* MERGEFORMAT (только голый PAGE)
    return re.sub(r'(<w:instrText[^>]*>)\s*PAGE\s*(</w:instrText>)',
                  lambda m: m.group(1) + f' PAGE \\* {fmt} \\* MERGEFORMAT ' + m.group(2), xml)

# пустые pgNumType из обложки
docxml2, n_removed = re.subn(r'<w:pgNumType/>', '', docxml)
print("удалено пустых <w:pgNumType/>:", n_removed)

zout = zipfile.ZipFile(TMP, "w", zipfile.ZIP_DEFLATED)
for item in zin.infolist():
    data = zin.read(item.filename)
    name = item.filename.split("/")[-1]
    if item.filename == "word/document.xml":
        data = docxml2.encode("utf-8")
    elif name == roman_target and item.filename.startswith("word/"):
        data = patch_footer(data.decode("utf-8"), "ROMAN").encode("utf-8")
        print(f"патч ROMAN применён к {item.filename}")
    elif name == arabic_target and item.filename.startswith("word/"):
        data = patch_footer(data.decode("utf-8"), "arabic").encode("utf-8")
        print(f"патч arabic применён к {item.filename}")
    zout.writestr(item, data)
zout.close(); zin.close()
shutil.move(TMP, DOCX)
print("OK:", DOCX)
