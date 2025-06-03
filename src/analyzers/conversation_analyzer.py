#!/usr/bin/env python3
"""
Conversation Analysis System for Hacker News Comments
"""

import json
import re
from collections import defaultdict, Counter
from typing import Dict, List, Optional, Any
from datetime import datetime
import os

class ConversationAnalyzer:
    """Analyzes conversation patterns and quality in comment threads."""
    
    def __init__(self, openai_api_key: Optional[str] = None):
        """Initialize the conversation analyzer."""
        self.openai_api_key = openai_api_key or os.getenv('OPENAI_API_KEY')
        
    def extract_conversations_from_content(self, content: str) -> List[Dict[str, Any]]:
        """Extract conversation-like patterns from article content."""
        conversations = []
        
        # Split content into sections that might be conversations
        sections = re.split(r'\n\s*\n', content)
        
        for i, section in enumerate(sections):
            if len(section.strip()) > 50:  # Minimum length for meaningful conversation
                # Check if section contains conversational patterns
                conversational_indicators = [
                    re.search(r'\b(says?|said|replied|responds?|commented|argues?|believes?|thinks?)\b', section, re.IGNORECASE),
                    re.search(r'["\'"].*?["\'"]', section),  # Quoted text
                    re.search(r'\b(I think|In my opinion|IMO|IMHO|Actually|However|But|Well)\b', section, re.IGNORECASE),
                    re.search(r'\b(you|your|we|our|us)\b', section, re.IGNORECASE),  # Personal pronouns
                ]
                
                if any(conversational_indicators):
                    conversations.append({
                        'id': f'conv_{i}',
                        'content': section.strip(),
                        'type': 'discussion_segment',
                        'length': len(section.strip()),
                        'conversational_score': sum(1 for x in conversational_indicators if x)
                    })
        
        return conversations
    
    def curate_conversation_experience(self, content: str) -> Dict[str, Any]:
        """Create a curated conversation experience."""
        conversations = self.extract_conversations_from_content(content)
        
        total_conversations = len(conversations)
        total_length = sum(conv['length'] for conv in conversations)
        
        return {
            'total_conversations': total_conversations,
            'total_content_length': total_length,
            'conversations': conversations,
            'engagement_metrics': {
                'high_engagement': len([c for c in conversations if c.get('conversational_score', 0) >= 3]),
                'medium_engagement': len([c for c in conversations if 1 <= c.get('conversational_score', 0) < 3]),
                'low_engagement': len([c for c in conversations if c.get('conversational_score', 0) < 1])
            },
            'ai_enhanced': False,
            'analysis_timestamp': datetime.now().isoformat(),
            'content_length': len(content)
        }
    
    def format_conversation_display(self, analysis: Dict[str, Any]) -> str:
        """Format the conversation analysis for display."""
        if not analysis:
            return "<div class='text-gray-500'>No conversation patterns detected.</div>"
        
        html = "<div class='conversation-analysis space-y-4'>"
        
        total_convs = analysis.get('total_conversations', 0)
        if total_convs > 0:
            html += f"<div class='mb-4'>"
            html += f"<h4 class='font-semibold text-gray-800 dark:text-gray-200 mb-2'>🗣️ Conversation Overview</h4>"
            html += f"<p class='text-gray-700 dark:text-gray-300 text-sm'>Found {total_convs} conversation segments"
            
            if analysis.get('total_content_length'):
                html += f" ({analysis['total_content_length']:,} characters total)"
            
            html += "</p></div>"
            
            # Show engagement metrics
            engagement = analysis.get('engagement_metrics', {})
            if engagement:
                html += "<div class='grid grid-cols-3 gap-4 text-center mb-4'>"
                html += f"<div><div class='text-lg font-bold text-green-600'>{engagement.get('high_engagement', 0)}</div><div class='text-xs text-gray-500 dark:text-gray-400'>High Engagement</div></div>"
                html += f"<div><div class='text-lg font-bold text-yellow-600'>{engagement.get('medium_engagement', 0)}</div><div class='text-xs text-gray-500 dark:text-gray-400'>Medium Engagement</div></div>"
                html += f"<div><div class='text-lg font-bold text-gray-600'>{engagement.get('low_engagement', 0)}</div><div class='text-xs text-gray-500 dark:text-gray-400'>Low Engagement</div></div>"
                html += "</div>"
                
            # Show conversation samples
            conversations = analysis.get('conversations', [])
            if conversations:
                html += "<div class='mb-4'>"
                html += "<h4 class='font-semibold text-gray-800 dark:text-gray-200 mb-2'>💬 Discussion Highlights</h4>"
                
                # Show top 3 conversations by engagement score
                top_conversations = sorted(conversations, key=lambda x: x.get('conversational_score', 0), reverse=True)[:3]
                
                for conv in top_conversations:
                    score = conv.get('conversational_score', 0)
                    color = 'bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200' if score >= 3 else 'bg-yellow-100 dark:bg-yellow-900 text-yellow-800 dark:text-yellow-200' if score >= 2 else 'bg-gray-100 dark:bg-gray-900 text-gray-800 dark:text-gray-200'
                    
                    html += f"<div class='border dark:border-gray-600 rounded-lg p-3 mb-2'>"
                    html += f"<div class='flex items-center justify-between mb-2'>"
                    html += f"<span class='px-2 py-1 {color} rounded text-xs'>Engagement: {score}/4</span>"
                    html += f"<span class='text-xs text-gray-500 dark:text-gray-400'>{conv['length']} chars</span>"
                    html += f"</div>"
                    html += f"<p class='text-gray-700 dark:text-gray-300 text-sm'>{conv['content'][:200]}{'...' if len(conv['content']) > 200 else ''}</p>"
                    html += "</div>"
                
                html += "</div>"
        else:
            html += "<div class='text-gray-500 dark:text-gray-400 text-sm'>No significant conversation patterns detected in this content.</div>"
        
        html += "</div>"
        return html
