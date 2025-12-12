project('python-xapp', version : '3.0.1', meson_version : '>=0.47.0')

pymod = import('python')
python3 = pymod.find_installation(get_option('python_target'))

i18n = import('i18n')
gettext_package = meson.project_name()
podir = meson.source_root() / 'po'

subdir('po')
subdir('xapp')

