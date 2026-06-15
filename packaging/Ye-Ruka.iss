#define AppName "Є-Рука"
#define AppExeName "Ye-Ruka.exe"
#define AppVersion "2.2.0"
#define AppPublisher "Medvid Oleksii (Kico)"
#define AppId "{{B7E715A2-38B9-4DAA-9810-705502EF0D3F}"

[Setup]
AppId={#AppId}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher={#AppPublisher}
VersionInfoVersion={#AppVersion}.0
VersionInfoCompany={#AppPublisher}
VersionInfoDescription=Інсталятор програми Є-Рука
VersionInfoProductName={#AppName}
DefaultDirName={localappdata}\Programs\Ye-Ruka
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
DisableWelcomePage=no
LicenseFile=EULA_UK.txt
InfoBeforeFile=SAFETY_NOTICE_UK.txt
OutputDir=..\dist\release
OutputBaseFilename=Ye-Ruka-{#AppVersion}-Windows-x64-Setup
SetupIconFile=..\resources\icons\ye-ruka.ico
WizardImageFile=assets\installer-wizard.bmp
WizardSmallImageFile=assets\installer-small.bmp
UninstallDisplayIcon={app}\{#AppExeName}
UninstallDisplayName={#AppName} {#AppVersion}
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
ShowLanguageDialog=no
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
CloseApplications=yes
RestartApplications=no
SetupLogging=yes
MinVersion=10.0.17763

[Languages]
Name: "ukrainian"; MessagesFile: "compiler:Languages\Ukrainian.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[CustomMessages]
ukrainian.PreferencesTitle=Початкові налаштування
ukrainian.PreferencesDescription=Оберіть мову та оформлення першого запуску
ukrainian.AppLanguage=Мова застосунку:
ukrainian.AppTheme=Тема застосунку:
ukrainian.ThemeSystem=Системна
ukrainian.ThemeDark=Темна
ukrainian.ThemeLight=Світла
english.PreferencesTitle=Initial settings
english.PreferencesDescription=Choose the language and appearance for the first launch
english.AppLanguage=Application language:
english.AppTheme=Application theme:
english.ThemeSystem=System
english.ThemeDark=Dark
english.ThemeLight=Light

[Tasks]
Name: "desktopicon"; Description: "Створити ярлик на робочому столі"; GroupDescription: "Додаткові ярлики:"; Flags: unchecked

[Files]
Source: "..\dist\Ye-Ruka\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "PRIVACY_POLICY_UK.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "SAFETY_NOTICE_UK.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "EULA_UK.txt"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExeName}"; WorkingDir: "{app}"
Name: "{group}\Видалити {#AppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExeName}"; Description: "Запустити {#AppName}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: files; Name: "{app}\install_preferences.ini"

[Code]
var
  BrandByline: TNewStaticText;
  BrandVersion: TNewStaticText;
  PreferencesPage: TWizardPage;
  LanguageLabel: TNewStaticText;
  LanguageCombo: TNewComboBox;
  ThemeLabel: TNewStaticText;
  ThemeCombo: TNewComboBox;

procedure InitializeWizard();
begin
  WizardForm.Caption := '{#AppName} | Встановлення';
  WizardForm.WelcomeLabel1.Caption := 'Встановлення «{#AppName}»';
  WizardForm.WelcomeLabel1.Font.Name := 'Segoe UI';
  WizardForm.WelcomeLabel1.Font.Size := 17;
  WizardForm.WelcomeLabel1.Font.Style := [fsBold];

  WizardForm.WelcomeLabel2.Caption :=
    'Керування роботизованою кистю через камеру, сенсорну рукавицю та ручну панель.' + #13#10 + #13#10 +
    'Майстер встановить усі необхідні компоненти. Python та додаткові бібліотеки не потрібні.';
  WizardForm.WelcomeLabel2.Font.Name := 'Segoe UI';
  WizardForm.WelcomeLabel2.Font.Size := 10;

  BrandByline := TNewStaticText.Create(WizardForm);
  BrandByline.Parent := WizardForm.WelcomePage;
  BrandByline.Caption := 'BY KICO';
  BrandByline.Font.Name := 'Segoe UI';
  BrandByline.Font.Size := 11;
  BrandByline.Font.Style := [fsBold];
  BrandByline.Font.Color := $00FF8C5B;
  BrandByline.Left := WizardForm.WelcomeLabel2.Left;
  BrandByline.Top := WizardForm.WelcomePage.ClientHeight - ScaleY(58);
  BrandByline.AutoSize := True;

  BrandVersion := TNewStaticText.Create(WizardForm);
  BrandVersion.Parent := WizardForm.WelcomePage;
  BrandVersion.Caption := 'Є-Рука 2.2.0  |  Windows x64';
  BrandVersion.Font.Name := 'Segoe UI';
  BrandVersion.Font.Size := 8;
  BrandVersion.Font.Color := $00887B72;
  BrandVersion.Left := BrandByline.Left;
  BrandVersion.Top := BrandByline.Top + ScaleY(25);
  BrandVersion.AutoSize := True;

  PreferencesPage := CreateCustomPage(
    wpSelectTasks,
    CustomMessage('PreferencesTitle'),
    CustomMessage('PreferencesDescription')
  );

  LanguageLabel := TNewStaticText.Create(PreferencesPage);
  LanguageLabel.Parent := PreferencesPage.Surface;
  LanguageLabel.Caption := CustomMessage('AppLanguage');
  LanguageLabel.Left := 0;
  LanguageLabel.Top := ScaleY(18);
  LanguageLabel.AutoSize := True;

  LanguageCombo := TNewComboBox.Create(PreferencesPage);
  LanguageCombo.Parent := PreferencesPage.Surface;
  LanguageCombo.Left := 0;
  LanguageCombo.Top := LanguageLabel.Top + ScaleY(24);
  LanguageCombo.Width := ScaleX(280);
  LanguageCombo.Style := csDropDownList;
  LanguageCombo.Items.Add('Українська');
  LanguageCombo.Items.Add('English');
  if ActiveLanguage = 'english' then
    LanguageCombo.ItemIndex := 1
  else
    LanguageCombo.ItemIndex := 0;

  ThemeLabel := TNewStaticText.Create(PreferencesPage);
  ThemeLabel.Parent := PreferencesPage.Surface;
  ThemeLabel.Caption := CustomMessage('AppTheme');
  ThemeLabel.Left := 0;
  ThemeLabel.Top := LanguageCombo.Top + ScaleY(56);
  ThemeLabel.AutoSize := True;

  ThemeCombo := TNewComboBox.Create(PreferencesPage);
  ThemeCombo.Parent := PreferencesPage.Surface;
  ThemeCombo.Left := 0;
  ThemeCombo.Top := ThemeLabel.Top + ScaleY(24);
  ThemeCombo.Width := ScaleX(280);
  ThemeCombo.Style := csDropDownList;
  ThemeCombo.Items.Add(CustomMessage('ThemeSystem'));
  ThemeCombo.Items.Add(CustomMessage('ThemeDark'));
  ThemeCombo.Items.Add(CustomMessage('ThemeLight'));
  ThemeCombo.ItemIndex := 0;
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  AppLanguage: String;
  AppTheme: String;
begin
  if CurStep <> ssPostInstall then
    exit;

  if LanguageCombo.ItemIndex = 1 then
    AppLanguage := 'en'
  else
    AppLanguage := 'uk';

  case ThemeCombo.ItemIndex of
    1: AppTheme := 'dark';
    2: AppTheme := 'light';
  else
    AppTheme := 'system';
  end;

  SetIniString('preferences', 'language', AppLanguage, ExpandConstant('{app}\install_preferences.ini'));
  SetIniString('preferences', 'theme', AppTheme, ExpandConstant('{app}\install_preferences.ini'));
end;
