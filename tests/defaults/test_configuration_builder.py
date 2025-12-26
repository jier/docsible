import logging

from docsible.defaults.builder import ConfigurationBuilder
from docsible.defaults.decisions.base import Decision


class TestConfigurationBuilder:
    """Test configuration building from decisions."""

    def test_empty_builder_creates_default_config(self):
        """Test that empty builder creates valid config with defaults."""
        builder = ConfigurationBuilder()
        config = builder.build()

        # Should have default values
        assert config is not None
        assert config.confidence == 1.0  # Full confidence in defaults
        assert len(config.decisions) == 0

    def test_add_single_decision(self):
        """Test adding a single decision."""
        builder = ConfigurationBuilder()
        decision = Decision(
            option_name="generate_graph",
            value=True,
            rationale="Complex role needs visualization",
            confidence=0.8,
            rule_name="GraphDecisionRule",
        )

        config = builder.add_decision(decision).build()

        assert config.generate_graph is True
        assert len(config.decisions) == 1
        assert config.decisions[0] == decision
        assert config.confidence == 0.8

    def test_add_multiple_decisions(self):
        """Test adding multiple decisions."""
        decisions = [
            Decision(
                option_name="generate_graph",
                value=True,
                rationale="Test",
                confidence=0.8,
                rule_name="GraphDecisionRule",
            ),
            Decision(
                option_name="minimal",
                value=False,
                rationale="Test",
                confidence=0.7,
                rule_name="MinimalModeRule",
            ),
            Decision(
                option_name="show_dependencies",
                value=True,
                rationale="Test",
                confidence=0.9,
                rule_name="DependenciesDecisionRule",
            ),
        ]

        builder = ConfigurationBuilder()
        config = builder.add_decisions(decisions).build()

        assert config.generate_graph is True
        assert config.minimal is False
        assert config.show_dependencies is True
        assert len(config.decisions) == 3
        # Average confidence: (0.8 + 0.7 + 0.9) / 3 = 0.8
        assert abs(config.confidence - 0.8) < 0.01

    def test_fluent_interface_chaining(self):
        """Test that builder supports method chaining."""
        d1 = Decision(option_name="generate_graph", value=True, rationale="Test", confidence=0.8, rule_name="GraphDecisionRule")
        d2 = Decision(option_name="minimal", value=False, rationale="Test", confidence=0.7, rule_name="MinimalModeRule")

        builder = ConfigurationBuilder()
        config = builder.add_decision(d1).add_decision(d2).build()

        assert len(config.decisions) == 2
        assert config.generate_graph is True
        assert config.minimal is False

    def test_none_decision_is_ignored(self):
        """Test that None decisions are safely ignored."""
        builder = ConfigurationBuilder()
        config = builder.add_decision(None).build()

        assert len(config.decisions) == 0

    def test_confidence_calculation_with_varying_values(self):
        """Test confidence calculation with different decision confidences."""
        decisions = [
            Decision(option_name="opt1", value=True, rationale="Test", confidence=1.0, rule_name="Rule1"),
            Decision(option_name="opt2", value=False, rationale="Test", confidence=0.5, rule_name="Rule2"),
            Decision(option_name="opt3", value=True, rationale="Test", confidence=0.7, rule_name="Rule3"),
        ]

        builder = ConfigurationBuilder()
        config = builder.add_decisions(decisions).build()

        # Average: (1.0 + 0.5 + 0.7) / 3 = 0.733...
        expected_confidence = (1.0 + 0.5 + 0.7) / 3
        assert abs(config.confidence - expected_confidence) < 0.01

    def test_decision_conflict_logged(self, caplog):
        """Test that conflicting decisions are logged as warnings."""
        d1 = Decision(option_name="generate_graph", value=True, rationale="First decision", confidence=0.8, rule_name="Rule1")
        d2 = Decision(option_name="generate_graph", value=False, rationale="Second decision", confidence=0.9, rule_name="Rule2")

        builder = ConfigurationBuilder()

        with caplog.at_level(logging.WARNING):
            config = builder.add_decision(d1).add_decision(d2).build()

        # Second decision should win
        assert config.generate_graph is False
        # Should have logged warning about conflict
        assert "Decision conflict" in caplog.text
        assert "generate_graph" in caplog.text

    def test_validate_contradictory_minimal_and_complexity_report(self, caplog):
        """Test validation catches minimal=True + complexity_report=True."""
        decisions = [
            Decision(option_name="minimal", value=True, rationale="Simple role", confidence=0.7, rule_name="MinimalModeRule"),
            Decision(option_name="complexity_report", value=True, rationale="Show report", confidence=0.8, rule_name="ComplexityRule"),
        ]

        builder = ConfigurationBuilder()

        with caplog.at_level(logging.WARNING):
            config = builder.add_decisions(decisions).build()

        # Should warn and disable complexity_report
        assert "Contradictory config" in caplog.text
        assert config.minimal is True
        assert config.complexity_report is False

    def test_validate_contradictory_no_diagrams_and_generate_graph(self, caplog):
        """Test validation catches no_diagrams=True + generate_graph=True."""
        decisions = [
            Decision(option_name="no_diagrams", value=True, rationale="No diagrams", confidence=0.9, rule_name="DiagramRule"),
            Decision(option_name="generate_graph", value=True, rationale="Generate graphs", confidence=0.8, rule_name="GraphRule"),
        ]

        builder = ConfigurationBuilder()

        with caplog.at_level(logging.WARNING):
            config = builder.add_decisions(decisions).build()

        # Should warn and respect no_diagrams
        assert "Contradictory config" in caplog.text
        assert config.no_diagrams is True
        assert config.generate_graph is False

    def test_add_decisions_with_empty_list(self):
        """Test that empty decision list is handled gracefully."""
        builder = ConfigurationBuilder()
        config = builder.add_decisions([]).build()

        assert len(config.decisions) == 0
        assert config.confidence == 1.0

    def test_builder_can_be_reused(self):
        """Test that builder can be used multiple times."""
        d1 = Decision(option_name="generate_graph", value=True, rationale="Test", confidence=0.8, rule_name="Rule1")
        d2 = Decision(option_name="minimal", value=False, rationale="Test", confidence=0.7, rule_name="Rule2")

        builder = ConfigurationBuilder()

        # First build
        config1 = builder.add_decision(d1).build()
        assert len(config1.decisions) == 1

        # Reset and second build (new instance needed)
        builder2 = ConfigurationBuilder()
        config2 = builder2.add_decision(d2).build()
        assert len(config2.decisions) == 1
        assert config2.decisions[0].option_name == "minimal"

    def test_all_boolean_options_default_to_false(self):
        """Test that all boolean options default to False."""
        builder = ConfigurationBuilder()
        config = builder.build()

        # All defaults should be False
        assert config.generate_graph is False
        assert config.minimal is False
        assert config.show_dependencies is False
        assert config.complexity_report is False
        assert config.no_diagrams is False

    def test_complex_scenario_multiple_rules(self):
        """Test realistic scenario with multiple decision rules."""
        decisions = [
            Decision(
                option_name="generate_graph",
                value=True,
                rationale="Role has 15 tasks and 3 files - complexity warrants visualization",
                confidence=0.8,
                rule_name="GraphDecisionRule",
            ),
            Decision(
                option_name="minimal",
                value=False,
                rationale="Role complexity justifies full documentation",
                confidence=0.6,
                rule_name="MinimalModeRule",
            ),
            Decision(
                option_name="show_dependencies",
                value=False,
                rationale="No role dependencies detected in meta",
                confidence=0.7,
                rule_name="DependenciesDecisionRule",
            ),
        ]

        builder = ConfigurationBuilder()
        config = builder.add_decisions(decisions).build()

        # Verify all decisions applied correctly
        assert config.generate_graph is True
        assert config.minimal is False
        assert config.show_dependencies is False

        # Verify confidence calculation
        expected_confidence = (0.8 + 0.6 + 0.7) / 3
        assert abs(config.confidence - expected_confidence) < 0.01

        # Verify all decisions recorded
        assert len(config.decisions) == 3
        rule_names = {d.rule_name for d in config.decisions}
        assert "GraphDecisionRule" in rule_names
        assert "MinimalModeRule" in rule_names
        assert "DependenciesDecisionRule" in rule_names

    def test_config_to_cli_args(self):
        """Test that config can generate CLI args."""
        decisions = [
            Decision(option_name="generate_graph", value=True, rationale="Test", confidence=0.8, rule_name="GraphRule"),
            Decision(option_name="show_dependencies", value=True, rationale="Test", confidence=0.7, rule_name="DepsRule"),
        ]

        builder = ConfigurationBuilder()
        config = builder.add_decisions(decisions).build()

        args = config.to_cli_args()

        assert isinstance(args, list)
        assert "--graph" in args
        assert "--show-dependencies" in args
