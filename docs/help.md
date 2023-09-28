# LibreOffice manager 2 (lomanager2)

This application helps to manage LibreOffice suite in PCLinuxOS by allowing to install and remove its core and language packages.

It is a successor of the original lomanager script.

## Contents

- [Installation](#installation)
- [Removal](#removal)
- [Upgrading](#upgrading-to-newer-version)
- [Installation from saved packages](#installation-from-saved-packages)
- [Switching localization](#switching-localization)
- [FAQ](#faq)

## Normal usage

### <a name="installation">Installation</a>

To install LibreOffice core package mark it for installation in the main window.

If you want LibreOffice to "speak" your language you should also install a relevant language pack. This can be done by clicking the "Add languages" button on the toolbar and making your choice in the new dialog that will show up. Currently LibreOffice supports some 119 languages, but the support level vary. For more than half of the most widely used ones you can expect to have localized GUI, help system and also a dictionary installed (for spell checking), however for others you will only get localized GUI and possibly a dictionary. You can install more then one language package. How to later switch between different languages in LibreOffice is described in the section [Switching localizations](#switching-localizations) below.

Once you are happy with your choices click the "Apply changes" button on the toolbar. You will see the summary of changes and once you confirm them lomanager2 will then try to download and install selected components. The option of keeping downloaded packages is explained in section [Installation from saved packages](#installation-from-saved-packages).

### <a name="removal">Removal</a>

The process of removing LibreOffice, or any of the language packs, is equally straightforward, mark them for removal/uninstall and hit the "Apply changes" button. Note that removal of LibreOffice core package will trigger the removal of all language packs.

### <a name="upgrading-to-newer-version">Upgrading to newer version</a>

Once the new LibreOffice version becomes available and gets thoroughly tested by PCLOS team you will be able to mark it for installation. Once marked it will automatically mark any already installed version for removal. At this point pressing the "Apply changes" button will first download the new version and only once this step is successful it will remove the old version and install the new one. Note that this procedure removes all existing language packs so if you want to use specific language pack you will have to manually mark it for installation in addition to the new core package just marked. This can be done in one step, simply mark desired language pack by using the "Add languages" option. If you don't do this you can add this package separately afterwards.

### <a name="downgrading">Downgrading</a>

It may happen that currently installed LibreOffice misbehaves. If this is the case PCLOS team will make one of the older LibreOffice versions available for install. The procedure of downgrading is the same as the procedure for upgrading, the only differences are that on the application startup you will get notified that a downgrade is advised and you will see that the version available for install is lower that the currently installed one.

### <a name="installation-from-saved-packages">Installation from saved packages</a>

For those who want to install LibreOffice on more then once computer and want to avoid re-downloading the packages an option to keep them is available. Once you have selected all packages you want to install mark the "Keep downloaded packages" checkbox in the apply changes confirmation dialog before proceeding.

Once install process is finished lomanager2 will show the directory to which the packages were saved. Copy or move that entire directory to the other machine(s) (but don't change its internal structure).

On the other machine instead of selecting packages again go to the menu "Tools" and select "Install from local copy". In the dialog that will show up select the directory with the packages and click "Apply".

Important remarks:

- This procedure will install packages from the selected directory and **remove** any LibreOffice packages already installed.
- If the target machine doesn't have Java installed you should, on the first machine, mark the option "Download Java" in addition to the option "Keep downloaded packages".
  - If Java is present on the target system it WILL NOT be replaced by the Java found among saved packages (lomanager2 is not meant to be used to upgrade the system, you should use a proper package manager to do that).
- Note that this procedure will not let you install individual language packages. If however LibreOffice core package is present saved language packages will be installed as well.

## <a name="switching-localization">Switching localization</a>

Once you have installed a language pack using lomanager2 you have to tell LibreOffice to use it (by default LibreOffice uses en_US locale).

Open LibreOffice and use the menu Tools->Options... to open options dialog. In that new window, in the tree view on the left, choose Language Settings->Languages. Now in the right panel the option:

- "User interface" controls the language of the interface. Switch it to one of the languages you have installed using lomanager2. For this change to take effect LibreOffice must be restarted.
- "Locale setting" is set up by LibreOffice automatically and you should not need to modify it if your entire OS is localized. If you think you need to set it yourself consult LibreOffice documentation.

## <a name="faq">FAQ</a>

1. "lomanager2 claims that my system is not fully updated and won't let me install LibreOffice"

   That's right. Since lomanager2 offers only LibreOffice version that was checked as working without problems in the current PCLOS you can only install it once your system is "current" - that is fully updated. Close lomanager2 and update your system using a package manager like Synaptic then rerun lomanager2.

2. "lomanager2 displays a message saying some package managers are running and it won't let me install or remove LibreOffice".

   Only one program at a time can use the database of packages installed in the system. lomanager2 will show you which package manager is running (usually Synaptic). Close it first and rerun lomanager2. If you don't have any package manager opened and lomanager2 is complaining try rebooting your system. Perhaps a package manager didn't close cleanly and is still running in the background.

3. "lomanager2 displays a message saying that an Office is running and it won't let me install or remove LibreOffice".

   Your currently installed LibreOffice is running. Save whatever documents you are working on at the moment and close LibreOffice then rerun lomanager2.

4. "Download fails with an error: While trying to open http://(...) an error occurred: HTTP error 404: Not Found"

   There are a few possible reasons for lomanager2 failing to download a package:

   - Your internet connections is down. Check if you can open any webpage in your browser.
   - The server lomanager2 is trying to reach is down. Copy and paste the http link to your browser and try opening it. If you get the same error (and you can open other websites) you may have to wait a bit until the server comes back online.
   - The file is really no longer present on the server. If your system is fully updated (as it should) this is odd. Report the problem on PCLOS forum.

5. "I had LibreOffice showing its menu in language X and after upgrading to a new version LibreOffice is now in English!"

   Read the section [Upgrading](#upgrading-to-newer-version) above then follow instructions in the section [Switching localizations](#switching-localization).

6. "I have a problem not described in this document."

   Head over to our forum and ask for help. There is the lomanager topic where relevant discussion takes place, use it please:

   [LibreOffice manager (lomanager) support topic](https://www.pclinuxos.com/forum/index.php/topic,59009.0.html) (opens in your browser)
