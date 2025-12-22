
from typing import Any, TypedDict

import pytest
from pydantic import ValidationError

from docsible.renderers.models.render_context import RenderContext


class RenderContextDict(TypedDict):
    role_info: dict[str, Any]
    template_type: str
    no_vars: bool
class TestRenderContextCreation:
    """Test RenderContext instantiation and validation."""

    def test_minimal_creation(self):
        """Test creating RenderContext with only required fields."""
        context = RenderContext(role_info={'name': 'test_role'})
        
        assert context.role_info == {'name': 'test_role'}
        assert context.template_type == "standard"
        assert context.append is False
        assert context.no_vars is False

    def test_full_creation(self):
        """Test creating RenderContext with all fields."""
        context = RenderContext(
            role_info={'name': 'test_role', 'description': 'A test'},
            template_type='hybrid',
            custom_template_path='/path/to/template.j2',
            mermaid_code_per_file={'main.yml': 'graph TD'},
            sequence_diagram_high_level='sequenceDiagram',
            sequence_diagram_detailed='detailed seq',
            state_diagram='stateDiagram',
            integration_boundary_diagram='boundary',
            architecture_diagram='arch',
            dependency_matrix='matrix',
            dependency_summary={'count': 5},
            show_dependency_matrix=True,
            complexity_report={'score': 10},
            include_complexity=True,
            no_vars=True,
            no_tasks=False,
            no_diagrams=False,
            simplify_diagrams=True,
            no_examples=False,
            no_metadata=False,
            no_handlers=True,
            append=True,
        )
        
        assert context.role_info == {'name': 'test_role', 'description': 'A test'}
        assert context.template_type == 'hybrid'
        assert context.custom_template_path == '/path/to/template.j2'
        assert context.no_vars is True
        assert context.append is True

    def test_validation_requires_role_info(self):
        """Test that role_info is required."""
        with pytest.raises(ValidationError) as exc_info:
            RenderContext() # type: ignore[call-arg]
        
        assert 'role_info' in str(exc_info.value)

    def test_defaults_are_correct(self):
        """Test that default values are set correctly."""
        context = RenderContext(role_info={})
        
        assert context.template_type == "standard"
        assert context.custom_template_path is None
        assert context.mermaid_code_per_file is None
        assert context.show_dependency_matrix is False
        assert context.no_vars is False
        assert context.no_tasks is False
        assert context.no_diagrams is False
        assert context.simplify_diagrams is False
        assert context.no_examples is False
        assert context.no_metadata is False
        assert context.no_handlers is False
        assert context.append is False


class TestToTemplateDict:
    """Test to_template_dict method."""

    def test_to_template_dict_minimal(self):
        """Test converting minimal context to template dict."""
        context = RenderContext(role_info={'name': 'test'})
        result = context.to_template_dict()
        
        assert result['role'] == {'name': 'test'}
        assert result['mermaid_code_per_file'] == {}
        assert result['no_vars'] is False
        assert result['no_tasks'] is False

    def test_to_template_dict_with_diagrams(self):
        """Test converting context with diagrams to template dict."""
        context = RenderContext(
            role_info={'name': 'test'},
            mermaid_code_per_file={'main.yml': 'graph'},
            sequence_diagram_high_level='seq',
            state_diagram='state'
        )
        result = context.to_template_dict()
        
        assert result['mermaid_code_per_file'] == {'main.yml': 'graph'}
        assert result['sequence_diagram_high_level'] == 'seq'
        assert result['state_diagram'] == 'state'

    def test_to_template_dict_with_flags(self):
        """Test converting context with content flags to template dict."""
        context = RenderContext(
            role_info={},
            no_vars=True,
            no_tasks=True,
            no_diagrams=True
        )
        result = context.to_template_dict()
        
        assert result['no_vars'] is True
        assert result['no_tasks'] is True
        assert result['no_diagrams'] is True

    def test_to_template_dict_mermaid_code_default(self):
        """Test that mermaid_code_per_file defaults to empty dict in template."""
        context = RenderContext(role_info={})
        result = context.to_template_dict()
        
        # Should be empty dict, not None
        assert result['mermaid_code_per_file'] == {}


class TestPydanticFeatures:
    """Test Pydantic-specific features."""

    def test_model_serialization(self):
        """Test that RenderContext can be serialized to dict."""
        context = RenderContext(
            role_info={'name': 'test'},
            template_type='hybrid',
            no_vars=True
        )
        
        data = context.model_dump()
        
        assert data['role_info'] == {'name': 'test'}
        assert data['template_type'] == 'hybrid'
        assert data['no_vars'] is True

    def test_model_json_serialization(self):
        """Test that RenderContext can be serialized to JSON."""
        context = RenderContext(
            role_info={'name': 'test'},
            template_type='hybrid'
        )
        
        json_str = context.model_dump_json()
        
        assert '"role_info"' in json_str
        assert '"template_type"' in json_str
        assert '"hybrid"' in json_str

    def test_model_from_dict(self):
        """Test creating RenderContext from dictionary."""

        data: RenderContextDict = {
            'role_info': {'name': 'test'},
            'template_type': 'hybrid',
            'no_vars': True
        }
        
        context = RenderContext(**data) 
        
        assert context.role_info == {'name': 'test'}
        assert context.template_type == 'hybrid'
        assert context.no_vars is True

    def test_validation_on_assignment(self):
        """Test that Pydantic validates on attribute assignment."""
        context = RenderContext(role_info={})
        
        # This should work
        context.template_type = 'hybrid'
        assert context.template_type == 'hybrid'
        
        # Values are validated
        context.no_vars = True
        assert context.no_vars is True


class TestRenderContextUseCases:
    """Test real-world usage scenarios."""

    def test_simple_role_rendering(self):
        """Test context for simple role rendering."""
        context = RenderContext(
            role_info={'name': 'simple_role', 'description': 'A simple role'},
            template_type='standard'
        )
        
        template_vars = context.to_template_dict()
        
        assert template_vars['role']['name'] == 'simple_role'
        assert template_vars['no_vars'] is False
        assert template_vars['no_tasks'] is False

    def test_complex_role_with_diagrams(self):
        """Test context for complex role with all diagrams."""
        context = RenderContext(
            role_info={'name': 'complex_role'},
            template_type='hybrid',
            mermaid_code_per_file={
                'main.yml': 'graph TD\nA-->B',
                'install.yml': 'graph LR\nX-->Y'
            },
            sequence_diagram_high_level='sequenceDiagram\nA->>B',
            architecture_diagram='graph TB\nRole-->Task',
            no_vars=False,
            no_diagrams=False
        )
        
        template_vars = context.to_template_dict()
        
        assert len(template_vars['mermaid_code_per_file']) == 2
        assert template_vars['sequence_diagram_high_level'] is not None
        assert template_vars['no_diagrams'] is False

    def test_minimal_output_role(self):
        """Test context for minimal output (no extras)."""
        context = RenderContext(
            role_info={'name': 'minimal_role'},
            no_vars=True,
            no_tasks=True,
            no_diagrams=True,
            no_examples=True,
            no_metadata=True,
            no_handlers=True
        )
        
        template_vars = context.to_template_dict()
        
        assert all([
            template_vars['no_vars'],
            template_vars['no_tasks'],
            template_vars['no_diagrams'],
            template_vars['no_examples'],
            template_vars['no_metadata'],
            template_vars['no_handlers']
        ])

    def test_append_mode(self):
        """Test context for append mode rendering."""
        context = RenderContext(
            role_info={'name': 'test'},
            append=True
        )
        
        assert context.append is True
        template_vars = context.to_template_dict()
        # append is not in template vars, it's used by renderer
        assert 'append' not in template_vars
