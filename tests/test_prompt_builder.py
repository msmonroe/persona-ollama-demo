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
        )
        assert cfg.cls == "Mage"
        assert cfg.verbosity == 6

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
        )
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
            )

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
            )

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
            )


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
        )
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
        )
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
        )
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
        )
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
        )
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
        )
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
        )
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
        )
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
        )
        s = build_system_prompt(cfg)
        assert "Do not claim sentience" in s
        assert "financial/legal/medical advice" in s
