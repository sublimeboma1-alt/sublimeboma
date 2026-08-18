@echo off
cd /d c:\Users\NGALA\Desktop\sublime
echo === Rollback to 0004 ===
python manage.py migrate frais_scolaires 0004
echo === Apply 0005 ===
python manage.py migrate frais_scolaires
echo === Done ===