"""
Chart Capture Hook for Financial Advisory Agent.

Captures chart data from the visualization tool and attaches it to conversation messages.
"""

from typing import Any, Dict, Optional
from strands.hooks import HookProvider, HookRegistry
from strands.hooks.events import AfterInvocationEvent
from tools.visualization_tool import get_last_chart_data, clear_chart_data


class ChartCaptureHook(HookProvider):
    """Hook to capture and store chart data from visualization tool."""
    
    def __init__(self):
        """Initialize the chart capture hook."""
        self.captured_chart_data: Optional[Dict[str, Any]] = None
        print("[ChartCaptureHook] Hook initialized")
    
    def register_hooks(self, registry: HookRegistry) -> None:
        """Register the hook callback for AfterInvocationEvent."""
        registry.add_callback(AfterInvocationEvent, self.capture_chart_data)
    
    def capture_chart_data(self, event: AfterInvocationEvent) -> None:
        """
        Capture chart data after tool calls.
        
        Args:
            event: The AfterInvocationEvent containing tool execution details
        """
        try:
            # After ANY tool call, check if there's chart data available
            # This is simpler and more reliable than trying to detect the tool name from the event
            chart_data = get_last_chart_data()
            
            if chart_data and isinstance(chart_data, dict):
                # Only capture if we haven't already captured this chart
                if self.captured_chart_data != chart_data:
                    self.captured_chart_data = chart_data
                    print(f"\n[ChartCaptureHook] ✅ Captured chart data!")
                    print(f"  - Chart type: {chart_data.get('chart_type', 'unknown')}")
                    print(f"  - Title: {chart_data.get('title', 'N/A')}")
                    print(f"  - Status: {chart_data.get('status', 'N/A')}")
        
        except Exception as e:
            print(f"[ChartCaptureHook] Error capturing chart data: {e}")
            import traceback
            traceback.print_exc()
    
    def get_captured_chart_data(self) -> Optional[Dict[str, Any]]:
        """
        Get the captured chart data.
        
        Returns:
            Dictionary containing chart configuration and data, or None
        """
        return self.captured_chart_data
    
    def clear_captured_chart_data(self) -> None:
        """Clear the captured chart data."""
        self.captured_chart_data = None
        clear_chart_data()
        print("[ChartCaptureHook] Cleared captured chart data")

