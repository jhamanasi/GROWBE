"""
Financial Conversation Hook for Financial Advisory Agent.
Captures financial information and updates customer profiles during conversations.
"""

import re
from typing import Dict, Any, Optional
from strands.hooks import HookProvider, HookRegistry, MessageAddedEvent
from services.customer_service import customer_service

class FinancialConversationHook(HookProvider):
    """Hook to capture financial information during conversations and update customer profiles."""
    
    def __init__(self):
        self.financial_patterns = {
            'income': [
                r'(?:salary|income|earn|make|annual|yearly).*?(\$?[\d,]+(?:\.\d{2})?)',
                r'(\$?[\d,]+(?:\.\d{2})?).*?(?:salary|income|earn|make|annual|yearly)',
                r'(?:I make|I earn|my salary|my income).*?(\$?[\d,]+(?:\.\d{2})?)'
            ],
            'debt': [
                r'(?:debt|owe|loan|credit card).*?(\$?[\d,]+(?:\.\d{2})?)',
                r'(\$?[\d,]+(?:\.\d{2})?).*?(?:debt|owe|loan|credit card)',
                r'(?:I owe|my debt|my loan).*?(\$?[\d,]+(?:\.\d{2})?)'
            ],
            'savings': [
                r'(?:savings|save|emergency fund).*?(\$?[\d,]+(?:\.\d{2})?)',
                r'(\$?[\d,]+(?:\.\d{2})?).*?(?:savings|save|emergency fund)',
                r'(?:I have|I saved|my savings).*?(\$?[\d,]+(?:\.\d{2})?)'
            ],
            'goals': [
                r'(?:goal|want|need|plan).*?(?:to|for).*?(?:buy|purchase|get|achieve)',
                r'(?:house|home|car|education|retirement|debt)',
                r'(?:down payment|mortgage|loan|investment)'
            ]
        }
        
        self.assessment_questions = {
            'primary_goal': [
                'What is your primary financial goal?',
                'What are you trying to achieve financially?',
                'What is your main financial priority?'
            ],
            'debt_status': [
                'How would you describe your current debt situation?',
                'Do you have any outstanding debts or loans?',
                'What is your current debt level?'
            ],
            'employment_status': [
                'What is your current employment status?',
                'Are you employed full-time, part-time, or self-employed?',
                'What type of work do you do?'
            ],
            'timeline': [
                'When do you want to achieve your financial goal?',
                'What is your timeline for this goal?',
                'How soon do you need to reach this goal?'
            ],
            'risk_tolerance': [
                'How comfortable are you with investment risk?',
                'Would you describe yourself as conservative, moderate, or aggressive with investments?',
                'How do you feel about market volatility?'
            ]
        }
    
    def register_hooks(self, registry: HookRegistry) -> None:
        """Register the hook callbacks for message events."""
        registry.add_callback(MessageAddedEvent, self.on_message_added)
    
    def on_message_added(self, event: MessageAddedEvent) -> None:
        """Handle message added events to extract financial information."""
        try:
            # Extract message content and session info
            message = event.message.get("content", "")
            session_id = event.message.get("session_id", "")
            
            if message and session_id:
                self.on_message_received(message, session_id)
        except Exception as e:
            print(f"Error in financial conversation hook: {str(e)}")
    
    def on_message_received(self, message: str, session_id: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Process incoming messages to extract financial information."""
        try:
            # Extract financial information from the message
            extracted_info = self._extract_financial_info(message)
            
            if extracted_info:
                # Update customer profile with extracted information
                self._update_customer_profile(session_id, extracted_info)
                
                return {
                    "extracted_financial_info": extracted_info,
                    "session_id": session_id
                }
            
            return None
        
        except Exception as e:
            print(f"Error in FinancialConversationHook: {str(e)}")
            return None
    
    def on_message_sent(self, message: str, session_id: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Process outgoing messages to identify assessment questions."""
        try:
            # Check if this is an assessment question
            assessment_type = self._identify_assessment_question(message)
            
            if assessment_type:
                return {
                    "assessment_question_type": assessment_type,
                    "session_id": session_id
                }
            
            return None
        
        except Exception as e:
            print(f"Error in FinancialConversationHook: {str(e)}")
            return None
    
    def _extract_financial_info(self, message: str) -> Dict[str, Any]:
        """Extract financial information from a message."""
        extracted = {}
        message_lower = message.lower()
        
        # Extract income information
        income_matches = self._extract_with_patterns(message, self.financial_patterns['income'])
        if income_matches:
            extracted['income'] = self._parse_currency(income_matches[0])
        
        # Extract debt information
        debt_matches = self._extract_with_patterns(message, self.financial_patterns['debt'])
        if debt_matches:
            extracted['debt'] = self._parse_currency(debt_matches[0])
        
        # Extract savings information
        savings_matches = self._extract_with_patterns(message, self.financial_patterns['savings'])
        if savings_matches:
            extracted['savings'] = self._parse_currency(savings_matches[0])
        
        # Extract goal information
        goal_matches = self._extract_with_patterns(message, self.financial_patterns['goals'])
        if goal_matches:
            extracted['goal_mentioned'] = True
        
        return extracted
    
    def _extract_with_patterns(self, message: str, patterns: list) -> list:
        """Extract matches using multiple patterns."""
        matches = []
        for pattern in patterns:
            regex_matches = re.findall(pattern, message, re.IGNORECASE)
            matches.extend(regex_matches)
        return matches
    
    def _parse_currency(self, currency_str: str) -> Optional[float]:
        """Parse currency string to float."""
        try:
            # Remove currency symbols and commas
            cleaned = re.sub(r'[$,]', '', currency_str)
            return float(cleaned)
        except (ValueError, TypeError):
            return None
    
    def _identify_assessment_question(self, message: str) -> Optional[str]:
        """Identify if a message is an assessment question."""
        message_lower = message.lower()
        
        for question_type, questions in self.assessment_questions.items():
            for question in questions:
                if any(word in message_lower for word in question.lower().split()):
                    return question_type
        
        return None
    
    def _update_customer_profile(self, session_id: str, extracted_info: Dict[str, Any]):
        """Update customer profile with extracted financial information."""
        try:
            # Get customer by session_id
            customer = customer_service.get_customer_by_session_id(session_id)
            
            if not customer:
                print(f"Customer not found for session_id: {session_id}")
                return
            
            # Prepare update data
            update_data = {}
            
            if 'income' in extracted_info:
                update_data['base_salary_annual'] = int(extracted_info['income'])
            
            # Update customer if we have data
            if update_data:
                customer_service.update_customer(customer.customer_id, update_data)
                print(f"Updated customer {customer.customer_id} with extracted info: {update_data}")
        
        except Exception as e:
            print(f"Error updating customer profile: {str(e)}")
    
    def get_assessment_questions(self, question_type: str) -> list:
        """Get assessment questions for a specific type."""
        return self.assessment_questions.get(question_type, [])
    
    def get_all_assessment_questions(self) -> Dict[str, list]:
        """Get all assessment questions."""
        return self.assessment_questions
    
    def suggest_next_assessment_question(self, customer_id: str) -> Optional[str]:
        """Suggest the next assessment question based on what's missing."""
        try:
            customer = customer_service.get_customer(customer_id)
            assessment = customer_service.get_customer_assessment(customer_id)
            
            if not customer:
                return None
            
            # If no assessment exists, start with primary goal
            if not assessment:
                return self.assessment_questions['primary_goal'][0]
            
            # Check what's missing in assessment
            missing_fields = []
            
            if not assessment.primary_goal:
                missing_fields.append('primary_goal')
            if not assessment.debt_status:
                missing_fields.append('debt_status')
            if not assessment.employment_status:
                missing_fields.append('employment_status')
            if not assessment.timeline:
                missing_fields.append('timeline')
            if not assessment.risk_tolerance:
                missing_fields.append('risk_tolerance')
            
            # Return first missing field's question
            if missing_fields:
                return self.assessment_questions[missing_fields[0]][0]
            
            return None
        
        except Exception as e:
            print(f"Error suggesting next assessment question: {str(e)}")
            return None
