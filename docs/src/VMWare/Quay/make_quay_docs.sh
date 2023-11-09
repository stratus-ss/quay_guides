mkdir -p tmp
echo "- [Introduction](Intro.md)
- [Prerequisites](Quay_Prerequisites.md)
- [Quay UI Install](Quay_UI_Install.md)
    - [Quay Config: init-config-bundle-secret](InitConfigBundle.md)
    - [Quay UI Secrets](Quay_UI_Secrets.md)
    - [Quay Config: Create QuayRegistry](Quay_UI_Objects.md)
    - [OPTIONAL: Quay Mirror](Quay_UI_Mirror.md)
    - [OPTIONAL: Quay ProxyCache](Quay_UI_ProxyCache.md)
- [Quay CLI Install](Quay_CLI_Install.md)
    - [Quay Config: init-config-bundle-secret](InitConfigBundle.md)
    - [Quay Config: Create QuayRegistry](Quay_CLI_Objects.md)
    - [OPTIONAL: Quay Mirror](Quay_CLI_Mirror.md)
    - [OPTIONAL: Quay ProxyCache](Quay_CLI_ProxyCache.md)
    - [OPTIONAL: Create Initial Quay User](Quay_CLI_Initialize.md)
" > tmp/summary.md


cd tmp
for file in Intro.md Quay_Prerequisites.md Quay_UI_Install.md InitConfigBundle.md Quay_UI_Secrets.md Quay_UI_Objects.md Quay_UI_Mirror.md Quay_UI_ProxyCache.md; do
  ln -s ../UI/"${file}"
done

for file in Quay_CLI_Install.md InitConfigBundle.md Quay_CLI_Objects.md Quay_CLI_Mirror.md Quay_CLI_ProxyCache.md Quay_CLI_Initialize.md; do
  ln -s ../CLI/"${file}"
done

cd ..

stitchmd -C tmp/ -o ../../../rendered/Quay_on_VMWare.md tmp/summary.md 

rm -rf tmp
