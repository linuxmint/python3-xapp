
def l10n(domain, locale_dir="/usr/share/locale"):
    """
    Initialize gettext and locale bindings for the given app.
    Returns:
        function: The gettext translation function `_` for convenience.
    """
    import gettext
    import locale
    locale.bindtextdomain(domain, locale_dir)
    gettext.bindtextdomain(domain, locale_dir)
    gettext.textdomain(domain)
    return gettext.gettext

__all__ = ["l10n"]
