import pytest
from personas.prompt_builder import PersonaConfig, build_system_prompt, PersonaValidationError


class TestPersonaConfig:
    """Tests for PersonaConfig validation."""

    def test_valid_config_creates_successfully(self):
        cfg = PersonaConfig(
            version_codename="ChatGPT 26.2: Redwood",
            cls="Mage",
            spec="Teacher",
            mode="Play",
            verbosity=6,
            humor=4,
            assertiveness=6,
            creativity=5,
            formality=5,
            empathy=5,
            technical_level=5,
            patience=5)
        assert cfg.cls == "Mage"
        assert cfg.verbosity == 6

    def test_config_with_avatar_creates_successfully(self):
        cfg = PersonaConfig(
            version_codename="ChatGPT 26.2: Redwood",
            cls="Mage",
            spec="Teacher",
            mode="Play",
            verbosity=6,
            humor=4,
            assertiveness=6,
            creativity=5,
            formality=5,
            empathy=5,
            technical_level=5,
            patience=5,
            avatar="🧙‍♂️")
        assert cfg.avatar == "🧙‍♂️"

    def test_verbosity_below_minimum_raises(self):
        with pytest.raises(PersonaValidationError, match="verbosity must be between 1 and 10"):
            PersonaConfig(
                version_codename="Test",
                cls="Mage",
                spec="Teacher",
                mode="Play",
                verbosity=0,  # Invalid: min is 1
                humor=4,
                assertiveness=6,
                creativity=5,
                formality=5,
                empathy=5,
                technical_level=5,
                patience=5,
            )
    def test_verbosity_above_maximum_raises(self):
        with pytest.raises(PersonaValidationError, match="verbosity must be between 1 and 10"):
            PersonaConfig(
                version_codename="Test",
                cls="Mage",
                spec="Teacher",
                mode="Play",
                verbosity=11,  # Invalid: max is 10
                humor=4,
                assertiveness=6,
                creativity=5,
                formality=5,
                empathy=5,
                technical_level=5,
                patience=5,
            )
    def test_humor_at_zero_is_valid(self):
        cfg = PersonaConfig(
            version_codename="Test",
            cls="Mage",
            spec="Teacher",
            mode="Play",
            verbosity=5,
            humor=0,  # Valid: min is 0
            assertiveness=5,
            creativity=5,
            formality=5,
            empathy=5,
            technical_level=5,
            patience=5)
        assert cfg.humor == 0

    def test_creativity_above_maximum_raises(self):
        with pytest.raises(PersonaValidationError, match="creativity must be between 0 and 10"):
            PersonaConfig(
                version_codename="Test",
                cls="Mage",
                spec="Teacher",
                mode="Play",
                verbosity=5,
                humor=4,
                assertiveness=6,
                creativity=15,  # Invalid
                formality=5,
                empathy=5,
                technical_level=5,
                patience=5)
    def test_empty_version_codename_raises(self):
        with pytest.raises(PersonaValidationError, match="version_codename cannot be empty"):
            PersonaConfig(
                version_codename="",
                cls="Mage",
                spec="Teacher",
                mode="Play",
                verbosity=5,
                humor=4,
                assertiveness=6,
                creativity=5,
                formality=5,
                empathy=5,
                technical_level=5,
                patience=5)
    def test_whitespace_only_version_codename_raises(self):
        with pytest.raises(PersonaValidationError, match="version_codename cannot be empty"):
            PersonaConfig(
                version_codename="   ",
                cls="Mage",
                spec="Teacher",
                mode="Play",
                verbosity=5,
                humor=4,
                assertiveness=6,
                creativity=5,

            formality=5,
            empathy=5,
            technical_level=5,
            patience=5)
class TestBuildSystemPrompt:
    """Tests for build_system_prompt function."""

    def test_build_system_prompt_contains_badge(self):
        cfg = PersonaConfig(
            version_codename="ChatGPT 26.2: Redwood",
            cls="Mage",
            spec="Teacher",
            mode="Play",
            verbosity=6,
            humor=4,
            assertiveness=6,
            creativity=5,

            formality=5,
            empathy=5,
            technical_level=5,
            patience=5)
        s = build_system_prompt(cfg)
        assert "Persona Badge:" in s
        assert "Class=Mage" in s
        assert "Spec=Teacher" in s

    def test_build_system_prompt_with_name(self):
        cfg = PersonaConfig(
            version_codename="ChatGPT 26.2: Redwood",
            cls="Mage",
            spec="Teacher",
            mode="Play",
            verbosity=6,
            humor=4,
            assertiveness=6,
            creativity=5,
            formality=5,
            empathy=5,
            technical_level=5,
            patience=5,
            name="Archmage Lyra",
        )
        s = build_system_prompt(cfg)
        assert "Your name is Archmage Lyra" in s
        assert "\"Archmage Lyra\"" in s

    def test_build_system_prompt_without_name(self):
        cfg = PersonaConfig(
            version_codename="ChatGPT 26.2: Redwood",
            cls="Mage",
            spec="Teacher",
            mode="Play",
            verbosity=6,
            humor=4,
            assertiveness=6,
            creativity=5,
            formality=5,
            empathy=5,
            technical_level=5,
            patience=5,
            name="",
        )
        s = build_system_prompt(cfg)
        assert "Your name is" not in s

    def test_build_system_prompt_contains_sliders(self):
        cfg = PersonaConfig(
            version_codename="Test",
            cls="Paladin",
            spec="Accuracy",
            mode="Work",
            verbosity=8,
            humor=2,
            assertiveness=7,
            creativity=3,

            formality=5,
            empathy=5,
            technical_level=5,
            patience=5)
        s = build_system_prompt(cfg)
        assert "Verbosity: 8/10" in s
        assert "Humor: 2/10" in s
        assert "Assertiveness: 7/10" in s
        assert "Creativity: 3/10" in s

    def test_work_mode_rules_included(self):
        cfg = PersonaConfig(
            version_codename="Test",
            cls="Rogue",
            spec="Speed",
            mode="Work",
            verbosity=5,
            humor=2,
            assertiveness=6,
            creativity=3,

            formality=5,
            empathy=5,
            technical_level=5,
            patience=5)
        s = build_system_prompt(cfg)
        assert "Work Mode: prioritize clarity and correctness" in s

    def test_play_mode_rules_included(self):
        cfg = PersonaConfig(
            version_codename="Test",
            cls="Bard",
            spec="Builder",
            mode="Play",
            verbosity=5,
            humor=6,
            assertiveness=6,
            creativity=7,

            formality=5,
            empathy=5,
            technical_level=5,
            patience=5)
        s = build_system_prompt(cfg)
        assert "Play Mode: allow stronger flavor" in s

    def test_unknown_class_raises(self):
        cfg = PersonaConfig(
            version_codename="X",
            cls="Necromancer",
            spec="Teacher",
            mode="Play",
            verbosity=6,
            humor=4,
            assertiveness=6,
            creativity=5,

            formality=5,
            empathy=5,
            technical_level=5,
            patience=5)
        with pytest.raises(ValueError, match="Unknown class"):
            build_system_prompt(cfg)
    def test_unknown_spec_raises(self):
        cfg = PersonaConfig(
            version_codename="X",
            cls="Mage",
            spec="Healer",
            mode="Play",
            verbosity=6,
            humor=4,
            assertiveness=6,
            creativity=5,

            formality=5,
            empathy=5,
            technical_level=5,
            patience=5)
        with pytest.raises(ValueError, match="Unknown spec"):
            build_system_prompt(cfg)
    def test_invalid_mode_raises(self):
        cfg = PersonaConfig(
            version_codename="X",
            cls="Mage",
            spec="Teacher",
            mode="Chaos",  # Invalid
            verbosity=6,
            humor=4,
            assertiveness=6,
            creativity=5,
            formality=5,
            empathy=5,
            technical_level=5,
            patience=5,
        )
        with pytest.raises(ValueError, match="mode must be"):
            build_system_prompt(cfg)
    def test_class_flavor_included(self):
        cfg = PersonaConfig(
            version_codename="Test",
            cls="Warlock",
            spec="Critic",
            mode="Work",
            verbosity=5,
            humor=2,
            assertiveness=8,
            creativity=3,

            formality=5,
            empathy=5,
            technical_level=5,
            patience=5)
        s = build_system_prompt(cfg)
        assert "Analytical and thorough" in s  # Warlock flavor

    def test_spec_behavior_included(self):
        cfg = PersonaConfig(
            version_codename="Test",
            cls="Hunter",
            spec="Debugger",
            mode="Work",
            verbosity=5,
            humor=1,
            assertiveness=6,
            creativity=2,

            formality=5,
            empathy=5,
            technical_level=5,
            patience=5)
        s = build_system_prompt(cfg)
        assert "Systematic troubleshooter" in s  # Debugger behavior

    def test_safety_rails_included(self):
        cfg = PersonaConfig(
            version_codename="Test",
            cls="Mage",
            spec="Teacher",
            mode="Play",
            verbosity=5,
            humor=4,
            assertiveness=6,
            creativity=5,

            formality=5,
            empathy=5,
            technical_level=5,
            patience=5)
        s = build_system_prompt(cfg)
        assert "Do not claim sentience" in s
        assert "financial/legal/medical advice" in s


class TestPersonaSaveLoad:
    """Tests for persona save/load functionality."""

    def test_to_dict_converts_config_to_dict(self):
        cfg = PersonaConfig(
            version_codename="Test Version",
            cls="Mage",
            spec="Teacher",
            mode="Play",
            verbosity=6,
            humor=4,
            assertiveness=6,
            creativity=5,
            formality=5,
            empathy=5,
            technical_level=5,
            patience=5,
            name="Test Persona",
            avatar="🧙‍♂️",
        )
        data = cfg.to_dict()
        assert data["version_codename"] == "Test Version"
        assert data["cls"] == "Mage"
        assert data["avatar"] == "🧙‍♂️"

    def test_from_dict_creates_config_from_dict(self):
        data = {
            "version_codename": "Test Version",
            "cls": "Mage",
            "spec": "Teacher",
            "mode": "Play",
            "verbosity": 6,
            "humor": 4,
            "assertiveness": 6,
            "creativity": 5,
            "formality": 5,
            "empathy": 5,
            "technical_level": 5,
            "patience": 5,
            "name": "Test Persona",
            "avatar": "🧙‍♂️",
        }
        cfg = PersonaConfig.from_dict(data)
        assert cfg.version_codename == "Test Version"
        assert cfg.cls == "Mage"
        assert cfg.avatar == "🧙‍♂️"

    def test_save_and_load_roundtrip(self, tmp_path):
        cfg = PersonaConfig(
            version_codename="Test Version",
            cls="Mage",
            spec="Teacher",
            mode="Play",
            verbosity=6,
            humor=4,
            assertiveness=6,
            creativity=5,
            formality=5,
            empathy=5,
            technical_level=5,
            patience=5,
            name="Test Persona",
            avatar="🧙‍♂️",
        )
        filepath = tmp_path / "test_persona.json"
        cfg.save_to_file(str(filepath))
        loaded_cfg = PersonaConfig.load_from_file(str(filepath))
        assert loaded_cfg.version_codename == cfg.version_codename
        assert loaded_cfg.cls == cfg.cls
        assert loaded_cfg.avatar == cfg.avatar
        assert loaded_cfg.name == cfg.name

    def test_load_from_nonexistent_file_raises_error(self):
        with pytest.raises(PersonaValidationError, match="Persona file not found"):
            PersonaConfig.load_from_file("nonexistent_file.json")
    def test_load_from_invalid_json_raises_error(self, tmp_path):
        filepath = tmp_path / "invalid.json"
        filepath.write_text("invalid json content")
        with pytest.raises(PersonaValidationError, match="Invalid persona file format"):
            PersonaConfig.load_from_file(str(filepath))