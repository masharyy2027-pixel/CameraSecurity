
[app]

title = Camera Security
package.name = camerasecurity
package.domain = com.hussainalbeyati

source.dir = .
source.include_exts = py,png,jpg,jpeg,mp3,xml,kv,txt

version = 1.0.0

requirements = python3==3.12.10,hostpython3==3.12.10,kivy==2.3.0

orientation = portrait
fullscreen = 0

icon.filename = %(source.dir)s/icon.png

android.permissions = CAMERA,INTERNET
android.api = 33
android.minapi = 26
android.ndk = 25b
android.archs = arm64-v8a

android.allow_backup = True
android.enable_androidx = True
android.accept_sdk_license = True

p4a.branch = master

[buildozer]

log_level = 2
warn_on_root = 1
