mkdir -p tmp
echo "- [Introduction](Intro.md)
- [Prerequisites](ODF_Prerequisites.md)
  - [ODF Storage Considerations](ODF_Storage_Consideration.md)
  - [Create Machinesets](ODF_Machineset.md)
    - [VIA CLI](ODF_CLI_Machineset.md)
    - [Via UI](ODF_UI_Machineset.md)
- [ODF UI Operator Installation](ODF_UI_Install_Operator.md)
  - [Optional: Local Storage Operator](ODF_UI_LocalStorage.md)
  - [ODF Storage Serving Option 1: Multicloud Object Gateway](ODF_UI_StorageSystem.md)
  - [ODF Storage Serving Option 2: Noobaa](ODF_Noobaa.md)
- [ODF CLI Operator Installation](ODF_CLI_Install_Operator.md)
  - [Label Nodes](ODF_CLI_Label_Node.md)
  - [ODF Operator Installation](ODF_CLI_Install_Operator.md)
  - [Optional: Local Storage Operator](ODF_CLI_Local_Storage.md)
  - [ODF Storage Serving Option 1: Multicloud Object Gateway](ODF_CLI_MCOG.md)
  - [ODF Storage Serving Option 2: Noobaa](ODF_Noobaa.md)
" > tmp/summary.md


cd tmp
for file in ODF_UI_Install.md ODF_UI_Machineset.md ODF_UI_Install_Operator.md ODF_UI_LocalStorage.md ODF_UI_StorageSystem.md; do
  ln -s ../UI/"${file}"
done

for file in ODF_CLI_Install_Operator.md  ODF_CLI_Machineset.md ODF_CLI_Label_Node.md ODF_CLI_MCOG.md ODF_CLI_Local_Storage.md; do
  ln -s ../CLI/"${file}"
done

for file in ODF_Storage_Consideration.md Intro.md ODF_Machineset.md ODF_Noobaa.md ODF_Prerequisites.md ; do
  ln -s ../common/"${file}"
done

cd ..

stitchmd -C tmp/ -o ../../../rendered/ODF_On_VMWare.md tmp/summary.md 

rm -rf tmp
