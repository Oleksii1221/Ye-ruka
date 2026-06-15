from types import SimpleNamespace

from ye_ruka.core.startup import apply_install_preferences


class _Config:
    def __init__(self):
        self.data = {"language": "uk", "theme": "dark"}
        self.saved = False

    def save(self):
        self.saved = True


def test_first_run_applies_installer_language_and_theme(tmp_path):
    path = tmp_path / "install_preferences.ini"
    path.write_text("[preferences]\nlanguage=en\ntheme=system\n", encoding="utf-8")
    config = _Config()

    assert apply_install_preferences(config, path, first_run=True)
    assert config.data == {"language": "en", "theme": "system"}
    assert config.saved
    assert not path.exists()


def test_upgrade_discards_installer_preferences_without_overwriting_profile(tmp_path):
    path = tmp_path / "install_preferences.ini"
    path.write_text("[preferences]\nlanguage=en\ntheme=light\n", encoding="utf-8")
    config = _Config()

    assert not apply_install_preferences(config, path, first_run=False)
    assert config.data == {"language": "uk", "theme": "dark"}
    assert not config.saved
    assert not path.exists()
