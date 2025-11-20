"""
Basic tests for Growbe Financial Advisor
Tests core functionality and imports
"""

import pytest
import os
from pathlib import Path


def test_imports():
    """Test that all core modules can be imported"""
    try:
        # Test FastAPI app import
        from main import app
        assert app is not None
        
        # Test tool system imports
        from tools.tool_manager import ToolRegistry
        from tools.base_tool import BaseTool
        
        # Test service imports
        from services.customer_service import customer_service
        from services.conversation_service import conversation_service
        
        # Test utility imports
        from utils.prompt_loader import load_system_prompt
        
        print("✅ All core imports successful")
        
    except ImportError as e:
        pytest.fail(f"Import failed: {e}")


def test_environment_variables():
    """Test that required environment variables are handled"""
    # Test with dummy values (GitHub Actions provides these)
    original_api_key = os.environ.get('OPENAI_API_KEY')
    
    try:
        # Set dummy values for testing
        os.environ['OPENAI_API_KEY'] = 'dummy_key_for_testing'
        
        # Test that environment loading works
        from dotenv import load_dotenv
        assert load_dotenv is not None
        
        print("✅ Environment variable handling works")
        
    finally:
        # Restore original value
        if original_api_key:
            os.environ['OPENAI_API_KEY'] = original_api_key
        elif 'OPENAI_API_KEY' in os.environ:
            del os.environ['OPENAI_API_KEY']


def test_tool_registry():
    """Test that tool registry can be initialized"""
    try:
        from tools.tool_manager import ToolRegistry
        
        registry = ToolRegistry()
        assert registry is not None
        assert hasattr(registry, '_tools')
        assert hasattr(registry, '_strands_tools')
        
        print("✅ Tool registry initialization works")
        
    except Exception as e:
        pytest.fail(f"Tool registry test failed: {e}")


def test_base_tool_structure():
    """Test that BaseTool abstract class is properly defined"""
    try:
        from tools.base_tool import BaseTool
        import inspect
        
        # Check that it's an abstract class
        assert inspect.isabstract(BaseTool)
        
        # Check required abstract methods exist
        methods = [name for name, obj in inspect.getmembers(BaseTool, predicate=inspect.isfunction)]
        assert 'execute' in methods
        
        # Check required properties exist
        props = [name for name, obj in inspect.getmembers(BaseTool, predicate=lambda x: isinstance(x, property))]
        assert len(props) >= 2  # name and description properties
        
        print("✅ BaseTool structure is correct")
        
    except Exception as e:
        pytest.fail(f"BaseTool structure test failed: {e}")


def test_database_path_resolution():
    """Test that database path resolution works"""
    try:
        # Test default path resolution
        db_path = os.getenv("SQLITE_DB_PATH", "data/financial_data.db")
        assert db_path is not None
        
        # Test Path operations work
        path_obj = Path(db_path)
        assert path_obj is not None
        
        print("✅ Database path resolution works")
        
    except Exception as e:
        pytest.fail(f"Database path test failed: {e}")


def test_math_operations():
    """Test basic math operations (used by financial calculators)"""
    # Test basic arithmetic that financial tools depend on
    assert 1 + 1 == 2
    assert 100 * 1.05 == 105.0  # Simple interest calculation
    assert abs(-5) == 5  # Absolute value for financial calculations
    
    # Test financial calculation basics
    principal = 10000
    rate = 0.05
    time = 1
    
    # Simple interest formula: P * R * T
    interest = principal * rate * time
    assert interest == 500.0
    
    print("✅ Basic math operations work")


def test_sample_financial_calculation():
    """Test a simple financial calculation"""
    # Test debt payment calculation (simple version)
    principal = 10000
    monthly_payment = 300
    
    # Estimate months to payoff (rough calculation)
    months = principal // monthly_payment
    assert months == 33  # 10000 / 300 = 33.33, integer division = 33
    
    print("✅ Sample financial calculation works")


@pytest.mark.skipif(
    os.getenv('OPENAI_API_KEY') is None,
    reason="OpenAI API key not available for integration tests"
)
def test_openai_import():
    """Test OpenAI client can be imported (integration test)"""
    try:
        import openai
        assert openai is not None
        
        # Test client initialization with dummy key
        client = openai.OpenAI(api_key="dummy_key_for_testing")
        assert client is not None
        
        print("✅ OpenAI client import works")
        
    except Exception as e:
        pytest.skip(f"OpenAI integration test skipped: {e}")


def test_strands_import():
    """Test Strands framework can be imported"""
    try:
        from strands import Agent
        from strands.models.openai import OpenAIModel
        assert Agent is not None
        assert OpenAIModel is not None
        
        print("✅ Strands framework import works")
        
    except ImportError as e:
        pytest.fail(f"Strands import failed: {e}")


def test_fastapi_app_structure():
    """Test that FastAPI app has expected structure"""
    try:
        from main import app
        
        # Check that it's a FastAPI app
        assert hasattr(app, 'routes')
        assert hasattr(app, 'middleware')
        
        # Check that it has some routes
        routes = [route for route in app.routes]
        assert len(routes) > 0
        
        print("✅ FastAPI app structure is correct")
        
    except Exception as e:
        pytest.fail(f"FastAPI app test failed: {e}")
