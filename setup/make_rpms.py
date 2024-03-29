"""
Copyright (C) 2023 programB

This file is part of lomanager2.

lomanager2 is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License version 3
as published by the Free Software Foundation.

lomanager2 is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with lomanager2.  If not, see <http://www.gnu.org/licenses/>.
"""
import pathlib

import common

__release__ = "1"

# fmt:off
spec_text = (
    f"#Document Foundation release schedule" + "\n"
    r"#  Wednesday - builds are uploaded here: https://dev-builds.libreoffice.org/pre-releases/rpm/x86_64/" + "\n"
    r"#  Thursday  - builds are uploaded on mirrors" + "\n"
    r"#  Friday    - builds are available via the official pre-release site" + "\n"
    r"#The final release is usually announced on Wednesday, few days after the final release candidate is out." + "\n"
    rf"%define name {common.package}" + "\n"
    r"name:           %{name}" + "\n"
    rf"version:        {common.version}" + "\n"
    rf"Release:        %mkrel {__release__}" + "\n"
    r"License:        GNU General Public License 2 (GPL)" + "\n"
    r"URL:            https://www.pclinuxos.com/forum/index.php/topic=59009.0.html" + "\n"
    r"Source:         %{name}-%{version}.tar.xz" + "\n"
    r"Source1:        help.md" + "\n"
    r"Source2:        LICENSE.md" + "\n"
    r"Summary:        Script to install LibreOffice in one of 110 languages" + "\n"
    r"Summary(de):    Skript zur Installation von LibreOffice in einer von 110 Sprachen" + "\n"
    r"Summary(fr):    Script pour installer LibreOffice en 110 langues" + "\n"
    r"Summary(pl):    Program do instalacji/uaktualniania/usuwania LibreOffice" + "\n"
    r"Group:          Office" + "\n"
    r"Requires:       gksu python3-pyside2-core python3-pyside2-gui python3-pyside2-widgets python3-pyside2-network" + "\n"
    r"Requires:       apt apt-common %{_lib}gnome-vfs2_0 python-pillow locales-en libnotify" + "\n"
    r"Requires:       desktop-common-data >= 2010-11	" + "\n"
    # r"Conflicts:      lomanager" + "\n"
    r"Obsoletes:      %name < %version" + "\n"
    rf"Provides:       {common.package} = %version-%release" + "\n"
    r"BuildRoot:      %{_tmppath}/%{name}-%{version}-build" + "\n"
    r"AutoReqProv:    no" + "\n"
    r"" + "\n"
    r"%description" + "\n"
    rf"To manage LibreOffice start the program {common.package} from:" + "\n"
    r"PCmenu -> Software Center -> LibreOffice Manger" + "\n"
    r"and follow the instructions." + "\n"
    r"" + "\n"
    r"The user-friendly GUI application that helps manage the LibreOffice suite" + "\n"
    r"(install/update/remove core packages and locales)." + "\n"
    r"" + "\n"
    r"%description -l de" + "\n"
    rf"Das benutzerfreundliche und verbose bash-Skript {common.package} automatisiert das Hinzufügen von" + "\n"
    r"LibreOffice in der Sprache des Benutzers/System-Lokalisierung. Sie haben nun eine einfache" + "\n"
    r"Ein-Schritt-Lösung zur Installation von LibreOffice in Englisch oder anderen Sprachen wie" + "\n"
    r"Arabisch, Französisch, Chinesisch, Spanisch, Deutsch, und sogar Exoten wie Zulu oder Walisisch" + "\n"
    r"" + "\n"
    r"%description -l fr" + "\n"
    rf"A user-friendly et verbose-script bash {common.package} automatise l'ajout de" + "\n"
    r"LibreOffice dans la langue de l'utilisateur / locale dans le système. Vous" + "\n"
    r"avez maintenant une seule étape facile solution pour installer LibreOffice en" + "\n"
    r"français ou en langues de grande diffusion comme l'arabe, français," + "\n"
    r"chinois, espagnol, allemand, et même exotiques, comme le zoulou ou gallois." + "\n"
    r"" + "\n"
    r"%description -l nl" + "\n"
    rf"Een gebruiksvriendelijke en verbose bash-script {common.package} automatiseert het toevoegen" + "\n"
    r"LibreOffice in de taal van de gebruiker / locale aan het systeem." + "\n"
    r"U hebt nu een eenvoudige een-staps oplossing om LibreOffice installeren in het Engels" + "\n"
    r"of in gesproken talen zoals Arabisch, Frans, Chinees, Spaans, Duits," + "\n"
    r"en zelfs exotische zoals Zulu of Welsh." + "\n"
    r"" + "\n"
    r"%description -l es" + "\n"
    rf"Un usuario-bash amable y detallado-script automatiza {common.package} añadir" + "\n"
    r"LibreOffice en la lengua del usuario / configuración regional del sistema." + "\n"
    r"Ahora tiene una fácil solución de paso para instalar LibreOffice en Inglés" + "\n"
    r"o se habla idiomas como el árabe, francés, chino, español, alemán," + "\n"
    r"y incluso los exóticos como Zulu o el galés." + "\n"
    r"" + "\n"
    r"%description -l it" + "\n"
    rf"A user-friendly e verbose bash-script {common.package} automatizza l'aggiunta di" + "\n"
    r"LibreOffice nella lingua dell'utente / locale al sistema." + "\n"
    r"Avete ora un facile soluzione passo per installare LibreOffice in italiano" + "\n"
    r"o parlate in lingue come l'arabo, francese, cinese, spagnolo, tedesco," + "\n"
    r"e perfino quelli esotici, come Zulu o gallesi." + "\n"
    r"" + "\n"
    r"" + "\n"
    r"%description -l pl" + "\n"
    r"Aby zaktualizować/zainstalować LibreOffice klikaj:" + "\n"
    r"PCmenu -> Software Center -> Instalator LibreOffice" + "\n"
    r"a następnie postępuj zgodnie z instrukcjami." + "\n"
    rf"{common.package} to przyjazny dla użytkownika program który automatyzuje " + "\n"
    r"zarządzanie" + "\n"
    r"LibreOffice (instalacja/aktualizacja/usuwanie i dodawanie języka)" + "\n"
    r"Jest to proste rozwiązanie jednoetapowe do zarządzania LibreOffice w " + "\n"
    r"kilkunastu językach takich jak:" + "\n"
    r"polski, angielski, arabski, francuski, chiński, hiszpański, niemiecki, " + "\n"
    r"itp...." + "\n"
    r"a nawet egzotycznych jak Zulu lub walijski." + "\n"
    r"" + "\n"
    r"%description -l sr" + "\n"
    r"Корисника и детаљни-басх-скрипта ГетОпенОффице аутоматизује додавање" + "\n"
    r"ОпенОффице на језику корисника / лоцале систем." + "\n"
    r"Сада сте једноставно један корак решење да инсталирате ОпенОффице на енглеском" + "\n"
    r"или у широкој употреби језика као што су арапски, француски, кинески, шпански, немачки," + "\n"
    r"па чак и оних попут егзотичне зулу или велшки." + "\n"
    r"" + "\n"
    r"%prep" + "\n"
    r"" + "\n"
    r"%setup -q" + "\n"
    r"" + "\n"
    r"%build" + "\n"
    r"" + "\n"
    r"%install" + "\n"
    r"rm -rf %{buildroot}" + "\n"
    r"" + "\n"
    r"mkdir -p %{buildroot}/%{_bindir}" + "\n"
    r"install -m 755 %{name} %{buildroot}/%{_bindir}/%{name}" + "\n"
    r"" + "\n"
    r"mkdir -p $RPM_BUILD_ROOT/%_datadir/applications" + "\n"
    r"cat > $RPM_BUILD_ROOT%{_datadir}/applications/%{name}.desktop << EOF" + "\n"
    r"[Desktop Entry]" + "\n"
    r"Encoding=UTF-8" + "\n"
    r"Version=1.0" + "\n"
    r"Name=LibreOffice Manager" + " 2\n"
    r"Name[ar]=LibreOffice مدير" + " 2\n"
    r"Name[bg]=LibreOffice мениджър" + " 2\n"
    r"Name[ca]=Gestor del LibreOffice" + " 2\n"
    r"Name[cs]=LibreOffice manažer" + " 2\n"
    r"Name[da]=LibreOffice Manager" + " 2\n"
    r"Name[de]=LibreOffice Manager" + " 2\n"
    r"Name[el]=Διαχειριστής LibreOffice" + " 2\n"
    r"Name[es]=Manager de LibreOffice" + " 2\n"
    r"Name[fi]=LibreOffice johtaja" + " 2\n"
    r"Name[fr]=Gestionnaire de LibreOffice" + " 2\n"
    r"Name[it]=LibreOffice Manager" + " 2\n"
    r"Name[ja]=LibreOfficeマネージャ" + " 2\n"
    r"Name[nl]=LibreOffice Beheerder" + " 2\n"
    r"Name[pl]=Instalator LibreOffice" + " 2\n"
    r"Name[pt]=Manager do LibreOffice" + " 2\n"
    r"Name[ru]=LibreOffice менеджер" + " 2\n"
    r"Name[sr]=Менаџер LibreOffice" + " 2\n"
    r"Name[sv]=LibreOffice chef" + " 2\n"
    r"Name[tr]=LibreOffice yöneticisi" + " 2\n"
    r"Name[uk]=LibreOffice менеджер" + " 2\n"
    r"Name[zh]=LibreOffice经理" + " 2\n"
    r"GenericName=LibreOffice Manager" + " 2\n"
    r"Type=Application" + "\n"
    rf"Exec= MY_SU=\`which kdesu 2>/dev/null\` || MY_SU=\`which gksu 2>/dev/null\`; \$MY_SU {common.package}" + "\n"
    r"Icon=office_section.png" + "\n"
    r"Comment=Install, update, remove or add other LibreOffice languages" + "\n"
    r"Comment[ar]=LibreOffice تثبيت وتحديث وإزالة أو إضافة لغات أخرى " + "\n"
    r"Comment[bg]=Инсталиране, Премахване на, обновяване или добавяне на локализация за LibreOffice" + "\n"
    r"Comment[ca]=Installar, actualitzar, eliminar o afegir altres idiomes de LibreOffice" + "\n"
    r"Comment[cs]=Instalujte, odstante, aktualizujte nebo pridejte lokalizaci LibreOffice" + "\n"
    r"Comment[da]=Installere, opdatere, fjerne eller tilføje andre LibreOffice sprog" + "\n"
    r"Comment[de]=Installieren, update, entfernen von LibreOffice in verschiedenen Sprachen" + "\n"
    r"Comment[el]=Install, Ολική διαγραφή του, upgrade, ή πρόσθεση LibreOffice locale" + "\n"
    r"Comment[es]=Instalar, desinstalar, actualizar o agregar la localización de LibreOffice" + "\n"
    r"Comment[fi]=Asentaa, päivittää, poistaa tai lisätä muita LibreOffice kielillä" + "\n"
    r"Comment[fr]=Installez, mettre à jour, supprimez LibreOffice dans la langue de votre choix" + "\n"
    r"Comment[it]=Installa, aggiorna, elimina o aggiungi LibreOffice in lingue diverse" + "\n"
    r"Comment[ja]=インストール、更新、削除、または他のLibreOffice言語を追加する" + "\n"
    r"Comment[nl]=Installeren, update, verwijderen van LibreOffice in verschillende talen" + "\n"
    r"Comment[pl]=Install, calkowite usuniecie, upgrade, lub dolacz LibreOffice locale" + "\n"
    r"Comment[pt]=Instalar, remover, upgrade, ou adicionar LibreOffice locale" + "\n"
    r"Comment[ru]=Установка, Полностью удалить, обновление или добавление LibreOffice locale" + "\n"
    r"Comment[sr]=Инсталирајте или ажурирајте LibreнОфис програм на жељеном језику" + "\n"
    r"Comment[sv]=Installera, flytta, uppdatera LibreOffice på ditt språk." + "\n"
    r"Comment[tr]=Yükleme, güncelleme kaldırmak veya diğer LibreOffice dilleri ekleyin" + "\n"
    r"Comment[uk]=Інсталювати, Видалення, оновити або додати LibreOffice locale" + "\n"
    r"Comment[zh]=安装，更新，删除或添加其他LibreOffice语言" + "\n"
    r"Categories=X-MandrivaLinux-System-Configuration-Packaging" + "\n"
    r"Comment=Manage installation/update/removal and localization of LibreOffice" + "\n"
    r"Terminal=false" + "\n"
    r"StartupNotify=true" + "\n"
    r"EOF" + "\n"
    r"" + "\n"
    r"" + "\n"
    r"#translations" + "\n"
    r"mkdir -p $RPM_BUILD_ROOT/%_datadir/locale/bg/LC_MESSAGES" + "\n"
    r"mkdir -p $RPM_BUILD_ROOT/%_datadir/locale/ca/LC_MESSAGES" + "\n"
    r"mkdir -p $RPM_BUILD_ROOT/%_datadir/locale/cs/LC_MESSAGES" + "\n"
    r"mkdir -p $RPM_BUILD_ROOT/%_datadir/locale/de/LC_MESSAGES" + "\n"
    r"mkdir -p $RPM_BUILD_ROOT/%_datadir/locale/el/LC_MESSAGES" + "\n"
    r"mkdir -p $RPM_BUILD_ROOT/%_datadir/locale/es/LC_MESSAGES" + "\n"
    r"mkdir -p $RPM_BUILD_ROOT/%_datadir/locale/fr/LC_MESSAGES" + "\n"
    r"mkdir -p $RPM_BUILD_ROOT/%_datadir/locale/it/LC_MESSAGES" + "\n"
    r"mkdir -p $RPM_BUILD_ROOT/%_datadir/locale/nl/LC_MESSAGES" + "\n"
    r"mkdir -p $RPM_BUILD_ROOT/%_datadir/locale/pl/LC_MESSAGES" + "\n"
    r"mkdir -p $RPM_BUILD_ROOT/%_datadir/locale/pt/LC_MESSAGES" + "\n"
    r"mkdir -p $RPM_BUILD_ROOT/%_datadir/locale/ru/LC_MESSAGES" + "\n"
    r"mkdir -p $RPM_BUILD_ROOT/%_datadir/locale/sr/LC_MESSAGES" + "\n"
    r"mkdir -p $RPM_BUILD_ROOT/%_datadir/locale/uk/LC_MESSAGES" + "\n"
    r"" + "\n"
    r"" + "\n"
    rf"install -m 0644 {common.package}_bg.mo $RPM_BUILD_ROOT/%_datadir/locale/bg/LC_MESSAGES/{common.package}.mo" + "\n"
    rf"install -m 0644 {common.package}_ca.mo $RPM_BUILD_ROOT/%_datadir/locale/ca/LC_MESSAGES/{common.package}.mo" + "\n"
    rf"install -m 0644 {common.package}_cs.mo $RPM_BUILD_ROOT/%_datadir/locale/cs/LC_MESSAGES/{common.package}.mo" + "\n"
    rf"install -m 0644 {common.package}_de.mo $RPM_BUILD_ROOT/%_datadir/locale/de/LC_MESSAGES/{common.package}.mo" + "\n"
    rf"install -m 0644 {common.package}_el.mo $RPM_BUILD_ROOT/%_datadir/locale/el/LC_MESSAGES/{common.package}.mo" + "\n"
    rf"install -m 0644 {common.package}_es.mo $RPM_BUILD_ROOT/%_datadir/locale/es/LC_MESSAGES/{common.package}.mo" + "\n"
    rf"install -m 0644 {common.package}_fr.mo $RPM_BUILD_ROOT/%_datadir/locale/fr/LC_MESSAGES/{common.package}.mo" + "\n"
    rf"install -m 0644 {common.package}_it.mo $RPM_BUILD_ROOT/%_datadir/locale/it/LC_MESSAGES/{common.package}.mo" + "\n"
    rf"install -m 0644 {common.package}_nl.mo $RPM_BUILD_ROOT/%_datadir/locale/nl/LC_MESSAGES/{common.package}.mo" + "\n"
    rf"install -m 0644 {common.package}_pl.mo $RPM_BUILD_ROOT/%_datadir/locale/pl/LC_MESSAGES/{common.package}.mo" + "\n"
    rf"install -m 0644 {common.package}_pt.mo $RPM_BUILD_ROOT/%_datadir/locale/pt/LC_MESSAGES/{common.package}.mo" + "\n"
    rf"install -m 0644 {common.package}_ru.mo $RPM_BUILD_ROOT/%_datadir/locale/ru/LC_MESSAGES/{common.package}.mo" + "\n"
    rf"install -m 0644 {common.package}_sr.mo $RPM_BUILD_ROOT/%_datadir/locale/sr/LC_MESSAGES/{common.package}.mo" + "\n"
    rf"install -m 0644 {common.package}_uk.mo $RPM_BUILD_ROOT/%_datadir/locale/uk/LC_MESSAGES/{common.package}.mo" + "\n"
    r"" + "\n"
    r"#Documents" + "\n"
    r"mkdir -p %{buildroot}/%_datadir/doc/%{name}" + "\n"
    r"install -m 0644 %SOURCE1 %{buildroot}/%_datadir/doc/%{name}/help.md" + "\n"
    r"install -m 0644 %SOURCE2 %{buildroot}/%_datadir/doc/%{name}/LICENSE.md" + "\n"
    r"" + "\n"
    r"#help ldconfig find the libs" + "\n"
    r"mkdir -p %{buildroot}/etc/ld.so.conf.d" + "\n"
    r"cat > %{buildroot}/etc/ld.so.conf.d/libreoffice.conf << EOF" + "\n"
    r"/opt/libreoffice7.3" + "\n"
    r"EOF" + "\n"
    r"" + "\n"
    r"%posttrans" + "\n"
    r"SYSUSER=$(who |cut -d' ' -f1)" + "\n"
    "su $SYSUSER -c 'notify-send \"Updated version of LibreOffice is available\" \"Run LibreOffice Manager 2 to install it\" -i /usr/share/icons/office_section.png -t 10000'" + "\n"
    r"" + "\n"
    r"/sbin/ldconfig" + "\n"
    r"" + "\n"
    r"%files " + "\n"
    r"%defattr(-, root, root)" + "\n"
    r"%{_bindir}/%{name}" + "\n"
    r"%_datadir/applications/%{name}.desktop" + "\n"
    rf"%_datadir/locale/*/LC_MESSAGES/{common.package}.mo" + "\n"
    r"/etc/ld.so.conf.d/libreoffice.conf" + "\n"
    r"%_datadir/doc/lomanager2/help.md" + "\n"
    r"%_datadir/doc/lomanager2/LICENSE.md" + "\n"
    r"" + "\n"
    r"%changelog" + "\n"
    r"* Mon Oct 2 2023 pp - 0.1.0-1programB2023" + "\n"
    r"- Initial release" + "\n"
    r"" + "\n"
)
# fmt:on


def create_spec_file(target: pathlib.Path):
    print(f"Creating spec file {target}")
    with open(target, "w") as spec_f:
        spec_f.write(spec_text)
