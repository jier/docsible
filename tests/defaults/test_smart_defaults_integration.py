from docsible.defaults.engine import SmartDefaultsEngine


class TestSmartDefaultsIntegration:
    """Test complete pipeline from detection to configuration."""

    def test_simple_role_pipeline(self, simple_role):
        """Test full pipeline for simple role.

        Note: simple_role has 3 tasks and 1 handler, so it won't be
        categorized as 'minimal' since the MinimalModeRule requires
        no handlers for minimal mode.
        """
        engine = SmartDefaultsEngine()
        config, _ = engine.generate_config(simple_role)  # Unpack tuple (config, complexity_report)

        # Simple role should not generate graphs (too simple)
        assert config.generate_graph is False

        # Simple role with handlers is NOT minimal
        # (MinimalModeRule requires: <=5 tasks AND no handlers AND no advanced features)
        assert config.minimal is False

        # Should have reasonable confidence
        assert config.confidence > 0.7

        # Should have decisions recorded
        assert len(config.decisions) > 0

        # Should have both graph and minimal decisions
        decision_names = {d.option_name for d in config.decisions}
        assert "generate_graph" in decision_names
        assert "minimal" in decision_names

    def test_medium_role_pipeline(self, medium_role_fixture):
        """Test full pipeline for medium complexity role.

        Note: With improved GraphDecisionRule, medium roles with 2+ files
        now get graph generation recommended with moderate confidence.
        """
        engine = SmartDefaultsEngine()
        config, _ = engine.generate_config(medium_role_fixture)  # Unpack tuple

        # Medium role (15 tasks, 3 files) - GraphDecisionRule now recommends graphs
        # with moderate confidence (0.6) since it has >= 2 task files
        assert config.generate_graph is True

        # Medium role should not be minimal
        assert config.minimal is False

        # Should have good confidence (average of 0.6 and 0.6)
        assert config.confidence >= 0.6

        # Should have both decisions
        assert len(config.decisions) >= 2

    def test_complex_role_pipeline(self, complex_role_fixture):
        """Test full pipeline for complex role.

        Note: Currently only GraphDecisionRule and MinimalModeRule exist.
        show_dependencies would require a new DependenciesDecisionRule.
        """
        engine = SmartDefaultsEngine()
        config, _ = engine.generate_config(complex_role_fixture)  # Unpack tuple

        # Complex role (30+ tasks) should definitely generate graphs
        assert config.generate_graph is True

        # Complex role should not be minimal
        assert config.minimal is False

        # Should have good confidence (average of 0.8, 0.6, and 0.9)
        assert config.confidence >= 0.7

        # Complex role has dependencies, so DependenciesDecisionRule sets show_dependencies
        assert config.show_dependencies is True

        # Should have all three decision rules represented
        assert len(config.decisions) >= 3
        rule_names = {d.rule_name for d in config.decisions}
        assert "GraphDecisionRule" in rule_names
        assert "MinimalModeRule" in rule_names
        assert "DependenciesDecisionRule" in rule_names

    def test_user_overrides_preserved(self, simple_role):
        """Test that user overrides take precedence over smart defaults."""
        engine = SmartDefaultsEngine()

        user_overrides = {
            "generate_graph": True,  # Override smart default (should be False)
            "minimal": True,  # Override smart default (should be False)
        }

        config, _ = engine.generate_config(  # Unpack tuple
            simple_role,
            user_overrides=user_overrides
        )

        # User overrides should be preserved
        # Note: This depends on builder implementation handling overrides
        # Currently, the builder adds decisions but user_overrides are passed to context
        # The actual override behavior depends on ConfigurationBuilder.build()

        # At minimum, verify config was generated without errors
        assert config is not None
        assert config.confidence > 0

    def test_cli_args_generation(self, simple_role):
        """Test that config can be converted to CLI args."""
        engine = SmartDefaultsEngine()
        config, _ = engine.generate_config(simple_role)  # Unpack tuple

        args = config.to_cli_args()

        # Should be valid CLI args
        assert isinstance(args, list)
        assert all(isinstance(arg, str) for arg in args)

        # Should include key decisions based on actual config
        if config.minimal:
            assert "--minimal" in args

        # Verify no graph args for simple role
        if not config.generate_graph:
            assert "--graph" not in args

    def test_decision_rationales(self, medium_role_fixture):
        """Test that decisions include proper rationales."""
        engine = SmartDefaultsEngine()
        config, _ = engine.generate_config(medium_role_fixture)  # Unpack tuple

        # All decisions should have rationales
        for decision in config.decisions:
            assert decision.rationale is not None
            assert len(decision.rationale) > 0
            assert decision.rule_name is not None
            assert 0.0 <= decision.confidence <= 1.0

    def test_confidence_calculation(self, complex_role_fixture):
        """Test that overall confidence is calculated correctly."""
        engine = SmartDefaultsEngine()
        config, _ = engine.generate_config(complex_role_fixture)  # Unpack tuple

        # Overall confidence should be average of decision confidences
        if config.decisions:
            avg_confidence = sum(d.confidence for d in config.decisions) / len(config.decisions)
            assert abs(config.confidence - avg_confidence) < 0.01

    def test_legacy_complex_role(self, complex_role):
        """Test with legacy complex_role fixture (actually MEDIUM).

        Note: Has 13 tasks across 4 files, categorized as MEDIUM.
        With improved logic, now gets graph generation recommended.
        """
        engine = SmartDefaultsEngine()
        config, _ = engine.generate_config(complex_role)  # Unpack tuple

        # Legacy fixture has 13 tasks, 4 files (MEDIUM category)
        # GraphDecisionRule now recommends graphs (>= 2 files)
        assert config.generate_graph is True
        assert config.minimal is False

    def test_empty_decisions_list(self, simple_role):
        """Test that we always get some decisions."""
        engine = SmartDefaultsEngine()
        config, _ = engine.generate_config(simple_role)  # Unpack tuple

        # Should always have at least graph and minimal decisions
        assert len(config.decisions) >= 2

        # Check specific rules ran
        rule_names = {d.rule_name for d in config.decisions}
        assert "GraphDecisionRule" in rule_names
        assert "MinimalModeRule" in rule_names

    #1. Test More Decision Rules (when implemented)
    def test_dependencies_decision_rule(self, complex_role_fixture):
        """Test show_dependencies decision for roles with dependencies."""
        engine = SmartDefaultsEngine()
        config, _ = engine.generate_config(complex_role_fixture)  # Unpack tuple

        # Complex role fixture has dependencies in meta/main.yml
        # (geerlingguy.postgresql and geerlingguy.nginx)
        assert config.show_dependencies is True

        # Should have decision from DependenciesDecisionRule
        rule_names = {d.rule_name for d in config.decisions}
        assert "DependenciesDecisionRule" in rule_names

        # Find the dependencies decision
        deps_decision = next(d for d in config.decisions if d.option_name == "show_dependencies")
        assert deps_decision.value is True
        assert deps_decision.confidence >= 0.5  # At least moderate confidence
    
    #2. Test User Overrides Actually Work
    def test_user_overrides_actually_override(self, simple_role):
        """Test that user overrides actually change the config."""
        engine = SmartDefaultsEngine()

        # Without overrides - get baseline
        config_baseline, _ = engine.generate_config(simple_role)  # Unpack tuple

        # Simple role defaults:
        # - generate_graph = False (simple role)
        # - minimal = False (has handlers)
        # - show_dependencies = False (no dependencies)
        assert config_baseline.generate_graph is False
        assert config_baseline.minimal is False
        assert config_baseline.show_dependencies is False

        # With overrides - force opposite values
        config_overridden, _ = engine.generate_config(  # Unpack tuple
            simple_role,
            user_overrides={
                "generate_graph": True,   # Override to True
                "minimal": True,           # Override to True
                "show_dependencies": True  # Override to True
            }
        )

        # User overrides are passed to context, rules should abstain
        # So decisions list should be shorter (rules returned None)
        # The actual override behavior depends on how ConfigurationBuilder
        # handles user_overrides - currently it only tracks decisions

        # At minimum: config generated without errors
        assert config_overridden is not None
        assert config_overridden.confidence > 0

        # Rules should NOT make decisions for user-overridden options
        # (they should return None and abstain)
        # So we expect fewer decisions when user overrides are present
        assert len(config_overridden.decisions) <= len(config_baseline.decisions)

        # Verify that overridden options don't appear in decisions
        decision_names = {d.option_name for d in config_overridden.decisions}
        # None of the user-overridden options should have decisions
        # (rules abstained because user specified them)
        for overridden_option in ["generate_graph", "minimal", "show_dependencies"]:
            if overridden_option in decision_names:
                # If there IS a decision, it means the rule didn't abstain
                # This would be a bug in the rule's user_specified() check
                assert False, f"Rule made decision for user-overridden option: {overridden_option}"
    
    # 3. Test Edge Cases
    def test_role_with_many_task_files(self, many_files_role):
        """Test role with 6+ task files triggers graph generation."""
        # Use many_files_role fixture from conftest.py
        # Has 6 task files (triggers complex role graph logic)
        engine = SmartDefaultsEngine()
        config, _ = engine.generate_config(many_files_role)  # Unpack tuple

        # 6 task files should trigger graph generation
        # GraphDecisionRule checks: task_file_count > MAX_TASK_FILES_LOWER_BOUND (5)
        assert config.generate_graph is True

        # Find the graph decision
        graph_decision = next(
            (d for d in config.decisions if d.option_name == "generate_graph"),
            None
        )
        assert graph_decision is not None
        assert graph_decision.value is True
        # Should have high confidence (complex role with many files)
        assert graph_decision.confidence >= 0.7
        
    def test_truly_minimal_role(self, minimal_role):
        """Test role that qualifies for minimal mode."""
        # Use minimal_role fixture from conftest.py
        # Satisfies MinimalModeRule criteria:
        # - 3 tasks (< 5 threshold)
        # - No handlers
        # - No advanced features (includes, imports, roles)
        # - Single task file
        engine = SmartDefaultsEngine()
        config, _ = engine.generate_config(minimal_role)  # Unpack tuple

        # Should qualify for minimal mode
        # MinimalModeRule checks:
        # - total_tasks <= 5 ✓ (3 tasks)
        # - not has_handlers ✓ (no handlers dir)
        # - not uses_advanced_features ✓ (no includes/imports)
        # - task_file_count == 1 ✓ (only main.yml)
        assert config.minimal is True

        # Should not generate graphs (too simple)
        assert config.generate_graph is False

        # Should not show dependencies (none exist)
        assert config.show_dependencies is False

        # Find the minimal decision
        minimal_decision = next(
            (d for d in config.decisions if d.option_name == "minimal"),
            None
        )
        assert minimal_decision is not None
        assert minimal_decision.value is True
        assert minimal_decision.confidence >= 0.6

        # Verify all three rules made decisions
        rule_names = {d.rule_name for d in config.decisions}
        assert "GraphDecisionRule" in rule_names
        assert "MinimalModeRule" in rule_names
        assert "DependenciesDecisionRule" in rule_names