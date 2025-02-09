#!/bin/bash
#
# Tested in Ubuntu 20.04.2 LTS.
# This script must strictly contain line endings in Linux format for correct work.
# Install QT5 dev tools packages before run this script, by the following commands:
#
# sudo apt update
# sudo apt install -y qttools5-dev-tools
# sudo apt install -y pyqt5-dev-tools
#
# This is array of supported languages. New languages, must be added to it.
languages=(zh-TW)
for lang in ${languages[*]}
do
   # Check if fastners_$lang.ts exist
   if [ -f "asm4_$lang.ts" ]; then
      if [ $lang = "zh-TW" ]; then
         targetstr="zh_TW"
         ostr=asm4_zh-TW.ts
      elif [ $lang = "zh-CN" ]; then
         targetstr="zh_CN"
         ostr=asm4_zh-CN.ts
      fi
      echo -e '\033[1;32m\n     <<< Update translation for '$lang' language >>> \n\033[m';
      # Creation of uifiles.ts file from ../*.ui files with designation of language code
   #   lupdate ../*.ui -ts uifiles.ts -source-language en_US -target-language $targetstr -no-obsolete
      # Creation of pyfiles.ts file from ../*.py files
      lupdate-qt6 ../../*.py -ts pyfiles.ts -verbose
      # Join uifiles.ts and pyfiles.ts files to Asm4.ts
      lconvert -i ../../../title_asm4.ts pyfiles.ts -o asm4.ts -source-language en_US -no-obsolete -sort-contexts -verbose
      # Join Asm4.ts to exist Asm4_(language).ts file ( -no-obsolete)
      lconvert -i ../../../title_asm4.ts asm4.ts asm4_$lang.ts -o $ostr -source-language en_US -target-language $targetstr -no-obsolete -sort-contexts -verbose
      # (Release) Creation of *.qm file from Asm4_(language).ts
      lrelease-qt6 asm4_$lang.ts
      # Delete unused files
      # rm uifiles.ts
      # rm pyfiles.ts
      # rm Asm4.ts
   else
      if [ $lang = "zh-TW" ]; then
         targetstr="zh_TW"
      elif [ $lang = "zh-CN" ]; then
         targetstr="zh_CN"
      fi
      echo -e '\033[1;33m\n     <<< Create files for added '$lang' language >>> \n\033[m';
      # Creation of uifiles.ts file from ../*.ui files with designation of language code
      lupdate ../../*.ui -ts uifiles.ts -source-language en_US -target-language $targetstr -no-obsolete
      # Creation of pyfiles.ts file from ../*.py files
      pylupdate5 ../../*.py -ts pyfiles.ts -verbose
      # Join uifiles.ts and pyfiles.ts files to Asm4_$lang.ts
      lconvert -i title.ts uifiles.ts pyfiles.ts -o asm4_$lang.ts
      # Delete unused files
      rm uifiles.ts
      rm pyfiles.ts
   fi
done
