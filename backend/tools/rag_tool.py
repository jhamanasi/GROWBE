"""
Knowledge Base Search Tool (RAG Tool)

This tool searches the financial knowledge base to provide evidence-based 
advice, explanations, and context for the agent's recommendations.

KEY CHARACTERISTICS:
- Always used ALONGSIDE calculation tools, not instead of them
- Provides supporting evidence and context for recommendations
- Returns cited sources for financial concepts
- Works in parallel with other tools for comprehensive advice
"""

from typing import Dict, Any, Optional
from .base_tool import BaseTool


class KnowledgeBaseSearchTool(BaseTool):
    """
    Search the financial knowledge base for concepts, strategies, and advice.
    
    PURPOSE:
    This tool provides evidence-based financial knowledge to support and 
    contextualize the agent's advice. It should be used to:
    - Explain financial concepts (APR, DTI, credit scores, etc.)
    - Provide debt management strategies (avalanche, snowball, etc.)
    - Offer context for loan/mortgage decisions
    - Support recommendations with cited sources
    
    WHEN TO USE:
    - User asks "What is X?" or "How does X work?"
    - User asks for advice/strategies on debt, credit, loans, etc.
    - You need to explain WHY a recommendation makes sense
    - You want to provide educational context alongside calculations
    
    PARALLEL USAGE (CRITICAL):
    This tool is designed to work IN PARALLEL with calculation tools:
    
    Example 1 - Loan Payoff Strategy:
    User: "How can I pay off my student loan faster?"
    Parallel calls:
    1. knowledge_base_search(query="student loan accelerated payoff strategies")
    2. debt_optimizer(customer_id=C001, extra_payment=200, ...)
    → Combine: calculation results + strategic advice from Kbase
    
    Example 2 - Debt Management Advice:
    User: "Should I focus on my high-interest credit card or small auto loan?"
    Parallel calls:
    1. knowledge_base_search(query="debt avalanche vs debt snowball strategy")
    2. nl2sql_query(customer_id=C001, query="show all my debts with interest rates")
    → Combine: user's actual debts + strategic framework from Kbase
    
    Example 3 - Credit Score Impact:
    User: "Will consolidating my credit cards hurt my credit score?"
    Parallel calls:
    1. knowledge_base_search(query="credit card consolidation impact on credit score")
    2. nl2sql_query(customer_id=C001, query="show my credit cards and utilization")
    → Combine: user's current situation + credit impact knowledge
    
    RESPONSE FORMAT:
    Always cite sources! Example:
    "According to Investopedia, the Debt Avalanche method prioritizes paying 
    off debts with the highest interest rates first, which can save you 
    significant money over time. [Source: https://...]
    
    Based on your student loan at 5.13% APR, this strategy would mean..."
    
    LIMITATIONS:
    - This tool provides GENERAL financial knowledge, not personalized advice
    - Always combine Kbase results with user-specific data and calculations
    - If Kbase has no relevant info, acknowledge and provide general guidance
    """
    
    @property
    def name(self) -> str:
        """Return the name of the tool."""
        return "knowledge_base_search"
    
    @property
    def description(self) -> str:
        """Return the description of the tool."""
        return """Search the financial knowledge base for concepts, strategies, and advice.

USE THIS TOOL TO:
- Explain financial concepts (APR, credit scores, DTI, amortization, etc.)
- Provide debt management strategies (avalanche, snowball, consolidation, etc.)
- Offer mortgage/housing guidance (rent vs buy, refinancing, etc.)
- Support recommendations with evidence and citations

IMPORTANT - PARALLEL TOOL USAGE:
This tool should be used IN PARALLEL with calculation/data tools:
- Use with debt_optimizer for strategy + calculations
- Use with nl2sql_query for concepts + user data
- Use with financial_summary_tool for context + overview

PARAMETERS:
- query: Natural language question or topic to search (required)
- knowledge_base: Specific Kbase to search (optional, auto-routes if omitted)
- top_k: Number of results to return (default: 3)

EXAMPLES:
1. "debt avalanche vs debt snowball strategy"
2. "how does credit utilization affect credit score"
3. "student loan income-driven repayment plans"
4. "mortgage refinancing when to consider"
5. "APR vs interest rate difference"

ALWAYS CITE SOURCES in your response using the 'citations' field from results."""
    
    def __init__(self):
        """Initialize the RAG tool."""
        super().__init__()
        self._manager = None  # Lazy load to avoid import issues
    
    def _get_manager(self):
        """Lazy load the KnowledgeBaseManager."""
        if self._manager is None:
            import os
            from pathlib import Path
            from rag.kbase_manager import KnowledgeBaseManager
            
            # Get absolute path to vector_db
            backend_dir = Path(__file__).resolve().parents[1]  # Go up from tools/ to backend/
            vector_db_path = backend_dir / "rag" / "vector_db"
            
            self._manager = KnowledgeBaseManager(vector_db_path=str(vector_db_path))
        return self._manager
    
    def execute(
        self,
        query: str,
        knowledge_base: Optional[str] = None,
        top_k: int = 3
    ) -> Dict[str, Any]:
        """
        Search the financial knowledge base.
        
        Args:
            query: Natural language question or topic to search
            knowledge_base: Specific Kbase name (optional, auto-routes if omitted)
            top_k: Number of results to return
            
        Returns:
            Dict containing search results with content, metadata, and citations
        """
        # Validate inputs
        if not query or not query.strip():
            return {
                "success": False,
                "error": "Query cannot be empty",
                "stop_retrying": True
            }
        
        if top_k < 1 or top_k > 10:
            return {
                "success": False,
                "error": "top_k must be between 1 and 10",
                "stop_retrying": True
            }
        
        try:
            # Get manager and search
            manager = self._get_manager()
            results = manager.search(
                query=query,
                knowledge_base=knowledge_base,
                top_k=top_k
            )
            
            if not results:
                return {
                    "success": True,
                    "query": query,
                    "results_found": 0,
                    "message": "No relevant information found in the knowledge base for this query. "
                              "You may need to provide general guidance based on standard financial principles.",
                    "results": []
                }
            
            # Format results for the agent
            formatted_results = []
            for i, result in enumerate(results, 1):
                # Create pre-formatted citation string for easy use
                citations = result.get('citations', [])
                citation_url = citations[0] if citations else "No URL available"
                
                # Extract source name from URL for nicer formatting
                source_name = "Financial Source"
                if citation_url and isinstance(citation_url, str):
                    if 'investopedia.com' in citation_url:
                        source_name = "Investopedia"
                    elif 'nerdwallet.com' in citation_url:
                        source_name = "NerdWallet"
                    elif 'bankrate.com' in citation_url:
                        source_name = "Bankrate"
                    elif 'experian.com' in citation_url:
                        source_name = "Experian"
                    elif 'cfpb.gov' in citation_url:
                        source_name = "Consumer Financial Protection Bureau (CFPB)"
                
                # Clean hyperlink format (Markdown)
                formatted_citation = f"**Source:** [{source_name}]({citation_url})"
                formatted_citation_with_name = f"According to {source_name}, ... \n\n**Source:** [{source_name}]({citation_url})"
                
                formatted_results.append({
                    "rank": i,
                    "title": result['metadata'].get('title', 'Untitled'),
                    "topic": result['metadata'].get('topic', 'general'),
                    "content": result['content'],
                    "similarity_score": round(result['similarity_score'], 3),
                    "citations": citations,
                    "citation_url": citation_url,
                    "source_name": source_name,
                    "formatted_citation": formatted_citation,
                    "citation_template": formatted_citation_with_name,
                    "keywords": result['metadata'].get('keywords', [])
                })
            

            return {
                "success": True,
                "query": query,
                "results_found": len(formatted_results),
                "results": formatted_results,
                "message": f"Found {len(formatted_results)} relevant knowledge base entries. "
                          f"Use this information to support your advice and ALWAYS cite sources."
            }
            
        except Exception as e:
            print(f"❌ RAG Tool Error: {e}")
            return {
                "success": False,
                "error": f"Knowledge base search failed: {str(e)}",
                "query": query,
                "stop_retrying": True
            }

