"""
SQL Result Capture Hook for Strands Agents

This hook captures SQL queries and results from NL2SQL tool executions
and makes them available for enhanced UI display with intelligent chart generation.
"""
from typing import Any, Dict, List, Optional
from strands.hooks import HookProvider, HookRegistry
from strands.hooks.events import AfterInvocationEvent
import json
import ast
import logging
import re

logger = logging.getLogger(__name__)


class SQLResultCaptureHook(HookProvider):
    """
    Hook to capture SQL query details from NL2SQL tool executions.
    
    This hook listens for AfterInvocationEvent and captures SQL queries
    and results when the nl2sql_query tool is used, making them available
    for enhanced UI display.
    """
    
    def __init__(self):
        self.captured_sql_details: Optional[Dict[str, Any]] = None
        self.is_streaming = False
        self.user_question: Optional[str] = None  # Store the original user question for context
        
    def register_hooks(self, registry: HookRegistry) -> None:
        """Register the hook callback for AfterInvocationEvent."""
        registry.add_callback(AfterInvocationEvent, self.capture_sql_results)
    
    def capture_sql_results(self, event: AfterInvocationEvent) -> None:
        """
        Capture SQL query and results from nl2sql_query tool executions.
        
        Args:
            event: The AfterInvocationEvent containing tool execution details
        """
        try:
            # Check if the event has the expected attributes
            if not hasattr(event, 'tool_name') or not hasattr(event, 'result'):
                return
                
            # Only process nl2sql_query tool calls
            if event.tool_name != "nl2sql_query":
                return
                
            logger.info(f"Capturing SQL results for tool: {event.tool_name}")
            
            # Extract tool result
            tool_result = event.result
            if not tool_result:
                logger.warning("No result found in event")
                return
                
            # Parse the tool result content
            content = tool_result["content"]
            if not content or not isinstance(content, list) or len(content) == 0:
                logger.warning("Invalid content structure in tool result")
                return
                
            # Get the text content (should contain JSON with sql and result)
            text_content = content[0].get("text", "")
            if not text_content:
                logger.warning("No text content found in tool result")
                return
                
            # Parse the response from nl2sql_tool (might be dict literal with single quotes)
            try:
                # Try JSON first, then fall back to ast.literal_eval for Python dict literals
                try:
                    nl2sql_response = json.loads(text_content)
                except json.JSONDecodeError:
                    # Handle Python dict literals with single quotes
                    nl2sql_response = ast.literal_eval(text_content)
            except (json.JSONDecodeError, ValueError, SyntaxError) as e:
                logger.warning(f"Failed to parse nl2sql tool response: {text_content}")
                return
                
            # Extract SQL and result details
            sql_query = nl2sql_response.get("sql", "")
            query_result = nl2sql_response.get("result", {})
            
            if not sql_query:
                logger.warning("No SQL query found in nl2sql response")
                return
                
            # Process the query result
            sql_details = self._process_query_result(sql_query, query_result)
            
            # Add intelligent chart analysis
            chart_config = self._analyze_chart_eligibility(sql_query, sql_details, self.user_question)
            if chart_config:
                sql_details["chart_config"] = chart_config
            
            # Store the captured details
            self.captured_sql_details = sql_details
            
            # Modify the tool result to include SQL details in a structured way
            self._enhance_tool_result(event, sql_details)
            
            logger.info(f"Successfully captured SQL details: {sql_details['result_count']} rows")
            
        except Exception as e:
            logger.error(f"Error capturing SQL results: {e}")
    
    def _process_query_result(self, sql_query: str, query_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process the query result into a structured format for UI display.
        
        Args:
            sql_query: The SQL query that was executed
            query_result: The result from SQLiteTool execution
            
        Returns:
            Structured SQL details for UI display
        """
        # Extract result data from SQLiteTool response
        rows = []
        columns = []
        result_count = 0
        execution_time = None
        
        if isinstance(query_result, dict):
            if "rows" in query_result:
                rows = query_result["rows"]
                result_count = len(rows) if rows else 0
                
            if "columns" in query_result:
                columns = query_result["columns"]
            elif rows and len(rows) > 0 and isinstance(rows[0], dict):
                # Extract columns from first row if not explicitly provided
                columns = list(rows[0].keys())
                
            if "execution_time" in query_result:
                execution_time = query_result["execution_time"]
        
        # Create structured SQL details
        sql_details = {
            "query": sql_query.strip(),
            "result_count": result_count,
            "columns": columns,
            "rows": rows[:100],  # Limit to first 100 rows for UI performance
            "total_rows": result_count,
            "execution_time": execution_time,
            "truncated": result_count > 100
        }
        
        return sql_details
    
    def _enhance_tool_result(self, event: AfterInvocationEvent, sql_details: Dict[str, Any]) -> None:
        """
        Enhance the tool result to include SQL details for UI consumption.
        
        Args:
            event: The AfterInvocationEvent to modify
            sql_details: The structured SQL details to include
        """
        try:
            # Get the current tool result
            tool_result = event.result
            
            # Parse the existing content
            content = tool_result["content"]
            text_content = content[0].get("text", "")
            
            # Parse the original nl2sql response
            try:
                original_response = json.loads(text_content)
            except json.JSONDecodeError:
                original_response = {"sql": "", "result": {}}
            
            # Create enhanced response with SQL details
            enhanced_response = {
                "sql": original_response.get("sql", ""),
                "result": original_response.get("result", {}),
                "sql_details": sql_details
            }
            
            # Update the tool result content
            content[0]["text"] = json.dumps(enhanced_response, ensure_ascii=False)
            
            logger.debug("Enhanced tool result with SQL details")
            
        except Exception as e:
            logger.error(f"Error enhancing tool result: {e}")
    
    def get_last_sql_details(self) -> Optional[Dict[str, Any]]:
        """
        Get the last captured SQL details.
        
        Returns:
            The last captured SQL details or None
        """
        return self.captured_sql_details
    
    def clear_sql_details(self) -> None:
        """Clear the captured SQL details."""
        self.captured_sql_details = None
    
    def set_user_question(self, question: str) -> None:
        """Set the user question for chart analysis context."""
        self.user_question = question
    
    def _analyze_chart_eligibility(self, sql_query: str, sql_details: Dict[str, Any], user_question: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Analyze if the SQL result is suitable for chart visualization and suggest optimal chart type.
        
        Args:
            sql_query: The executed SQL query
            sql_details: The processed SQL result details
            user_question: The original user question for context
            
        Returns:
            Chart configuration dict or None if not chart-worthy
        """
        try:
            rows = sql_details.get("rows", [])
            columns = sql_details.get("columns", [])
            result_count = sql_details.get("result_count", 0)
            
            # Basic eligibility checks
            if not self._is_chart_eligible(sql_query, rows, columns, result_count, user_question):
                return None
            
            # Analyze data patterns and suggest chart type
            chart_type = self._suggest_chart_type(sql_query, rows, columns, user_question)
            if not chart_type:
                return None
            
            # Generate chart configuration
            chart_config = self._generate_chart_config(chart_type, rows, columns, sql_query)
            
            logger.info(f"Generated chart config: {chart_type} with {len(rows)} data points")
            return chart_config
            
        except Exception as e:
            logger.error(f"Error analyzing chart eligibility: {e}")
            return None
    
    def _is_chart_eligible(self, sql_query: str, rows: List[Dict], columns: List[str], result_count: int, user_question: Optional[str] = None) -> bool:
        """Check if the data is suitable for chart visualization."""
        
        # Skip if too few rows
        if result_count < 2:
            return False
        
        # Skip if too many columns (likely a wide data dump)
        if len(columns) > 10:
            return False
        
        # Skip schema/metadata queries
        schema_keywords = ['PRAGMA', 'DESCRIBE', 'SHOW', 'INFORMATION_SCHEMA', 'sqlite_master']
        if any(keyword in sql_query.upper() for keyword in schema_keywords):
            return False
        
        # Skip if no numeric data for visualization
        numeric_cols = self._get_numeric_columns(rows, columns)
        if len(numeric_cols) == 0:
            return False
        
        # Check user question intent for visualization keywords
        if user_question:
            viz_keywords = ['show', 'compare', 'trend', 'distribution', 'chart', 'graph', 'plot', 'visualize']
            lookup_keywords = ['find', 'get', 'what is', 'which', 'who is', 'when is']
            
            question_lower = user_question.lower()
            has_viz_intent = any(keyword in question_lower for keyword in viz_keywords)
            has_lookup_intent = any(keyword in question_lower for keyword in lookup_keywords)
            
            # Prefer visualization if explicit viz keywords, avoid if lookup intent
            if has_lookup_intent and not has_viz_intent:
                return False
        
        return True
    
    def _suggest_chart_type(self, sql_query: str, rows: List[Dict], columns: List[str], user_question: Optional[str] = None) -> Optional[str]:
        """Suggest the best chart type based on data patterns and query context."""
        
        numeric_cols = self._get_numeric_columns(rows, columns)
        categorical_cols = [col for col in columns if col not in numeric_cols]
        
        # Check for time series data
        if self._has_time_column(rows, columns):
            return "line"  # Time series -> line chart
        
        # Check SQL query patterns
        sql_upper = sql_query.upper()
        
        # Aggregation queries with GROUP BY -> bar chart
        if 'GROUP BY' in sql_upper and 'COUNT' in sql_upper:
            return "bar"
        
        if 'GROUP BY' in sql_upper and any(agg in sql_upper for agg in ['SUM', 'AVG', 'MAX', 'MIN']):
            return "bar"
        
        # Two numeric columns -> scatter plot
        if len(numeric_cols) >= 2 and len(categorical_cols) >= 1:
            return "scatter"
        
        # Single categorical + single numeric -> bar chart
        if len(categorical_cols) == 1 and len(numeric_cols) == 1:
            # Check if it looks like parts of a whole
            if len(rows) <= 8 and 'percentage' in sql_query.lower():
                return "pie"
            return "bar"
        
        # Multiple numeric columns -> stacked bar or line
        if len(numeric_cols) > 2:
            return "stacked-bar"
        
        # Default fallback
        if len(categorical_cols) >= 1 and len(numeric_cols) >= 1:
            return "bar"
        
        return None
    
    def _generate_chart_config(self, chart_type: str, rows: List[Dict], columns: List[str], sql_query: str) -> Dict[str, Any]:
        """Generate chart configuration based on the suggested chart type."""
        
        numeric_cols = self._get_numeric_columns(rows, columns)
        categorical_cols = [col for col in columns if col not in numeric_cols]
        
        # Determine axes
        x_axis = categorical_cols[0] if categorical_cols else columns[0]
        y_axis = numeric_cols[0] if numeric_cols else columns[-1]
        
        # Generate chart title
        title = self._generate_chart_title(chart_type, x_axis, y_axis, sql_query)
        
        config = {
            "type": chart_type,
            "title": title,
            "x_axis": x_axis,
            "y_axis": y_axis,
            "eligible": True
        }
        
        # Add additional config for specific chart types
        if chart_type == "scatter" and len(numeric_cols) >= 2:
            config["x_axis"] = numeric_cols[0]
            config["y_axis"] = numeric_cols[1]
        
        if chart_type == "stacked-bar" and len(numeric_cols) > 1:
            config["series_columns"] = numeric_cols[1:4]  # Up to 3 additional series
        
        return config
    
    def _get_numeric_columns(self, rows: List[Dict], columns: List[str]) -> List[str]:
        """Identify numeric columns from the data."""
        if not rows:
            return []
        
        numeric_cols = []
        for col in columns:
            if col in rows[0]:
                sample_values = [row.get(col) for row in rows[:5] if row.get(col) is not None]
                if sample_values and all(isinstance(v, (int, float)) or (isinstance(v, str) and v.replace('.', '').replace('-', '').isdigit()) for v in sample_values):
                    numeric_cols.append(col)
        
        return numeric_cols
    
    def _has_time_column(self, rows: List[Dict], columns: List[str]) -> bool:
        """Check if data contains time/date columns."""
        time_keywords = ['date', 'time', 'year', 'month', 'day', 'created', 'updated']
        
        for col in columns:
            col_lower = col.lower()
            if any(keyword in col_lower for keyword in time_keywords):
                return True
        
        return False
    
    def _generate_chart_title(self, chart_type: str, x_axis: str, y_axis: str, sql_query: str) -> str:
        """Generate an appropriate chart title."""
        
        # Extract table name from query
        table_match = re.search(r'FROM\s+(\w+)', sql_query, re.IGNORECASE)
        table_name = table_match.group(1).title() if table_match else "Data"
        
        if chart_type == "bar":
            return f"{y_axis.title()} by {x_axis.title()}"
        elif chart_type == "line":
            return f"{y_axis.title()} Over Time"
        elif chart_type == "pie":
            return f"{table_name} Distribution"
        elif chart_type == "scatter":
            return f"{x_axis.title()} vs {y_axis.title()}"
        elif chart_type == "stacked-bar":
            return f"{table_name} Metrics by {x_axis.title()}"
        else:
            return f"{table_name} Analysis"
