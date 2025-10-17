"""
Customer Profile Tool for Financial Advisory Agent.
Allows the agent to update customer information during conversations.
"""

from typing import Dict, Any, Optional
from .base_tool import BaseTool
from services.customer_service import customer_service, Customer, CustomerAssessment

class CustomerProfileTool(BaseTool):
    """Tool for updating customer profile information during conversations."""
    
    @property
    def name(self) -> str:
        """Return the tool name."""
        return "customer_profile"
    
    @property
    def description(self) -> str:
        """Return the tool description."""
        return """Update customer profile information during conversation. Use this to capture and store customer details, preferences, and assessment responses.

        Args:
            customer_id: Customer ID to update
            update_type: Type of update - basic_info/assessment/persona
            data: Data to update (dict with relevant fields)
            
        Returns:
            Result of the profile update operation
        """
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute the customer profile update."""
        try:
            # Extract parameters
            customer_id = kwargs.get('customer_id')
            update_type = kwargs.get('update_type')
            data = kwargs.get('data', {})
            
            if not customer_id or not update_type:
                return {
                    "success": False,
                    "error": "customer_id and update_type are required"
                }
            
            if update_type == "basic_info":
                return self._update_basic_info(customer_id, data)
            elif update_type == "assessment":
                return self._update_assessment(customer_id, data)
            elif update_type == "persona":
                return self._update_persona(customer_id, data)
            else:
                return {
                    "success": False,
                    "error": f"Invalid update_type: {update_type}. Must be 'basic_info', 'assessment', or 'persona'"
                }
        
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to update customer profile: {str(e)}"
            }
    
    def _update_basic_info(self, customer_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update basic customer information."""
        # Validate required fields
        allowed_fields = {
            'first_name', 'last_name', 'dob', 'country', 'state', 'zip',
            'household_id', 'marital_status', 'dependents_cnt', 'education_level',
            'student_status', 'citizenship_status', 'kyc_verified_bool',
            'consent_data_sharing_bool', 'savings_rate_target', 'base_salary_annual',
            'fico_baseline', 'cc_util_baseline'
        }
        
        # Filter data to only include allowed fields
        filtered_data = {k: v for k, v in data.items() if k in allowed_fields}
        
        if not filtered_data:
            return {
                "success": False,
                "error": "No valid fields provided for basic_info update"
            }
        
        # Update customer
        updated_customer = customer_service.update_customer(customer_id, filtered_data)
        
        if updated_customer:
            return {
                "success": True,
                "message": f"Updated basic information for customer {customer_id}",
                "updated_fields": list(filtered_data.keys()),
                "customer": {
                    "customer_id": updated_customer.customer_id,
                    "first_name": updated_customer.first_name,
                    "last_name": updated_customer.last_name,
                    "base_salary_annual": updated_customer.base_salary_annual
                }
            }
        else:
            return {
                "success": False,
                "error": f"Customer {customer_id} not found"
            }
    
    def _update_assessment(self, customer_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update customer assessment information."""
        # Validate required fields
        allowed_fields = {
            'email', 'phone', 'primary_goal', 'debt_status', 'employment_status',
            'timeline', 'risk_tolerance'
        }
        
        # Filter data to only include allowed fields
        filtered_data = {k: v for k, v in data.items() if k in allowed_fields}
        
        if not filtered_data:
            return {
                "success": False,
                "error": "No valid fields provided for assessment update"
            }
        
        # Check if assessment exists, if not create it
        existing_assessment = customer_service.get_customer_assessment(customer_id)
        
        if existing_assessment:
            # Update existing assessment
            updated_assessment = customer_service.update_assessment(customer_id, filtered_data)
        else:
            # Create new assessment
            updated_assessment = customer_service.create_assessment(customer_id, filtered_data)
        
        if updated_assessment:
            return {
                "success": True,
                "message": f"Updated assessment for customer {customer_id}",
                "updated_fields": list(filtered_data.keys()),
                "assessment": {
                    "customer_id": updated_assessment.customer_id,
                    "primary_goal": updated_assessment.primary_goal,
                    "debt_status": updated_assessment.debt_status,
                    "employment_status": updated_assessment.employment_status,
                    "timeline": updated_assessment.timeline,
                    "risk_tolerance": updated_assessment.risk_tolerance
                }
            }
        else:
            return {
                "success": False,
                "error": f"Failed to update assessment for customer {customer_id}"
            }
    
    def _update_persona(self, customer_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update customer persona."""
        persona_type = data.get('persona_type')
        
        if not persona_type:
            return {
                "success": False,
                "error": "persona_type is required for persona update"
            }
        
        # Validate persona type
        valid_personas = {
            'high_spending_student_debtor',
            'aspiring_homebuyer_moderate_savings',
            'credit_card_juggler',
            'consistent_saver_idle_cash',
            'freelancer_income_volatility',
            'general'
        }
        
        if persona_type not in valid_personas:
            return {
                "success": False,
                "error": f"Invalid persona_type: {persona_type}. Must be one of: {', '.join(valid_personas)}"
            }
        
        # Update customer persona
        updated_customer = customer_service.update_customer(customer_id, {'persona_type': persona_type})
        
        if updated_customer:
            return {
                "success": True,
                "message": f"Updated persona for customer {customer_id}",
                "persona_type": persona_type,
                "customer": {
                    "customer_id": updated_customer.customer_id,
                    "first_name": updated_customer.first_name,
                    "last_name": updated_customer.last_name,
                    "persona_type": updated_customer.persona_type
                }
            }
        else:
            return {
                "success": False,
                "error": f"Customer {customer_id} not found"
            }
    
    def get_customer_context(self, customer_id: str) -> Dict[str, Any]:
        """Get customer context for the agent."""
        try:
            context = customer_service.get_customer_context(customer_id)
            return {
                "success": True,
                "context": context
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to get customer context: {str(e)}"
            }
    
    def create_new_customer(self, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new customer from assessment form data."""
        try:
            # Validate required fields
            required_fields = ['first_name', 'last_name']
            missing_fields = [field for field in required_fields if not customer_data.get(field)]
            
            if missing_fields:
                return {
                    "success": False,
                    "error": f"Missing required fields: {', '.join(missing_fields)}"
                }
            
            # Create customer
            customer = customer_service.create_customer(customer_data)
            
            if customer:
                return {
                    "success": True,
                    "message": f"Created new customer {customer.customer_id}",
                    "customer": {
                        "customer_id": customer.customer_id,
                        "first_name": customer.first_name,
                        "last_name": customer.last_name,
                        "base_salary_annual": customer.base_salary_annual
                    }
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to create customer"
                }
        
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to create customer: {str(e)}"
            }
    
    def assign_persona_automatically(self, customer_id: str) -> Dict[str, Any]:
        """Automatically assign persona based on customer profile and assessment."""
        try:
            persona_type = customer_service.assign_persona(customer_id)
            
            # Update the customer with the assigned persona
            updated_customer = customer_service.update_customer(customer_id, {'persona_type': persona_type})
            
            if updated_customer:
                return {
                    "success": True,
                    "message": f"Automatically assigned persona '{persona_type}' to customer {customer_id}",
                    "persona_type": persona_type,
                    "customer": {
                        "customer_id": updated_customer.customer_id,
                        "first_name": updated_customer.first_name,
                        "last_name": updated_customer.last_name,
                        "persona_type": updated_customer.persona_type
                    }
                }
            else:
                return {
                    "success": False,
                    "error": f"Customer {customer_id} not found"
                }
        
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to assign persona: {str(e)}"
            }
