def get_topic_identification_prompt(transcript: str, min_topics: int = 3, max_topics: int = 10,
                                   include_timestamps: bool = True, timestamped_segments=None) -> str:
    """Generate prompt for identifying viral topics from transcription."""
    
    base_prompt = f"""
You are an expert content strategist specializing in viral content creation. Analyze the following transcript and identify the most viral-worthy topics that would perform well on social media platforms.

TRANSCRIPT:
{transcript}

"""
    
    if include_timestamps and timestamped_segments:
        base_prompt += "\nTIMESTAMPED SEGMENTS:\n"
        for segment in timestamped_segments[:20]:  # Limit to first 20 segments
            base_prompt += f"[{segment['start_time']} - {segment['end_time']}] {segment['text'][:100]}...\n"
    
    return base_prompt + f"""
INSTRUCTIONS:
1. Identify {min_topics}-{max_topics} viral-worthy topics from this content
2. For each topic, provide:
   - Topic title (5-8 words)
   - Brief description (1-2 sentences)
   - Viral potential score (0.0-1.0)
   - Target audience
   - Content category (educational, entertainment, motivational, controversial, etc.)
   - Key hook/angle for social media
   {'- Timestamp ranges where this topic appears' if include_timestamps else ''}

3. Focus on topics that are:
   - Relatable and shareable
   - Emotionally engaging
   - Actionable or thought-provoking
   - Trending or timely
   - Have strong hook potential

OUTPUT FORMAT (JSON):
{{
  "topics": [
    {{
      "topic": "Topic Title",
      "description": "Brief description of the topic",
      "confidence": 0.85,
      "viral_potential": 0.9,
      "category": "educational",
      "target_audience": "professionals",
      "hook_angle": "Main hook for social media",
      {'"timestamp_ranges": [{{"start": "00:01:30", "end": "00:03:45"}}],' if include_timestamps else ''}
      "hashtags": ["#relevant", "#hashtags"]
    }}
  ],
  "summary": "Overall content theme and viral potential"
}}

Analyze and extract the topics:
"""


def get_x_thread_prompt(transcript: str, max_posts: int = 8, character_limit: int = 280,
                        thread_style: str = "viral", include_timestamps: bool = True,
                        timestamped_segments=None, topic_focus: str = None) -> str:
    """Generate prompt for creating X/Twitter threads from transcription."""
    
    style_instructions = {
        "viral": "engaging hooks, controversial takes, and shareable insights",
        "educational": "clear explanations, actionable tips, and learning points",
        "storytelling": "narrative flow, personal anecdotes, and emotional connection",
        "professional": "industry insights, thought leadership, and expertise",
        "conversational": "casual tone, questions, and community engagement"
    }
    
    base_prompt = f"""
You are a viral content creator specializing in X (Twitter) threads. Create a compelling {max_posts}-post thread from the following transcript.

TRANSCRIPT:
{transcript}

"""
    
    if include_timestamps and timestamped_segments:
        base_prompt += "\nTIMESTAMPED SEGMENTS:\n"
        for segment in timestamped_segments[:15]:  # Limit for context
            base_prompt += f"[{segment['start_time']} - {segment['end_time']}] {segment['text'][:150]}...\n"
    
    focus_instruction = f"\nFOCUS TOPIC: {topic_focus}\n" if topic_focus else ""
    
    return base_prompt + focus_instruction + f"""
THREAD REQUIREMENTS:
1. Create exactly {max_posts} posts maximum
2. Each post must be under {character_limit} characters
3. Style: {thread_style} - focus on {style_instructions.get(thread_style, 'engaging content')}
4. First post must be a strong hook that stops scrolling
5. Include strategic thread numbering (1/n format)
6. End with a strong call-to-action or question
7. Use relevant emojis and hashtags strategically
8. Maintain narrative flow between posts

THREAD STRUCTURE:
- Post 1: Hook + preview of value
- Posts 2-{max_posts-1}: Main content with key insights
- Post {max_posts}: Conclusion + CTA

{'TIMESTAMP MAPPING: Include timestamp references for each post showing where the content comes from in the video.' if include_timestamps else ''}

OUTPUT FORMAT (JSON):
{{
  "thread": [
    {{
      "post_number": 1,
      "content": "1/{max_posts} Thread content here...",
      "character_count": 95,
      {'"start_time": "00:01:30",' if include_timestamps else ''}
      {'"end_time": "00:02:15",' if include_timestamps else ''}
      "engagement_elements": ["hook", "emoji", "hashtag"]
    }}
  ],
  "thread_summary": "Brief description of thread focus",
  "viral_elements": ["List of viral elements used"],
  "target_metrics": {{
    "expected_engagement": "high/medium/low",
    "shareability_score": 0.8
  }}
}}

Create the thread:
"""


def get_content_analysis_prompt(transcript: str, analysis_type: str = "comprehensive") -> str:
    """Generate prompt for comprehensive content analysis."""
    
    analysis_types = {
        "comprehensive": "topics, sentiment, viral potential, key moments, and audience insights",
        "viral_assessment": "viral potential, shareability factors, and engagement predictions",
        "audience_analysis": "target demographics, interests, and content preferences",
        "key_moments": "highlight clips, quotable moments, and peak engagement points"
    }
    
    return f"""
You are a content analysis expert. Perform a {analysis_type} analysis of the following transcript.

TRANSCRIPT:
{transcript}

ANALYSIS FOCUS: {analysis_types.get(analysis_type, 'general content analysis')}

PROVIDE:
1. Content Summary (2-3 sentences)
2. Key Topics (3-5 main themes)
3. Sentiment Analysis (overall tone and emotional elements)
4. Viral Potential Assessment (0.0-1.0 score with reasoning)
5. Target Audience Profile
6. Recommended Content Formats (threads, posts, stories, etc.)
7. Engagement Optimization Suggestions
8. Hashtag Recommendations
9. Best Practices Alignment
10. Content Calendar Suggestions

OUTPUT FORMAT (JSON):
{{
  "summary": "Content overview",
  "topics": ["topic1", "topic2", "topic3"],
  "sentiment": {{
    "overall_tone": "positive/neutral/negative",
    "emotional_elements": ["humor", "inspiration", "education"],
    "confidence": 0.85
  }},
  "viral_assessment": {{
    "score": 0.75,
    "factors": ["relatability", "shareability", "timing"],
    "potential_reach": "high/medium/low"
  }},
  "audience_profile": {{
    "primary_demographic": "professionals",
    "interests": ["interest1", "interest2"],
    "platforms": ["platform preferences"]
  }},
  "recommendations": {{
    "formats": ["twitter_thread", "linkedin_post"],
    "timing": "optimal posting times",
    "hashtags": ["#recommended", "#hashtags"],
    "engagement_tactics": ["questions", "polls", "controversy"]
  }}
}}

Perform the analysis:
"""


def get_social_media_prompt(platform: str, transcript: str, **kwargs) -> str:
    """
    Generates a social media content generation prompt based on the platform.
    """
    base_prompt = f"Generate content for {platform} based on the following transcript:\n\nTRANSCRIPT: {transcript}\n\n"

    if platform.lower() == "linkedin":
        # Parameters from the cloned repo's prompts.py
        number_of_posts = kwargs.get("number_of_posts", 1)
        tone = kwargs.get("tone", "professional")
        style = kwargs.get("style", "Story-based")
        length = kwargs.get("length", "short")
        hook_type = kwargs.get("hook_type", "Question")
        cta_type = kwargs.get("cta_type", "Soft CTA")
        emoji_preference = kwargs.get("emoji_preference", "None")
        spacing = kwargs.get("spacing", "Regular")
        formatting = kwargs.get("formatting", "Plain")
        hashtag_preference = kwargs.get("hashtag_preference", "None")
        industry = kwargs.get("industry", "General")
        target_audience = kwargs.get("target_audience", "Professionals")
        brand_voice = kwargs.get("brand_voice", "Authoritative")
        creator_style = kwargs.get("creator_style", "None")
        focus = kwargs.get("focus", "Educational")
        experience = kwargs.get("experience", "Beginner")
        perspective = kwargs.get("perspective", "First-hand experience")
        cultural_context = kwargs.get("cultural_context", "Global")
        angle = kwargs.get("angle", "Success story")

        return f"""
        You are a professional content creator specializing in LinkedIn posts. Create {number_of_posts} LinkedIn post(s) based on the following inputs and parameters:
        SOURCE CONTENT:

        YouTube Video Transcript: {transcript}

        STYLE PARAMETERS:

        Tone: {tone} [Options: Professional, Casual, Gen-Z, Motivational, Educational, Technical]
        Writing Style: {style} [Options: Story-based, Data-driven, Question-based, List format, Problem-solution]
        Post Length: {length} [Options: Short (< 800 chars), Medium (800-1500 chars), Long (1500-3000 chars)]
        Hook Style: {hook_type} [Options: Question, Statistic, Bold Statement, Personal Story, Contrarian View]
        Call-to-Action Type: {cta_type} [Options: Soft CTA, Strong CTA, Question-based CTA, None]

        FORMATTING PREFERENCES:

        Emoji Usage: {emoji_preference} [Options: None, Minimal (1-2), Moderate (3-5), Heavy (6+)]
        Line Spacing: {spacing} [Options: Compact, Regular, Airy]
        Text Formatting: {formatting} [Options: Plain, With Bold Points, With Bullet Points]
        Hashtag Usage: {hashtag_preference} [Options: None, Minimal (1-3), Moderate (4-6), Heavy (7+)]

        BRANDING ELEMENTS:

        Industry: {industry}
        Target Audience: {target_audience}
        Brand Voice: {brand_voice} [Options: Authoritative, Friendly, Innovative, Traditional]
        Creator Inspiration: {creator_style}
        Key Message Focus: {focus} [Options: Educational, Inspirational, Problem-solving, Thought Leadership]

        PERSONALIZATION:

        Personal Experience Level: {experience} [Options: Beginner, Intermediate, Expert]
        Unique Perspective: {perspective} [Options: First-hand experience, Research-based, Opinion, Case study]
        Cultural Context: {cultural_context} [Options: Global, Region-specific, Industry-specific]
        Content Angle: {angle} [Options: Success story, Learning experience, Industry insight, Trend analysis]

        Create {number_of_posts} unique LinkedIn posts that are:

        Engaging and scroll-stopping
        Relevant to the source content
        Formatted according to the specified preferences
        Aligned with the chosen creator's style while maintaining authenticity
        Optimized for LinkedIn's algorithm

        Format each post as:
        Post 1:
        [Post content]
        Post 2:
        [Post content]
        Post 3:
        [Post content]
        """
    elif platform.lower() == "facebook":
        return f"{base_prompt}Generate a Facebook post. Keep it conversational and engaging, suitable for a broad audience. Include a clear call to action if applicable. Consider using emojis naturally."
    elif platform.lower() == "instagram":
        return f"{base_prompt}Generate an Instagram caption. Keep it concise and visually appealing. Use relevant hashtags and consider including emojis. The tone should be engaging and direct."
    elif platform.lower() == "x": # Formerly Twitter
        # Enhanced X/Twitter generation with thread support
        is_thread = kwargs.get("is_thread", False)
        max_posts = kwargs.get("max_posts", 1)
        character_limit = kwargs.get("character_limit", 280)
        thread_style = kwargs.get("thread_style", "viral")
        
        if is_thread and max_posts > 1:
            return get_x_thread_prompt(
                transcript, 
                max_posts=max_posts,
                character_limit=character_limit,
                thread_style=thread_style,
                include_timestamps=kwargs.get("include_timestamps", False),
                topic_focus=kwargs.get("topic_focus")
            )
        else:
            return f"{base_prompt}Generate a tweet (X post). Keep it extremely concise, impactful, and within {character_limit} characters. Use relevant hashtags and consider mentioning key accounts if appropriate. Focus on the most engaging hook from the content."
    else:
        return f"{base_prompt}Generate a social media post suitable for {platform}. Focus on key takeaways and a clear message. Consider platform-specific best practices for engagement and reach."
