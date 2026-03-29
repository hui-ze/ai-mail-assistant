; 邮件智能助手 v1.0.0 安装脚本
; Inno Setup Compiler 6.x

#define MyAppName "邮件智能助手"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Mail Assistant Team"
#define MyAppExeName "邮件智能助手.exe"
#define MyAppDescription "AI-powered email management assistant"

[Setup]
; 应用信息
AppId={{8F3D9A7B-4C2E-4F1B-9D8E-6A5B7C3D2E1F}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL=https://github.com/mail-assistant
AppSupportURL=https://github.com/mail-assistant/issues
AppUpdatesURL=https://github.com/mail-assistant/releases

; 默认安装路径
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}

; 输出设置
OutputDir=dist
OutputBaseFilename=邮件智能助手-Setup-v{#MyAppVersion}
SetupIconFile=assets\icons\app.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern

; 权限和架构
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
MinVersion=10.0.26200
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

; 许可协议
;LicenseFile=LICENSE.txt

; 界面设置
ShowLanguageDialog=no
LanguageDetectionMethod=uilanguage
UninstallDisplayIcon={app}\{#MyAppExeName}
UninstallDisplayName={#MyAppName}

; 安装界面配置
WindowVisible=no
WindowShowCaption=no
WindowResizable=no
CreateAppDir=yes

; 许可和文档
InfoBeforeFile=dist\README.txt

[Languages]
Name: "chinesesimplified"; MessagesFile: "compiler:Languages\ChineseSimplified.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: checked
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; 主程序
Source: "dist\邮件智能助手\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\邮件智能助手\_internal\*"; DestDir: "{app}\_internal"; Flags: ignoreversion recursesubdirs createallsubdirs

; 文档
Source: "dist\README.txt"; DestDir: "{app}"; Flags: ignoreversion isreadme

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:ProgramOnTheWeb,{#MyAppName}}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: quicklaunchicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[Code]
// 检查是否已安装
function InitializeSetup(): Boolean;
var
  OldVersion: String;
  UninstallString: String;
  ErrorCode: Integer;
begin
  // 检查是否已安装旧版本
  if RegQueryStringValue(HKEY_LOCAL_MACHINE,
    'Software\Microsoft\Windows\CurrentVersion\Uninstall\{#MyAppName}_is1',
    'UninstallString', UninstallString) then
  begin
    UninstallString := RemoveQuotes(UninstallString);
    if MsgBox('检测到已安装 {#MyAppName}，是否先卸载旧版本？', mbConfirmation, MB_YESNO) = IDYES then
    begin
      UninstallString := UninstallString + ' /SILENT';
      Exec(UninstallString, '', '', SW_HIDE, ewWaitUntilTerminated, ErrorCode);
    end;
  end;
  Result := True;
end;

// 安装完成后显示说明
procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    // 可以在这里添加安装后的操作
  end;
end;

// 卸载前的清理
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  DataPath: string;
begin
  if CurUninstallStep = usPostUninstall then
  begin
    // 询问是否删除用户数据
    if MsgBox('是否删除用户数据文件？'#13#10'(数据库、日志等文件位于用户目录下)', 
      mbConfirmation, MB_YESNO) = IDYES then
    begin
      // 删除用户数据目录
      DataPath := ExpandConstant('{userappdata}\..\.mail-assistant');
      if DirExists(DataPath) then
      begin
        DelTree(DataPath, True, True, True);
      end;
    end;
  end;
end;
