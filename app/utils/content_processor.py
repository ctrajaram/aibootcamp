"""
Content Processing Utilities for hallucination management.
This module provides functionality to fix hallucinated content and improve factual accuracy.
"""

import os
from typing import Dict, Any, List, Tuple, Union
from openai import OpenAI
import re
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class ContentProcessor:
    """
    A class to process content by fixing hallucinations and improving factual accuracy.
    Works with HallucinationChecker to identify and fix problematic content.
    """
    
    def __init__(self, model: str = "gpt-4o"):
        """
        Initialize the ContentProcessor with necessary models.
        
        Args:
            model: The OpenAI model to use for processing (default: gpt-4o)
        """
        print("Initializing ContentProcessor...")
        
        # Initialize OpenAI client
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        
        self.client = OpenAI(api_key=openai_api_key)
        self.model = model
    
    def fix_hallucinations(self, query: str, content: str, problematic_claims, context: str = None) -> str:
        """
        Fix hallucinations in content by rewriting sections with problematic claims.
        
        Args:
            query: The original query that prompted the content
            content: The content to fix hallucinations in
            problematic_claims: Problematic claims to fix, can be a list of claims or full evaluation result
            context: Context information to use for rewriting
            
        Returns:
            The content with hallucinations fixed
        """
        if not content or not problematic_claims:
            return content
            
        # Handle case where full evaluation is passed
        if isinstance(problematic_claims, dict):
            if "problematic_claims" in problematic_claims:
                problematic_claims = problematic_claims["problematic_claims"]
            elif "hallucinated_statements" in problematic_claims:
                # Convert simple hallucinated_statements to problematic_claims format
                problematic_claims = [
                    {"text": claim, "reason": "Not supported by sources"} 
                    for claim in problematic_claims["hallucinated_statements"]
                ]
            elif "ungrounded_claims" in problematic_claims.get("grounding", {}):
                # Extract from grounding information
                problematic_claims = [
                    {"text": claim, "reason": "Not grounded in sources"} 
                    for claim in problematic_claims["grounding"]["ungrounded_claims"]
                ]
        
        # If we still have no claims after processing, return original content
        if not problematic_claims:
            print("No specific problematic claims found to fix")
            return content
            
        print("Fixing hallucinations in content...")
        
        # Identify sections to rewrite
        sections_to_rewrite = self._identify_sections_to_rewrite(content, problematic_claims)
        
        if not sections_to_rewrite:
            print("No sections identified for rewriting")
            return content
            
        # Create a deep copy of content to modify
        improved_content = content
        
        # Rewrite each section, starting from the end to preserve indices
        for section in sorted(sections_to_rewrite, key=lambda x: x["start"], reverse=True):
            section_text = section["text"]
            claims = section["claims"]
            
            # Skip if section is empty
            if not section_text.strip():
                continue
                
            # Generate improved version of this section
            improved_section = self._rewrite_section(
                content=content,
                section=section, 
                query=query, 
                context=context
            )
            
            # Replace the section in the content
            if improved_section:
                improved_content = improved_content[:section["start"]] + improved_section + improved_content[section["end"]:]
        
        return improved_content
    
    def _identify_sections_to_rewrite(self, content: str, problematic_claims: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Identify sections of content that need rewriting based on problematic claims.
        
        Args:
            content: The original content text
            problematic_claims: List of problematic claims to fix
            
        Returns:
            List of sections to rewrite, each with the section text and claims to fix
        """
        if not problematic_claims:
            return []
            
        print(f"Identifying sections to rewrite. Found {len(problematic_claims)} problematic claims.")
        
        # First, let's try to locate each claim in the content
        located_claims = []
        for claim in problematic_claims:
            claim_text = claim.get('text', '')
            
            # Skip if no text
            if not claim_text:
                continue
                
            # Try exact match first
            if claim_text in content:
                located_claims.append({
                    'index': content.find(claim_text),
                    'length': len(claim_text),
                    'claim': claim
                })
            else:
                # Try to find a fuzzy match if exact match fails
                # We'll normalize whitespace and try again
                normalized_claim = ' '.join(claim_text.split())
                normalized_content = ' '.join(content.split())
                
                if normalized_claim in normalized_content:
                    # Found normalized match, now find approximate location in original
                    idx = normalized_content.find(normalized_claim)
                    
                    # Count whitespace before the match to adjust index
                    whitespace_adjust = sum(1 for c in normalized_content[:idx] if c.isspace())
                    approximate_idx = max(0, idx - whitespace_adjust)
                    
                    located_claims.append({
                        'index': approximate_idx,
                        'length': len(normalized_claim),
                        'claim': claim
                    })
                else:
                    # Try to find a partial match by looking for key phrases
                    # Extract key phrases (5+ word sequences)
                    words = claim_text.split()
                    if len(words) >= 5:
                        for i in range(len(words) - 4):
                            phrase = ' '.join(words[i:i+5])
                            if phrase in content:
                                located_claims.append({
                                    'index': content.find(phrase),
                                    'length': len(phrase),
                                    'claim': claim
                                })
                                break
                    
                    # If we still can't find it, check for sentences containing key terms
                    if claim_text not in content:
                        # Get the key terms from the claim (nouns and key words)
                        key_terms = [word for word in words if len(word) > 4 and word.lower() not in ('these', 'those', 'their', 'there', 'about', 'after', 'before')]
                        
                        # Split content into sentences
                        import re
                        sentences = re.split(r'(?<=[.!?])\s+', content)
                        
                        for sentence in sentences:
                            # Check if multiple key terms appear in this sentence
                            term_matches = sum(1 for term in key_terms if term in sentence)
                            if term_matches >= 2 and len(sentence) > 20:  # At least 2 key terms and reasonably long sentence
                                located_claims.append({
                                    'index': content.find(sentence),
                                    'length': len(sentence),
                                    'claim': claim
                                })
                                break
                
                # If we still couldn't locate it, log a warning
                if all(claim.get('claim', {}).get('text', '') != claim_text for claim in located_claims):
                    # Check if it's a short incomplete fragment of a longer sentence
                    if len(claim_text) < 60 and claim_text.strip()[-1] not in ('.', '!', '?'):
                        print(f"Warning: Could not locate short claim in content: {claim_text[:60]}...")
                    else:
                        print(f"Warning: Could not locate claim in content: {claim_text[:60]}...")
        
        # Sort located claims by position
        located_claims.sort(key=lambda x: x['index'])
        
        # If we couldn't locate any claims, try rewriting the entire content
        if not located_claims:
            return [{
                'text': content,
                'claims': problematic_claims
            }]
        
        # Group claims into sections (paragraphs or clusters of nearby claims)
        sections = []
        current_section = None
        
        for claim_info in located_claims:
            claim_start = claim_info['index']
            claim_end = claim_start + claim_info['length']
            
            # Find paragraph boundaries - go backward to find start
            paragraph_start = content.rfind('\n\n', 0, claim_start)
            if paragraph_start == -1:
                paragraph_start = 0
            else:
                paragraph_start += 2  # Skip the newlines
                
            # Find paragraph end
            paragraph_end = content.find('\n\n', claim_end)
            if paragraph_end == -1:
                paragraph_end = len(content)
                
            # Check if this claim can be added to current section
            if current_section and claim_start < current_section['end'] + 500:  # Within reasonable distance
                current_section['end'] = max(current_section['end'], paragraph_end)
                current_section['claims'].append(claim_info['claim'])
            else:
                # Start new section
                if current_section:
                    # Add the complete text for the previous section
                    current_section['text'] = content[current_section['start']:current_section['end']]
                    sections.append(current_section)
                    
                # Create new section
                current_section = {
                    'start': paragraph_start,
                    'end': paragraph_end,
                    'claims': [claim_info['claim']]
                }
        
        # Add the last section
        if current_section:
            current_section['text'] = content[current_section['start']:current_section['end']]
            sections.append(current_section)
        
        # If the claims are scattered throughout, consider rewriting the whole document
        if len(sections) > 5 or sum(len(s['text']) for s in sections) > 0.8 * len(content):
            return [{
                'text': content,
                'claims': problematic_claims
            }]
            
        return sections
    
    def _rewrite_section(self, content: str, section: Dict[str, Any], query: str, context: str) -> str:
        """
        Rewrite a specific section to fix hallucinations.
        
        Args:
            content: The full content text
            section: The section to rewrite
            query: The original query that prompted the content
            context: The reference context with accurate information
            
        Returns:
            Rewritten section text
        """
        # Check if there are actually problematic claims to fix
        if not section["claims"]:
            print("No problematic claims identified for this section. Returning original.")
            return section["text"]
            
        print(f"Fixing {len(section['claims'])} problematic claims in section of length {len(section['text'])}")
        print(f"First few words of section: '{section['text'][:50]}...'")
        
        # Extract key facts from context that could be used for replacement
        context_facts = self._extract_key_facts_from_context(context, section["claims"])
        
        # Create a more effective rewriting prompt with stronger factuality requirements
        system_prompt = """You are an expert fact-checker and content rewriter specializing in fixing hallucinations in AI-generated text.
Your task is to rewrite the provided text section to ONLY include factual information from the context.

CRITICAL RULES:
1. REPLACE ALL inaccurate information with accurate facts from the context
2. If information can't be verified from the context, REMOVE it completely
3. DO NOT preserve claims that aren't supported by the context
4. DO NOT add qualifiers like "according to sources" - make direct factual statements
5. DO NOT invent any new information or keep any unverified claims from the original
6. Return ONLY the corrected text with NO explanation
7. Make the text flow naturally - don't just insert context facts verbatim
8. Use a similar style and tone as the original

Your goal is to produce completely factual content, even if it means significantly changing the original text.
"""
        
        # Format the problematic claims for better clarity in the prompt
        claims_display = "\n".join([f"- {claim.get('text', 'Unknown claim')}: {claim.get('reason', 'Not verified')}" for claim in section["claims"]])
        
        # Create the user prompt
        user_prompt = f"""I need you to rewrite a section of content that contains factual inaccuracies.

ORIGINAL SECTION:
{section["text"]}

SPECIFIC PROBLEMATIC CLAIMS THAT MUST BE REPLACED OR REMOVED:
{claims_display}

FACTUAL CONTEXT - USE ONLY THESE FACTS:
{context[:3000]}

Please rewrite the section to completely fix the hallucinations and make it factually accurate.
Use ONLY information from the context and REMOVE any claims not supported by the context.
Maintain a similar style and tone as the original.
Return ONLY the corrected text with no additional explanations or notes.
"""
        
        # Try multiple approaches to rewriting
        rewritten_text = None
        
        # First attempt: Standard rewriting
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,  # Lower temperature for more factual output
                max_tokens=max(1000, len(section["text"]) * 2)
            )
            
            rewritten_text = response.choices[0].message.content.strip()
            
            # Check if the rewritten text is drastically different from original
            similarity = self._content_similarity(rewritten_text, section["text"])
            if similarity < 0.4:
                print(f"Rewritten text is substantially different from original (similarity: {similarity:.2f})")
                
                # If rewritten text is very different, make sure it still includes key information
                if len(rewritten_text.split()) < 0.5 * len(section["text"].split()):
                    print("Warning: Rewritten text is much shorter than original. Adding more detail...")
                    
                    # Add a follow-up request to expand with more context
                    expansion_prompt = f"""Your rewritten text is good, but please expand it with more details from the context
to make it approximately the same length as the original. Make sure to only use factual information.

Original length: {len(section["text"].split())} words
Current rewrite: {len(rewritten_text.split())} words

Context: {context[:3000]}
"""
                    
                    expansion_response = self.client.chat.completions.create(
                        model=self.model,
                        messages=[
                            {"role": "system", "content": "You are an expert fact-checker and content writer."},
                            {"role": "user", "content": user_prompt},
                            {"role": "assistant", "content": rewritten_text},
                            {"role": "user", "content": expansion_prompt}
                        ],
                        temperature=0.2,
                        max_tokens=max(1000, len(section["text"]) * 2)
                    )
                    
                    rewritten_text = expansion_response.choices[0].message.content.strip()
            
            # Validate the rewritten content is not empty or too short
            if len(rewritten_text) > 20:
                print("Successfully rewrote content in attempt 1")
                return rewritten_text
            else:
                print("Warning: Rewritten text is too short. Trying alternative approach...")
            
        except Exception as e:
            print(f"Error in first rewrite attempt: {str(e)}")
        
        # Second attempt: More structured approach with explicit replacements
        try:
            structured_prompt = self._create_structured_rewrite_prompt(
                section_text=section["text"],
                problematic_claims=section["claims"],
                context_facts=context_facts
            )
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert fact-checker. Replace inaccurate claims with factual information."},
                    {"role": "user", "content": structured_prompt}
                ],
                temperature=0.1,
                max_tokens=max(1000, len(section["text"]) * 2)
            )
            
            rewritten_text = response.choices[0].message.content.strip()
            
            if len(rewritten_text) > 20:  # Basic validation that we got meaningful content
                print("Successfully rewrote content in attempt 2")
                return rewritten_text
            else:
                print("Warning: Second rewrite attempt produced too little content. Trying minimal fix...")
                
        except Exception as e:
            print(f"Error in second rewrite attempt: {str(e)}")
        
        # Final fallback: Minimal direct replacement approach
        try:
            minimal_fix = self._create_minimal_fix(
                section_text=section["text"],
                problematic_claims=section["claims"],
                context_facts=context_facts
            )
            
            print("Using minimal direct replacement approach")
            
            # Ensure the minimal fix is different from the original
            if minimal_fix != section["text"] and len(minimal_fix) > 20:
                return minimal_fix
            
        except Exception as e:
            print(f"Error in minimal fix attempt: {str(e)}")
        
        # If all attempts failed, add a disclaimer and return original
        print("Warning: All rewrite attempts failed. Returning input text with a disclaimer")
        
        # Add a disclaimer about the content possibly containing inaccuracies
        disclaimer = "\n\n[NOTE: This section may contain factual inaccuracies. Please verify information from reliable sources.]"
        
        # Only add the disclaimer if it's not already there
        if disclaimer not in section["text"]:
            return section["text"] + disclaimer
        else:
            return section["text"]
    
    def _extract_key_facts_from_context(self, context: str, problematic_claims: List[Dict[str, Any]]) -> Dict[int, str]:
        """
        Extract key facts from context that could replace problematic claims.
        
        Args:
            context: The reference context 
            problematic_claims: List of problematic claims
            
        Returns:
            Dictionary mapping claim index to potential replacement facts
        """
        # Use GPT to extract relevant facts for each claim
        system_prompt = """You are a factual information extractor. Your task is to find accurate information 
from the provided context that could be used to replace incorrect claims. Extract only factual 
statements that are directly supported by the context."""
        
        facts_by_claim = {}
        
        try:
            for i, claim in enumerate(problematic_claims):
                # Create a targeted extraction prompt
                user_prompt = f"""Find accurate information in the context that directly addresses this claim:
                
CLAIM: {claim['text']}

CONTEXT:
{context[:4000]}

Extract ONLY the specific facts from the context that could replace this claim.
Be concise and precise. Only include information that is explicitly stated in the context.
If no relevant information exists in the context, state "No directly relevant information found in context."
"""
                
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.0,  # Zero temperature for deterministic extraction
                    max_tokens=250  # Limit token count for efficiency
                )
                
                extracted_facts = response.choices[0].message.content.strip()
                facts_by_claim[i] = extracted_facts
                
        except Exception as e:
            print(f"Error extracting facts from context: {str(e)}")
            # Provide a reasonable fallback
            for i in range(len(problematic_claims)):
                if i not in facts_by_claim:
                    facts_by_claim[i] = "Error extracting facts from context."
        
        return facts_by_claim
    
    def _create_structured_rewrite_prompt(self, section_text: str, 
                                        problematic_claims: List[Dict[str, Any]], 
                                        context_facts: Dict[int, str]) -> str:
        """
        Create a structured prompt for rewriting by explicitly marking up the text.
        
        Args:
            section_text: Original text section
            problematic_claims: List of problematic claims
            context_facts: Dictionary of facts extracted from context
            
        Returns:
            Structured prompt for rewriting
        """
        # Mark up the text with explicit replacements
        marked_text = section_text
        
        # Sort claims by position in reverse order to avoid index shifting
        sorted_claims = sorted(
            [(i, claim) for i, claim in enumerate(problematic_claims)],
            key=lambda x: section_text.find(x[1]["text"]),
            reverse=True
        )
        
        for i, claim in sorted_claims:
            claim_text = claim["text"]
            replacement_text = f"[REPLACE WITH ACCURATE INFO: {context_facts.get(i, 'Use facts from context')}]"
            
            start_pos = section_text.find(claim_text)
            if start_pos != -1:
                marked_text = marked_text[:start_pos] + replacement_text + marked_text[start_pos + len(claim_text):]
        
        prompt = f"""I need you to fix this text that contains inaccuracies. I've marked problematic areas 
with [REPLACE WITH ACCURATE INFO: ...] tags. Replace each tagged section with accurate information 
based on the guidance provided.

MARKED TEXT:
{marked_text}

CONTEXT FROM RELIABLE SOURCES:
{section_text}

Please rewrite the entire text, replacing marked sections with accurate information while maintaining 
the original flow and style. The replacement text should blend seamlessly with surrounding content.

Return ONLY the corrected text, with NO explanations or notes.
"""
        return prompt
    
    def _validate_rewritten_content(self, rewritten_text: str, 
                                  problematic_claims: List[Dict[str, Any]], 
                                  context: str) -> bool:
        """
        Validate if the rewritten content actually fixed the hallucinations.
        
        Args:
            rewritten_text: The rewritten content
            problematic_claims: List of problematic claims
            context: The reference context
            
        Returns:
            True if the content has been successfully fixed, False otherwise
        """
        # Check if problematic claims are still present
        for claim in problematic_claims:
            claim_text = claim.get('text', '')
            if not claim_text:
                continue
                
            if claim_text in rewritten_text:
                print(f"Warning: Problematic claim still present: '{claim_text[:30]}...'")
                return False
                
        # Check overall similarity - shouldn't be identical or too different
        from difflib import SequenceMatcher
        similarity = SequenceMatcher(None, rewritten_text, context).ratio()
        
        if similarity < 0.1:
            print(f"Warning: Rewritten text has very low similarity to context: {similarity:.2f}")
            return False
            
        return True
    
    def _create_minimal_fix(self, section_text: str, 
                          problematic_claims: List[Dict[str, Any]], 
                          context_facts: Dict[int, str]) -> str:
        """
        Create a minimal fixed version by directly replacing problematic claims.
        
        Args:
            section_text: Original text section
            problematic_claims: List of problematic claims
            context_facts: Dictionary of facts extracted from context
            
        Returns:
            Minimally fixed text
        """
        current_text = section_text
        
        # Sort claims by position in reverse order to avoid index shifting
        sorted_claims = sorted(
            [(i, claim) for i, claim in enumerate(problematic_claims)],
            key=lambda x: section_text.find(x[1]["text"]),
            reverse=True
        )
        
        for i, claim in sorted_claims:
            claim_text = claim["text"]
            replacement_fact = context_facts.get(i, "")
            
            # Create a simple replacement
            if replacement_fact and "No directly relevant information" not in replacement_fact:
                # Use the extracted fact as replacement
                replacement = replacement_fact
            else:
                # Create a hedged version of the original claim
                replacement = f"Some sources suggest that {claim_text.lower()}, though this information could not be fully verified."
            
            # Find and replace the claim
            start_pos = current_text.find(claim_text)
            if start_pos != -1:
                current_text = current_text[:start_pos] + replacement + current_text[start_pos + len(claim_text):]
        
        return current_text
    
    def _rewrite_full_content(self, query: str, content: str, context: str) -> str:
        """
        Rewrite the entire content to improve factual accuracy.
        
        Args:
            query: Original query that prompted the content
            content: The original content with potential hallucinations
            context: The original context/sources used to generate the content
            
        Returns:
            Rewritten content
        """
        # Create a prompt for rewriting the entire content
        system_prompt = """You are an expert content corrector specialized in fixing factual inaccuracies 
while preserving the original text's style, tone, and flow. Your primary goal is to REPLACE 
hallucinated information with FACTUAL information from the provided sources.

FOLLOW THESE RULES STRICTLY:
1. DO NOT simply remove claims that aren't supported - replace them with accurate information
2. DO NOT change content that is already accurate
3. DO NOT add disclaimers like "according to sources" - make direct factual statements
4. MATCH the style, tone, and technical level of the original content
5. PRESERVE the structure (paragraphs, sentences) of the original where possible
6. ONLY use information from the provided context and sources
7. BE SPECIFIC - use dates, names, and technical details from the sources when available
8. NEVER invent information even if the context seems incomplete"""
        
        user_prompt = f"""I need you to rewrite this text to improve factual accuracy. 
Use the provided context to replace any inaccurate information.

==== ORIGINAL TEXT ====
{content}

==== CONTEXT FROM RELIABLE SOURCES ====
{context[:4000]}

YOUR TASK:
1. Rewrite the original text to replace any inaccurate information with accurate information
2. Maintain the same style, structure, and technical depth of the original
3. Only use facts that are directly supported by the context
4. DO NOT add hedging language or qualifiers unless they appear in the source
5. Ensure your revised text flows naturally and reads coherently

IMPORTANT: Return ONLY the corrected text without any prefixes, explanations, or markdown formatting.
"""
        
        # Try to rewrite with multiple attempts using different techniques
        temp = 0.3  # Start with low temperature for precision
        max_tokens = max(len(content) * 2, 1000)  # Allow expansion but with reasonable limits
        
        for attempt in range(2):
            try:
                # For first attempt, use standard completion
                if attempt == 0:
                    response = self.client.chat.completions.create(
                        model=self.model,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        temperature=temp,
                        max_tokens=max_tokens
                    )
                    
                elif attempt == 1:
                    # Second attempt: more structured approach
                    structured_prompt = user_prompt + "\n\nPlease be extra careful to fact-check and replace any hallucinated information."
                    response = self.client.chat.completions.create(
                        model=self.model,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": structured_prompt}
                        ],
                        temperature=0.1,  # Lower temperature for more precision
                        max_tokens=max_tokens
                    )
                    
                rewritten_text = response.choices[0].message.content.strip()
                
                # Simple validation: make sure we got something back that's reasonable
                if len(rewritten_text) < len(content) * 0.3:
                    print(f"Warning: Rewritten text suspiciously short: {len(rewritten_text)} chars")
                    temp += 0.2  # Increase temperature for next attempt
                    continue
                
                if len(rewritten_text) > len(content) * 4:
                    print(f"Warning: Rewritten text suspiciously long: {len(rewritten_text)} chars")
                    temp -= 0.1  # Decrease temperature for next attempt
                    continue
                
                return rewritten_text
                
            except Exception as e:
                print(f"Error rewriting full content (attempt {attempt+1}): {str(e)}")
                temp += 0.1  # Adjust temperature for next attempt
        
        # If all fails, return the original content
        print("All attempts to rewrite the full content failed. Returning original.")
        return content
    
    def _content_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate a simple similarity score between two texts.
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            Float between 0-1 representing similarity (1 = identical)
        """
        # Convert to lowercase and tokenize simply by splitting on whitespace
        tokens1 = set(text1.lower().split())
        tokens2 = set(text2.lower().split())
        
        # Calculate Jaccard similarity (intersection over union)
        if not tokens1 or not tokens2:
            return 0.0
            
        intersection = len(tokens1.intersection(tokens2))
        union = len(tokens1.union(tokens2))
        
        return intersection / union if union > 0 else 0.0
