; 账号仓库管理系统 安装脚本
Unicode true
!include "MUI2.nsh"

Name "账号仓库管理系统"
OutFile "dist\账号仓库管理系统_Setup.exe"
InstallDir "$PROGRAMFILES\账号仓库管理系统"
RequestExecutionLevel admin

!define MUI_ABORTWARNING

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_LANGUAGE "SimpChinese"

Section "Install"
  SetOutPath "$INSTDIR"
  File "dist\账号仓库管理系统.exe"

  CreateDirectory "$SMPROGRAMS\账号仓库管理系统"
  CreateShortcut "$SMPROGRAMS\账号仓库管理系统\账号仓库管理系统.lnk" "$INSTDIR\账号仓库管理系统.exe"
  CreateShortcut "$SMPROGRAMS\账号仓库管理系统\卸载.lnk" "$INSTDIR\uninstall.exe"
  CreateShortcut "$DESKTOP\账号仓库管理系统.lnk" "$INSTDIR\账号仓库管理系统.exe"

  WriteUninstaller "$INSTDIR\uninstall.exe"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\账号仓库管理系统" \
    "DisplayName" "账号仓库管理系统"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\账号仓库管理系统" \
    "UninstallString" "$INSTDIR\uninstall.exe"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\账号仓库管理系统" \
    "DisplayIcon" "$INSTDIR\账号仓库管理系统.exe"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\账号仓库管理系统" \
    "Publisher" "账号仓库管理系统"
  WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\账号仓库管理系统" \
    "NoModify" 1
  WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\账号仓库管理系统" \
    "NoRepair" 1
SectionEnd

Section "Uninstall"
  Delete "$INSTDIR\账号仓库管理系统.exe"
  Delete "$INSTDIR\uninstall.exe"
  RMDir "$INSTDIR"
  Delete "$SMPROGRAMS\账号仓库管理系统\账号仓库管理系统.lnk"
  Delete "$SMPROGRAMS\账号仓库管理系统\卸载.lnk"
  RMDir "$SMPROGRAMS\账号仓库管理系统"
  Delete "$DESKTOP\账号仓库管理系统.lnk"
  DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\账号仓库管理系统"
SectionEnd
