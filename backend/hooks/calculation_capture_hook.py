"""
Hook to capture calculation details from tool results.
This allows the frontend to display calculation steps in a collapsible panel.
"""

from typing import Any, Dict, Optional
from strands.hooks import HookProvider, HookRegistry
from strands.hooks.events import AfterInvocationEvent
import json

class CalculationCaptureHook(HookProvider):
    """Hook that captures calculation_steps and latex_formulas from tool results."""
    
    def __init__(self):
        self.last_calculation_details: Optional[Dict[str, Any]] = None
    
    def register_hooks(self, registry: HookRegistry) -> None:
        """Register the hook callback for AfterInvocationEvent."""
        registry.add_callback(AfterInvocationEvent, self.capture_calculation_details)
    
    def capture_calculation_details(self, event: AfterInvocationEvent) -> None:
        """
        Capture calculation details after tool calls.
        Looks for calculation_steps, latex_formulas, and scenario_type in tool results.
        """
        try:
            # Debug: Print event attributes
            print(f"\n[CalculationCaptureHook] Event received")
            print(f"  - Event type: {type(event)}")
            print(f"  - Event dir: {[attr for attr in dir(event) if not attr.startswith('_')]}")
            
            # Try multiple ways to extract tool name
            tool_name = None
            for attr in ['tool_name', 'function_name', 'name', 'tool']:
                if hasattr(event, attr):
                    tool_name = getattr(event, attr)
                    print(f"  - Found tool_name via '{attr}': {tool_name}")
                    break
            
            # Try multiple ways to extract result
            tool_result = None
            for attr in ['result', 'output', 'response', 'return_value']:
                if hasattr(event, attr):
                    tool_result = getattr(event, attr)
                    print(f"  - Found result via '{attr}': {type(tool_result)}")
                    break
            
            # Only capture from calculation tools
            if tool_name in ['debt_optimizer', 'student_loan_payment_calculator', 'student_loan_refinancing_calculator']:
                print(f"  - Calculation tool detected: {tool_name}")
                
                # Tool result might be in different formats - try to extract
                result_data = None
                
                if isinstance(tool_result, dict):
                    # Direct dict result
                    print(f"  - Result is dict with keys: {list(tool_result.keys())}")
                    result_data = tool_result
                elif isinstance(tool_result, str):
                    # String result - try to parse JSON
                    print(f"  - Result is string, attempting JSON parse")
                    try:
                        result_data = json.loads(tool_result)
                    except (json.JSONDecodeError, TypeError):
                        print(f"  - JSON parse failed")
                        result_data = None
                elif hasattr(tool_result, 'content'):
                    # Strands result object
                    print(f"  - Result has 'content' attribute")
                    content = tool_result.content
                    if isinstance(content, list) and len(content) > 0:
                        # Try to parse JSON if it's a string
                        text_content = content[0].get('text', '') if isinstance(content[0], dict) else str(content[0])
                        try:
                            result_data = json.loads(text_content)
                        except (json.JSONDecodeError, TypeError):
                            result_data = None
                
                # Check if we have calculation details
                if result_data and isinstance(result_data, dict):
                    print(f"  - Checking for calculation_steps: {'calculation_steps' in result_data}")
                    print(f"  - Checking for latex_formulas: {'latex_formulas' in result_data}")
                    
                    if 'calculation_steps' in result_data or 'latex_formulas' in result_data:
                        self.last_calculation_details = {
                            'scenario_type': result_data.get('scenario_type', 'unknown'),
                            'calculation_steps': result_data.get('calculation_steps', []),
                            'latex_formulas': result_data.get('latex_formulas', []),
                            'tool_name': tool_name
                        }
                        print(f"\n✅ [CalculationCaptureHook] SUCCESSFULLY Captured calculation details from {tool_name}")
                        print(f"  - Scenario: {self.last_calculation_details['scenario_type']}")
                        print(f"  - Steps: {len(self.last_calculation_details['calculation_steps'])}")
                        print(f"  - Formulas: {len(self.last_calculation_details['latex_formulas'])}")
                    else:
                        print(f"  - ❌ No calculation_steps or latex_formulas found in result")
                else:
                    print(f"  - ❌ result_data is not a dict or is None")
            else:
                print(f"  - Not a calculation tool (tool_name: {tool_name})")
        
        except Exception as e:
            import traceback
            print(f"[CalculationCaptureHook] Error capturing calculation details: {e}")
            print(f"Traceback: {traceback.format_exc()}")
    
    def get_last_calculation_details(self) -> Optional[Dict[str, Any]]:
        """Retrieve the last captured calculation details."""
        return self.last_calculation_details
    
    def clear(self):
        """Clear the captured calculation details."""
        self.last_calculation_details = None

