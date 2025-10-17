"""
Conversation Capture Hook for Strands Agents

This hook captures user messages and agent responses in real-time
and automatically saves them to the database for lead management.
"""
from typing import Any, Dict, List, Optional
from strands.hooks import HookProvider, HookRegistry
from strands.hooks.events import AfterInvocationEvent
import json
import logging
import re
from datetime import datetime

logger = logging.getLogger(__name__)


class ConversationCaptureHook(HookProvider):
    """
    Hook to capture user messages and agent responses in real-time.
    
    This hook automatically saves conversations to the database
    for lead management and realtor access.
    """
    
    def __init__(self, lead_service=None):
        self.lead_service = lead_service
        self.current_session_id = None
        self.current_lead_id = None
        self.pending_user_message = None
        
    def register_hooks(self, registry: HookRegistry) -> None:
        """Register the hook callback for AfterInvocationEvent."""
        registry.add_callback(AfterInvocationEvent, self.capture_conversation)
    
    def set_session_context(self, session_id: str, lead_id: int = None):
        """Set the current session context for conversation tracking."""
        self.current_session_id = session_id
        self.current_lead_id = lead_id
        logger.info(f"Set conversation context: session={session_id}, lead={lead_id}")
    
    def set_pending_user_message(self, message: str):
        """Set the pending user message to be saved with the next agent response."""
        self.pending_user_message = message
        logger.debug(f"Set pending user message: {message[:50]}...")
    
    def capture_conversation(self, event: AfterInvocationEvent) -> None:
        """
        Capture and save agent responses.
        
        Args:
            event: The AfterInvocationEvent containing agent response details
        """
        try:
            # Only process if we have session context
            if not self.current_session_id or not self.lead_service:
                return
                
            # Get the current lead if not already set
            if not self.current_lead_id:
                lead = self.lead_service.get_lead_by_session_id(self.current_session_id)
                if lead:
                    self.current_lead_id = lead.id
                else:
                    logger.warning(f"No lead found for session {self.current_session_id}")
                    return
            
            # Save pending user message if we have one
            if self.pending_user_message:
                self._save_user_message(self.pending_user_message)
                
                # Parse user message for lead updates
                user_lead_updates = self._parse_lead_updates(self.pending_user_message)
                if user_lead_updates:
                    self._update_lead_information(user_lead_updates)
                
                self.pending_user_message = None
            
            # Extract agent response from the event
            agent_response = self._extract_agent_response(event)
            if agent_response:
                self._save_agent_response(agent_response)
                
                # Parse agent response for lead updates
                lead_updates = self._parse_lead_updates(agent_response)
                if lead_updates:
                    self._update_lead_information(lead_updates)
            
            logger.info(f"Captured conversation for lead {self.current_lead_id}")
            
        except Exception as e:
            logger.error(f"Error capturing conversation: {e}")
    
    def _extract_agent_response(self, event: AfterInvocationEvent) -> Optional[str]:
        """
        Extract agent response from the event.
        
        Args:
            event: The AfterInvocationEvent
            
        Returns:
            Agent response text or None
        """
        try:
            # Extract response from the event result
            if hasattr(event, 'result') and event.result:
                if isinstance(event.result, dict) and 'content' in event.result:
                    content = event.result['content']
                    if isinstance(content, list) and len(content) > 0:
                        if isinstance(content[0], dict) and 'text' in content[0]:
                            return content[0]['text']
                    elif isinstance(content, str):
                        return content
                elif isinstance(event.result, str):
                    return event.result
            
            return None
            
        except Exception as e:
            logger.error(f"Error extracting agent response: {e}")
            return None
    
    def _save_user_message(self, message: str) -> None:
        """Save user message to the database."""
        try:
            from models.lead_models import ConversationCreate
            
            conversation_data = ConversationCreate(
                lead_id=self.current_lead_id,
                message=message,
                is_user=True
            )
            
            self.lead_service.add_conversation(conversation_data)
            logger.debug(f"Saved user message: {message[:50]}...")
            
        except Exception as e:
            logger.error(f"Error saving user message: {e}")
    
    def _save_agent_response(self, response: str) -> None:
        """Save agent response to the database."""
        try:
            from models.lead_models import ConversationCreate
            
            conversation_data = ConversationCreate(
                lead_id=self.current_lead_id,
                message=response,
                is_user=False
            )
            
            self.lead_service.add_conversation(conversation_data)
            logger.debug(f"Saved agent response: {response[:50]}...")
            
        except Exception as e:
            logger.error(f"Error saving agent response: {e}")
    
    def _update_lead_information(self, updates: Dict[str, Any]) -> None:
        """Update lead information based on conversation content."""
        try:
            print(f"\n🔧 DEBUG _update_lead_information called:")
            print(f"   - current_lead_id: {self.current_lead_id}")
            print(f"   - updates: {updates}")
            
            if not updates:
                print(f"   ⚠️  No updates to apply")
                return
            
            if not self.current_lead_id:
                print(f"   ❌ ERROR: current_lead_id is None!")
                logger.error("Cannot update lead: current_lead_id is None")
                return
            
            # Create LeadUpdate model from updates
            from models.lead_models import LeadUpdate
            print(f"   - Creating LeadUpdate model...")
            lead_update = LeadUpdate(**updates)
            print(f"   - LeadUpdate model created: {lead_update}")
            
            # Update lead with new information
            print(f"   - Calling lead_service.update_lead({self.current_lead_id}, ...)")
            updated_lead = self.lead_service.update_lead(self.current_lead_id, lead_update)
            print(f"   ✅ Lead updated successfully!")
            print(f"   - Updated fields: {list(updates.keys())}")
            print(f"   - New values: location={updated_lead.location}, property_type={updated_lead.property_type}, bedrooms={updated_lead.bedrooms}\n")
            logger.info(f"Updated lead {self.current_lead_id} with: {list(updates.keys())}")
            
        except Exception as e:
            print(f"   ❌ ERROR in _update_lead_information: {e}")
            import traceback
            traceback.print_exc()
            logger.error(f"Error updating lead information: {e}")
    
    def _parse_lead_updates(self, agent_response: str) -> Dict[str, Any]:
        """
        Parse agent response to extract lead information updates.
        
        Args:
            agent_response: The agent's response text
            
        Returns:
            Dictionary of lead field updates
        """
        updates = {}
        response_lower = agent_response.lower()
        
        # Extract location information
        location = self._extract_location(agent_response)
        if location:
            updates['location'] = location
        
        # Extract budget information
        budget_info = self._extract_budget(agent_response)
        if budget_info:
            updates.update(budget_info)
        
        # Extract timeline information
        timeline = self._extract_timeline(agent_response)
        if timeline:
            updates['timeline'] = timeline
        
        # Extract property requirements
        property_info = self._extract_property_requirements(agent_response)
        if property_info:
            updates.update(property_info)
        
        # Extract motivation
        motivation = self._extract_motivation(agent_response)
        if motivation:
            updates['motivation'] = motivation
        
        # Extract pre-approval status
        pre_approved = self._extract_pre_approval(agent_response)
        if pre_approved is not None:
            updates['pre_approved'] = pre_approved
        
        # Update engagement score based on response length and content
        engagement_score = self._calculate_engagement_score(agent_response)
        if engagement_score > 0:
            updates['engagement_score'] = engagement_score
        
        return updates
    
    def _extract_location(self, text: str) -> Optional[str]:
        """Extract location information from conversation text."""
        # First check for City, State patterns (Windsor, NJ or Austin, TX)
        city_state_pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*),\s*([A-Z]{2})\b'
        city_state_match = re.search(city_state_pattern, text)
        if city_state_match:
            city = city_state_match.group(1).strip()
            state = city_state_match.group(2).strip()
            return f"{city}, {state}"
        
        # Look for location patterns
        location_patterns = [
            r'(?:in|around|near|close to)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'(?:looking in|interested in)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'(?:area|neighborhood|city)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'(?:like|love|interested in)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:GA|CA|NY|TX|FL|VA|MD|DC|NJ|PA)\b'  # City + State pattern
        ]
        
        for pattern in location_patterns:
            match = re.search(pattern, text)
            if match:
                location = match.group(1).strip()
                # Filter out common false positives
                if location.lower() not in ['the', 'this', 'that', 'your', 'my', 'our', 'idk', 'work']:
                    return location
        
        # Special case for "Cumming GA" pattern
        cumming_match = re.search(r'\b(Cumming)\s+(GA)\b', text, re.IGNORECASE)
        if cumming_match:
            return f"{cumming_match.group(1)} {cumming_match.group(2)}"
        
        return None
    
    def _extract_budget(self, text: str) -> Dict[str, Any]:
        """Extract budget information from conversation text."""
        budget_info = {}
        
        # Look for specific budget amounts
        budget_patterns = [
            r'\$(\d+(?:,\d{3})*(?:k|K)?)\s*-\s*\$(\d+(?:,\d{3})*(?:k|K)?)',
            r'budget.*?\$(\d+(?:,\d{3})*(?:k|K)?)\s*-\s*\$(\d+(?:,\d{3})*(?:k|K)?)',
            r'around\s*\$(\d+(?:,\d{3})*(?:k|K)?)',
            r'up to\s*\$(\d+(?:,\d{3})*(?:k|K)?)'
        ]
        
        for pattern in budget_patterns:
            match = re.search(pattern, text)
            if match:
                if len(match.groups()) == 2:  # Range
                    min_budget = self._parse_budget_amount(match.group(1))
                    max_budget = self._parse_budget_amount(match.group(2))
                    if min_budget and max_budget:
                        budget_info['budget_min'] = min_budget
                        budget_info['budget_max'] = max_budget
                elif len(match.groups()) == 1:  # Single amount
                    amount = self._parse_budget_amount(match.group(1))
                    if amount:
                        budget_info['budget_max'] = amount
                break
        
        return budget_info
    
    def _parse_budget_amount(self, amount_str: str) -> Optional[int]:
        """Parse budget amount string to integer."""
        try:
            # Remove commas and convert k/K to thousands
            amount_str = amount_str.replace(',', '')
            if amount_str.lower().endswith('k'):
                return int(amount_str[:-1]) * 1000
            return int(amount_str)
        except (ValueError, AttributeError):
            return None
    
    def _extract_timeline(self, text: str) -> Optional[str]:
        """Extract timeline information from conversation text."""
        timeline_patterns = [
            r'(?:in|within)\s+(\d+\s*(?:weeks?|months?|days?))',
            r'(?:by|before)\s+([A-Z][a-z]+ \d{1,2})',
            r'(?:asap|as soon as possible)',
            r'(?:next|this)\s+(?:week|month)',
            r'(\d+\s*(?:weeks?|months?))\s+(?:from now|time)'
        ]
        
        for pattern in timeline_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0).strip()
        
        return None
    
    def _extract_property_requirements(self, text: str) -> Dict[str, Any]:
        """Extract property requirements from conversation text."""
        requirements = {}
        
        # Word to number mapping for bedrooms
        word_to_number = {
            'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
            'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10
        }
        
        # Extract bedrooms
        bedroom_match = re.search(r'(\d+)\s*(?:bed|bedroom)', text, re.IGNORECASE)
        if bedroom_match:
            requirements['bedrooms'] = int(bedroom_match.group(1))
        else:
            # Check for word numbers (one, two, three, four, etc.)
            for word, number in word_to_number.items():
                if re.search(r'\b' + word + r'\b', text.lower()):
                    requirements['bedrooms'] = number
                    break
            
            # If no word match, try to extract standalone numbers (1-10)
            if 'bedrooms' not in requirements:
                standalone_number = re.search(r'\b([1-9]|10)\b', text)
                if standalone_number and len(text.strip()) <= 10:  # Short responses likely to be bedroom count
                    requirements['bedrooms'] = int(standalone_number.group(1))
        
        # Extract bathrooms
        bathroom_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:bath|bathroom)', text, re.IGNORECASE)
        if bathroom_match:
            requirements['bathrooms'] = float(bathroom_match.group(1))
        
        # Extract property type (check more specific types first)
        property_types = ['single home', 'single family', 'townhouse', 'multi-family', 'apartment', 'condo', 'house']
        for prop_type in property_types:
            if prop_type in text.lower():
                if prop_type in ['single home', 'single family']:
                    requirements['property_type'] = 'House'  # Map to House enum
                elif prop_type == 'multi-family':
                    requirements['property_type'] = 'Multi-family'
                else:
                    requirements['property_type'] = prop_type.title()
                break
        
        return requirements
    
    def _extract_motivation(self, text: str) -> Optional[str]:
        """Extract motivation from conversation text."""
        motivation_keywords = [
            'job relocation', 'work', 'career', 'family', 'kids', 'school',
            'downsizing', 'upsizing', 'investment', 'retirement', 'divorce',
            'new job', 'promotion', 'lease ending', 'renting', 'buying'
        ]
        
        for keyword in motivation_keywords:
            if keyword in text.lower():
                # Extract sentence containing the motivation
                sentences = text.split('.')
                for sentence in sentences:
                    if keyword in sentence.lower():
                        return sentence.strip()
        
        return None
    
    def _extract_pre_approval(self, text: str) -> Optional[bool]:
        """Extract pre-approval status from conversation text."""
        pre_approved_patterns = [
            r'(?:pre.?approved|pre.?qualified)',
            r'(?:already|already have).*?(?:lender|mortgage|loan)',
            r'(?:yes|yeah|yep).*?(?:pre.?approved|pre.?qualified)'
        ]
        
        not_pre_approved_patterns = [
            r'(?:not|not yet|no).*?(?:pre.?approved|pre.?qualified)',
            r'(?:need|need to).*?(?:get|find).*?(?:lender|mortgage|loan)'
        ]
        
        text_lower = text.lower()
        
        for pattern in pre_approved_patterns:
            if re.search(pattern, text_lower):
                return True
        
        for pattern in not_pre_approved_patterns:
            if re.search(pattern, text_lower):
                return False
        
        return None
    
    def _calculate_engagement_score(self, text: str) -> int:
        """Calculate engagement score based on response characteristics."""
        score = 0
        
        # Length of response (longer = more engaged)
        if len(text) > 200:
            score += 20
        elif len(text) > 100:
            score += 10
        
        # Question marks (asking questions = engaged)
        question_count = text.count('?')
        score += min(question_count * 5, 15)
        
        # Exclamation marks (enthusiasm)
        exclamation_count = text.count('!')
        score += min(exclamation_count * 3, 10)
        
        # Specific details mentioned
        detail_keywords = ['budget', 'location', 'timeline', 'bedrooms', 'bathrooms', 'must have']
        detail_count = sum(1 for keyword in detail_keywords if keyword in text.lower())
        score += min(detail_count * 5, 15)
        
        # Enthusiastic language
        enthusiastic_words = ['excited', 'love', 'perfect', 'fantastic', 'amazing', 'great']
        enthusiastic_count = sum(1 for word in enthusiastic_words if word in text.lower())
        score += min(enthusiastic_count * 3, 10)
        
        return min(score, 100)  # Cap at 100
    
    def clear_context(self) -> None:
        """Clear the current session context."""
        self.current_session_id = None
        self.current_lead_id = None
        self.pending_user_message = None
        logger.info("Cleared conversation context")
