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
        return f"{base_prompt}Generate a tweet (X post). Keep it extremely concise, impactful, and within character limits. Use relevant hashtags and consider mentioning key accounts if appropriate."
    else:
        return f"{base_prompt}Generate a social media post suitable for {platform}. Focus on key takeaways and a clear message."
