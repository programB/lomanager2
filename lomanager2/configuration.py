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
import logging
import pathlib

from i18n import _

log = logging.getLogger("lomanager2_logger")


def make_base_ver(full_version: str) -> str:
    # base version comprises of the first 2 numbers of the full version
    # eg. 7.5.4.2 -> 7.5
    return ".".join(full_version.split(".")[:2])


def make_minor_ver(full_version: str) -> str:
    # minor version comprises of the first 3 numbers of the full version
    # eg. 7.5.4.2 -> 7.5.4
    return ".".join(full_version.split(".")[:3])


# latest_available_LO_version should be full version number (4 segments)
# (all version strings are derived from it unless overridden by
#  non empty force_specific_LO_version which should also comprise 4 segments)
latest_available_LO_version = "7.6.2.1"
force_specific_LO_version = ""
# force_specific_LO_version = "7.5.4.2"

latest_available_clipart_version = (
    make_base_ver(latest_available_LO_version)
    if not force_specific_LO_version
    else make_base_ver(force_specific_LO_version)
)


# Global read-only definitions
temporary_dir = pathlib.Path("/tmp/lomanager2-tmp")
working_dir = temporary_dir.joinpath("working_directory")
verified_dir = temporary_dir.joinpath("verified_storage")
offline_copy_dir = pathlib.Path("/tmp/lomanager2-saved_packages")

# URLs
PCLOS_repo_base_url = "https://ftp.nluug.nl/"
PCLOS_repo_path = "/os/Linux/distr/pclinuxos/pclinuxos/apt/pclinuxos/64bit/RPMS.x86_64/"
DocFund_base_url = "http://download.documentfoundation.org/libreoffice/stable/"
DocFund_path_ending = "/rpm/x86_64/"

# List of languages supported by LibreOffice
# Supported means that there is a langpack
# with a given language code.
# a) Note that availability of a langpack does
# not imply that a helppack exists for that language.
# b) Here language code should be understood
# as a language code proper extended with a region code
# (if it exists) eg. en-US
supported_langs = {
    "af": "Afrikaans",
    "am": "Amharic",
    "ar": "Arabic",
    "as": "Assamese",
    "ast": "Asturian",
    "be": "Belarusian",
    "bg": "Bulgarian",
    "bn": "Bengali",
    "bn-IN": "Bengali (India)",
    "bo": "Tibetan (PR China)",
    "br": "Breton",
    "brx": "Bodo (India)",
    "bs": "Bosnian",
    "ca": "Catalan",
    "ca-valencia": "Catalan (Valencian)",
    "ckb": "Kurdish (Central)",
    "cs": "Czech",
    "cy": "Welsh",
    "da": "Danish",
    "de": "German",
    "dgo": "Dogri",
    "dsb": "Sorbian (Lower)",
    "dz": "Dzongkha",
    "el": "Greek",
    "en-GB": "English (United Kingdom)",
    "en-US": "English (USA)",
    "en-ZA": "English (South Africa)",
    "eo": "Esperanto",
    "es": "Spanish",
    "et": "Estonian",
    "eu": "Basque",
    "fa": "Farsi",
    "fi": "Finnish",
    "fr": "French",
    "fur": "Friulian",
    "fy": "Frisian",
    "ga": "Gaelic (Ireland)",
    "gd": "Gaelic (Scotland)",
    "gl": "Galician",
    "gu": "Gujarati",
    "gug": "Guaraní (Paraguayan)",
    "he": "Hebrew",
    "hi": "Hindi (India)",
    "hr": "Croatian",
    "hsb": "Sorbian (Upper)",
    "hu": "Hungarian",
    "id": "Indonesian",
    "is": "Icelandic",
    "it": "Italian",
    "ja": "Japanese",
    "ka": "Georgian",
    "kab": "Kabyle",
    "kk": "Kazakh",
    "km": "Khmer",
    "kmr-Latn": "Kurdish",
    "kn": "Kannada (India)",
    "ko": "Korean",
    "kok": "Konkani",
    "ks": "Kashmiri (Kashmir)",
    "lb": "Luxembourgish",
    "lo": "Lao",
    "lt": "Lithuanian",
    "lv": "Latvian",
    "mai": "Maithili",
    "mk": "Macedonian",
    "ml": "Malayalam (India)",
    "mn": "Mongolian",
    "mni": "Manipuri",
    "mr": "Marathi (India)",
    "my": "Burmese",
    "nb": "Norwegian (Bokmaal)",
    "ne": "Nepali",
    "nl": "Dutch",
    "nn": "Norwegian (Nynorsk)",
    "nr": "Ndebele",
    "nso": "Northern Sotho",
    "oc": "Occitan",
    "om": "Oromo",
    "or": "Oriya (India)",
    "pa-IN": "Punjabi (India)",
    "pl": "Polish",
    "pt": "Portuguese (Portugal)",
    "pt-BR": "Portuguese (Brazil)",
    "ro": "Romanian",
    "ru": "Russian",
    "rw": "Kinyarwanda",
    "sa-IN": "Sanskrit (India)",
    "sat": "Santali",
    "sd": "Sindhi",
    "si": "Sinhala",
    "sid": "Sidama",
    "sk": "Slovak",
    "sl": "Slovenian",
    "sq": "Albanian",
    "sr": "Serbian",
    "sr-Latn": "Serbian Latin (Serbia)",
    "ss": "Swati",
    "st": "Sotho",
    "sv": "Swedish",
    "sw-TZ": "Swahili (Tanzania)",
    "szl": "Silesian",
    "ta": "Tamil (India)",
    "te": "Telugu (India)",
    "tg": "Tajik",
    "th": "Thai",
    "tn": "Tswana",
    "tr": "Turkish",
    "ts": "Tsonga",
    "tt": "Tatar",
    "ug": "Uyghur",
    "uk": "Ukrainian",
    "uz": "Uzbek",
    "ve": "Venda",
    "vec": "Venetian",
    "vi": "Vietnamese",
    "xh": "Xhosa",
    "zh-CN": "Chinese (simplified)",
    "zh-TW": "Chinese (traditional)",
    "zu": "Zulu",
}

# List of language codes for which a helppack exists.
# fmt: off
existing_helppacks = [
    "en-US", "he", "ar", "en-GB", "en-ZA", "lo", "ro", "bs", "cs",
    "da", "eo", "et", "eu", "fi", "gu", "hi", "hr", "hsb", "id", "is",
    "lv", "mk", "nb", "nn", "sid", "sl", "sq", "sv", "tg", "ug", "vi",
    "ast", "ca", "ca-valencia", "de", "dsb", "es", "fr", "gl", "it",
    "ka", "ko", "lt", "nl", "om", "pl", "pt-BR", "pt", "si", "sk",
    "tr", "zh-CN", "am", "bn", "bo", "hu", "ne", "zh-TW", "bg", "dz",
    "ru", "ta", "uk", "bn-IN", "ja", "km", "el"
    ]
# fmt: on

button_sizing_string = "awesome lomanager2"
