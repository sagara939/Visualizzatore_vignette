[app]

# Informazioni App
title = Comic Viewer
package.name = comicviewer
package.domain = org.comicviewer
version = 1.0.0

# Sorgenti
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json,txt
source.exclude_dirs = tests, bin, venv, __pycache__, .git

# Requisiti Python
requirements = python3,kivy==2.3.0,requests,certifi,pillow,urllib3,charset-normalizer,idna

# Orientamento schermo
orientation = portrait

# Permessi Android
android.permissions = INTERNET,ACCESS_NETWORK_STATE,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE

# Versioni API Android
android.api = 33
android.minapi = 21
android.ndk = 25b
android.sdk = 33

# Accetta licenze SDK automaticamente
android.accept_sdk_license = True

# Architetture da compilare
android.archs = arm64-v8a, armeabi-v7a

# Fullscreen
fullscreen = 0

# Presplash e icona (opzionali)
# presplash.filename = %(source.dir)s/data/presplash.png
# icon.filename = %(source.dir)s/data/icon.png

# (Android) Gradle dependencies
# android.gradle_dependencies =

# (Android) Enable AndroidX support
android.enable_androidx = True

# (Android) Wakelock per mantenere schermo attivo durante uso
android.wakelock = False

# Debug mode
# android.logcat_filters = *:S python:D

[buildozer]

# Livello log (0 = error, 1 = info, 2 = debug)
log_level = 2

# Warning se eseguito come root
warn_on_root = 1

# Percorso build
# build_dir = ./build

# Percorso bin (output APK)
# bin_dir = ./bin
