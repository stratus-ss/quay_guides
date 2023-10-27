mkdir -p tmp
echo "- [Introduction](Intro.md)
- [Prerequisites](ODF_Prerequisites.md)
  - [ODF UI Prerequisites.md](ODF_UI_Prerequisites.md)
  - [ODF CLI Prerequisites.md](ODF_CLI_Prerequisites.md)
    - [Create Machinesets](ODF_Machineset.md)
      - [VIA CLI](ODF_CLI_Machineset.md)
      - [Via UI](ODF_UI_Machineset.md)
    - [ODF UI Operator Installation](ODF_UI_Install_Operator.md)
    - [ODF Storage Considerations](ODF_Storage_Consideration.md)
        - [Optional: Local Storage Operator](ODF_UI_Local_Storage.md)
        - [ODF Storage Serving Option 1: Multicloud Object Gateway](ODF_UI_StorageSystem.md)
        - [ODF Storage Serving Option 2: Noobaa](ODF_CLI_Noobaa.md)
" > tmp/summary.md


cd tmp
for file in Intro.md Quay_Prerequisites.md Quay_UI_Install.md InitConfigBundle.md Quay_UI_Secrets.md Quay_UI_Objects.md Quay_UI_Mirror.md Quay_UI_ProxyCache.md; do
  ln -s ../UI/"${file}"
done

for file in Quay_CLI_Install.md InitConfigBundle.md Quay_CLI_Objects.md Quay_CLI_Mirror.md Quay_CLI_ProxyCache.md; do
  ln -s ../CLI/"${file}"
done

cd ..

stitchmd -C tmp/ -o ../../../rendered/Quay_on_VMWare.md tmp/summary.md 

rm -rf tmp
