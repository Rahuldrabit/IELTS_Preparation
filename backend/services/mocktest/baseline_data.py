"""
Pre-built baseline mock test data for consistent first-time assessment.
Progressive difficulty: each section escalates from easy to hard.
"""

# ═══════════════════════════════════════════════════════════════════════════════
# SECTION TIMING (seconds) — Real IELTS timing
# ═══════════════════════════════════════════════════════════════════════════════

SECTION_TIMING = {
    "listening": 30 * 60,   # 30 minutes
    "reading": 60 * 60,     # 60 minutes
    "writing": 60 * 60,     # 60 minutes
    "speaking": 15 * 60,    # 15 minutes
}

SECTION_ORDER = {
    "listening": 1,
    "reading": 2,
    "writing": 3,
    "speaking": 4,
}

# ═══════════════════════════════════════════════════════════════════════════════
# DIFFICULTY CONFIGS — Progressive scaling per sub-section
# ═══════════════════════════════════════════════════════════════════════════════

LISTENING_DIFFICULTY = [
    {
        "section_number": 1,
        "difficulty": "easy",
        "vocabulary_level": "basic",
        "grammar_complexity": "simple",
        "context": "daily conversation between two people",
        "accent": "british",
        "speech_rate": "slow",
        "question_count": 10,
        "question_types": ["FILL_BLANK", "MULTIPLE_CHOICE"],
    },
    {
        "section_number": 2,
        "difficulty": "medium",
        "vocabulary_level": "medium",
        "grammar_complexity": "medium",
        "context": "monologue in everyday social situation",
        "accent": "british",
        "speech_rate": "normal",
        "question_count": 10,
        "question_types": ["MULTIPLE_CHOICE", "MATCHING"],
    },
    {
        "section_number": 3,
        "difficulty": "hard",
        "vocabulary_level": "academic",
        "grammar_complexity": "complex",
        "context": "discussion between students/academics",
        "accent": "australian",
        "speech_rate": "normal",
        "question_count": 10,
        "question_types": ["SENTENCE_COMPLETION", "MULTIPLE_CHOICE"],
    },
    {
        "section_number": 4,
        "difficulty": "very_hard",
        "vocabulary_level": "c1",
        "grammar_complexity": "complex",
        "context": "academic lecture on specialized topic",
        "accent": "british",
        "speech_rate": "fast",
        "question_count": 10,
        "question_types": ["SUMMARY_COMPLETION", "SENTENCE_COMPLETION"],
    },
]

READING_DIFFICULTY = [
    {
        "passage_number": 1,
        "difficulty": "easy",
        "vocabulary_level": "basic",
        "grammar_complexity": "simple",
        "topic": "daily life",
        "passage_length_words": 600,
        "question_count": 13,
        "question_types": ["TRUE_FALSE_NOT_GIVEN", "MULTIPLE_CHOICE"],
    },
    {
        "passage_number": 2,
        "difficulty": "medium",
        "vocabulary_level": "academic",
        "grammar_complexity": "medium",
        "topic": "science",
        "passage_length_words": 800,
        "question_count": 13,
        "question_types": ["MATCHING_HEADINGS", "SENTENCE_COMPLETION"],
    },
    {
        "passage_number": 3,
        "difficulty": "hard",
        "vocabulary_level": "c1",
        "grammar_complexity": "complex",
        "topic": "philosophy",
        "passage_length_words": 1000,
        "question_count": 14,
        "question_types": ["TRUE_FALSE_NOT_GIVEN", "SUMMARY_COMPLETION", "MULTIPLE_CHOICE"],
    },
]

WRITING_DIFFICULTY = [
    {
        "task_number": 1,
        "task_type": "task_1",
        "difficulty": "medium",
        "min_words": 150,
        "suggested_time_minutes": 20,
        "description": "Describe data from a chart or graph",
    },
    {
        "task_number": 2,
        "task_type": "task_2",
        "difficulty": "hard",
        "min_words": 250,
        "suggested_time_minutes": 40,
        "description": "Write an argumentative essay",
    },
]

SPEAKING_DIFFICULTY = [
    {
        "part_number": 1,
        "difficulty": "easy",
        "duration_minutes": 4,
        "description": "Introduction and general questions",
        "question_count": 5,
    },
    {
        "part_number": 2,
        "difficulty": "medium",
        "duration_minutes": 4,
        "description": "Individual long turn (cue card)",
        "prep_time_seconds": 60,
        "speaking_time_seconds": 120,
    },
    {
        "part_number": 3,
        "difficulty": "hard",
        "duration_minutes": 5,
        "description": "Two-way discussion on abstract topics",
        "question_count": 4,
    },
]


# ═══════════════════════════════════════════════════════════════════════════════
# BASELINE TEST CONTENT — Pre-built for consistent assessment
# ═══════════════════════════════════════════════════════════════════════════════

BASELINE_LISTENING_CONTENT = [
    {
        "section_number": 1,
        "title": "Booking a Hotel Room",
        "transcript": (
            "Receptionist: Good morning, Riverside Hotel. How can I help you?\n"
            "Caller: Hi, I'd like to book a room for next weekend, please.\n"
            "Receptionist: Certainly. That would be for Friday and Saturday nights?\n"
            "Caller: Yes, two nights. Do you have a double room available?\n"
            "Receptionist: Let me check. Yes, we have a double room on the third floor "
            "with a view of the garden. It's ninety-five pounds per night.\n"
            "Caller: That sounds lovely. Does it include breakfast?\n"
            "Receptionist: Yes, a full English breakfast is included. We also have "
            "a swimming pool and gym that guests can use free of charge.\n"
            "Caller: Perfect. My name is Sarah Mitchell, that's M-I-T-C-H-E-L-L.\n"
            "Receptionist: Thank you, Ms Mitchell. Could I have a contact number?\n"
            "Caller: Yes, it's oh-seven-seven-oh, five-five-three, eight-nine-two.\n"
            "Receptionist: And will you be paying by credit card?\n"
            "Caller: Yes, Visa. The number is four-seven-two-one, "
            "three-eight-six-five, nine-zero-one-two, four-four-seven-eight.\n"
            "Receptionist: Wonderful. Your booking reference is HB-three-four-seven. "
            "Check-in is from two p.m. on Friday.\n"
            "Caller: Thank you very much. Goodbye.\n"
            "Receptionist: Goodbye, have a nice day."
        ),
        "questions": [
            {"id": 1, "text": "The hotel room is on the ___ floor.", "type": "FILL_BLANK",
             "correct_answer": "third", "options": None},
            {"id": 2, "text": "The room costs ___ pounds per night.", "type": "FILL_BLANK",
             "correct_answer": "95", "options": None},
            {"id": 3, "text": "Breakfast is included in the room price.", "type": "MULTIPLE_CHOICE",
             "correct_answer": "A", "options": ["A. True", "B. False", "C. Not stated"]},
            {"id": 4, "text": "The caller's surname is spelled:", "type": "MULTIPLE_CHOICE",
             "correct_answer": "B", "options": ["A. MICHAEL", "B. MITCHELL", "C. MITCHEL"]},
            {"id": 5, "text": "The caller's phone number is ___.", "type": "FILL_BLANK",
             "correct_answer": "07705538892", "options": None},
        ],
    },
    {
        "section_number": 2,
        "title": "Library Orientation Tour",
        "transcript": (
            "Welcome to the Central City Library. I'm going to give you a brief overview "
            "of our facilities and services. The library is spread over four floors. "
            "On the ground floor, you'll find the reception desk and the main collection "
            "of fiction books. We have over fifty thousand titles in this section alone.\n\n"
            "The first floor is dedicated to non-fiction, including science, history, "
            "and technology. You'll also find our study rooms here — we have twelve "
            "individual study rooms that can be booked for up to three hours at a time.\n\n"
            "The second floor houses our digital media section, with computers available "
            "for public use. We have thirty-two workstations. You'll need your library "
            "card to log in. Printing costs ten pence per page for black and white, "
            "and twenty-five pence for colour.\n\n"
            "Finally, the third floor is our quiet reading area and periodicals section. "
            "We subscribe to over two hundred magazines and journals. Please note that "
            "mobile phones must be switched off on this floor.\n\n"
            "The library is open Monday to Friday from eight a.m. to nine p.m., "
            "Saturdays from nine to six, and Sundays from ten to four. "
            "Membership is free for all city residents."
        ),
        "questions": [
            {"id": 6, "text": "How many fiction titles does the library have?", "type": "MULTIPLE_CHOICE",
             "correct_answer": "C", "options": ["A. 15,000", "B. 5,000", "C. 50,000", "D. 500,000"]},
            {"id": 7, "text": "Study rooms can be booked for up to ___ hours.", "type": "FILL_BLANK",
             "correct_answer": "3", "options": None},
            {"id": 8, "text": "The number of computer workstations is ___.", "type": "FILL_BLANK",
             "correct_answer": "32", "options": None},
            {"id": 9, "text": "Colour printing costs ___ pence per page.", "type": "FILL_BLANK",
             "correct_answer": "25", "options": None},
            {"id": 10, "text": "On Sundays, the library closes at:", "type": "MULTIPLE_CHOICE",
             "correct_answer": "B", "options": ["A. 6 p.m.", "B. 4 p.m.", "C. 9 p.m.", "D. 5 p.m."]},
        ],
    },
]

BASELINE_LISTENING_CONTENT_PART2 = [
    {
        "section_number": 3,
        "title": "University Research Project Discussion",
        "transcript": (
            "Tutor: So, how is your research project coming along?\n"
            "Student A: Well, we've completed the literature review and we're now "
            "designing the methodology. We decided to use a mixed-methods approach.\n"
            "Tutor: That's quite ambitious. What made you choose that?\n"
            "Student B: We felt that quantitative data alone wouldn't capture the "
            "complexity of the issue. We want to combine survey data with in-depth "
            "interviews to get a more nuanced understanding.\n"
            "Tutor: How many participants are you planning to recruit?\n"
            "Student A: For the survey, we're aiming for two hundred respondents. "
            "For the interviews, we'll select fifteen participants based on their "
            "survey responses — specifically those who showed unusual patterns.\n"
            "Tutor: And what about ethical approval?\n"
            "Student B: We submitted the application last week. The committee meets "
            "on the fourteenth of March, so we should hear back by the end of that week.\n"
            "Student A: In the meantime, we're piloting the survey instrument with "
            "a small group of twenty volunteers from the psychology department.\n"
            "Tutor: Good. One concern I have is your timeline. The submission deadline "
            "is June the fifteenth. Are you confident you can collect and analyse all "
            "the data by then?\n"
            "Student B: We've built in a two-week buffer for unexpected delays. "
            "If we start data collection by early April, we should have eight weeks "
            "for analysis and writing up."
        ),
        "questions": [
            {"id": 11, "text": "The research methodology is:", "type": "MULTIPLE_CHOICE",
             "correct_answer": "C",
             "options": ["A. Purely quantitative", "B. Purely qualitative",
                        "C. Mixed methods", "D. Case study"]},
            {"id": 12, "text": "The target number of survey respondents is ___.",
             "type": "FILL_BLANK", "correct_answer": "200", "options": None},
            {"id": 13, "text": "How many interview participants will be selected?",
             "type": "FILL_BLANK", "correct_answer": "15", "options": None},
            {"id": 14, "text": "The ethics committee meets on:", "type": "MULTIPLE_CHOICE",
             "correct_answer": "B",
             "options": ["A. March 4th", "B. March 14th", "C. April 14th", "D. March 24th"]},
            {"id": 15, "text": "The pilot group consists of ___ volunteers.",
             "type": "FILL_BLANK", "correct_answer": "20", "options": None},
        ],
    },
    {
        "section_number": 4,
        "title": "Lecture: The Neuroscience of Decision-Making",
        "transcript": (
            "Today I want to discuss recent advances in our understanding of how the "
            "brain makes decisions, particularly in situations involving uncertainty. "
            "Traditional economic models assumed that humans are rational agents who "
            "consistently maximize utility. However, the pioneering work of Kahneman "
            "and Tversky in the nineteen-seventies demonstrated systematic biases in "
            "human judgment.\n\n"
            "Neuroimaging studies have since revealed that decision-making involves "
            "a complex interplay between the prefrontal cortex, which handles "
            "deliberate reasoning, and the limbic system, particularly the amygdala, "
            "which processes emotional responses. What's fascinating is that these "
            "two systems often conflict.\n\n"
            "In a landmark study published in two thousand and five, researchers at "
            "Princeton used functional MRI to observe brain activity while subjects "
            "made choices involving immediate versus delayed rewards. They found that "
            "immediate rewards activated the limbic system disproportionately, while "
            "delayed rewards engaged the prefrontal cortex more strongly.\n\n"
            "This has profound implications for understanding phenomena like addiction, "
            "where the limbic system's preference for immediate gratification overwhelms "
            "the prefrontal cortex's capacity for long-term planning. Recent therapeutic "
            "approaches, including cognitive behavioural therapy and mindfulness-based "
            "interventions, essentially aim to strengthen prefrontal control over "
            "limbic impulses.\n\n"
            "The implications extend beyond clinical settings. Marketing, public policy, "
            "and even architectural design increasingly incorporate insights from "
            "behavioural neuroscience to nudge decisions in particular directions."
        ),
        "questions": [
            {"id": 16, "text": "Traditional economic models assumed humans are ___ agents.",
             "type": "FILL_BLANK", "correct_answer": "rational", "options": None},
            {"id": 17, "text": "Kahneman and Tversky's work began in the:",
             "type": "MULTIPLE_CHOICE", "correct_answer": "A",
             "options": ["A. 1970s", "B. 1980s", "C. 1990s", "D. 2000s"]},
            {"id": 18, "text": "The ___ handles deliberate reasoning in decision-making.",
             "type": "FILL_BLANK", "correct_answer": "prefrontal cortex", "options": None},
            {"id": 19, "text": "The Princeton study was published in ___.",
             "type": "FILL_BLANK", "correct_answer": "2005", "options": None},
            {"id": 20, "text": "Immediate rewards disproportionately activate the:",
             "type": "MULTIPLE_CHOICE", "correct_answer": "B",
             "options": ["A. Prefrontal cortex", "B. Limbic system",
                        "C. Cerebellum", "D. Hippocampus"]},
        ],
    },
]


# ═══════════════════════════════════════════════════════════════════════════════
# BASELINE READING CONTENT
# ═══════════════════════════════════════════════════════════════════════════════

BASELINE_READING_CONTENT = [
    {
        "passage_number": 1,
        "title": "The Growth of Urban Cycling",
        "difficulty": "easy",
        "content": (
            "A. Over the past decade, cycling has experienced a remarkable resurgence "
            "in cities around the world. What was once seen primarily as a recreational "
            "activity has become a serious mode of urban transportation. Cities from "
            "Copenhagen to Bogota have invested heavily in cycling infrastructure.\n\n"
            "B. The benefits of urban cycling are well-documented. Cyclists enjoy "
            "improved cardiovascular health, reduced stress levels, and significant "
            "cost savings compared to car ownership. A typical urban cyclist saves "
            "approximately three thousand dollars annually on transport costs.\n\n"
            "C. City governments have responded to growing demand by creating dedicated "
            "bike lanes, bike-sharing programmes, and secure parking facilities. "
            "London's cycle hire scheme, launched in 2010, now has over eleven thousand "
            "bikes available across seven hundred and fifty docking stations.\n\n"
            "D. However, safety remains a significant concern. Studies show that the "
            "perceived danger of cycling, rather than actual risk, is the primary "
            "barrier preventing more people from choosing bicycles. Separated bike "
            "lanes reduce cyclist injuries by up to seventy-five percent.\n\n"
            "E. Environmental benefits are equally compelling. A shift from car to "
            "bicycle for short urban trips could reduce transport-related carbon "
            "emissions by up to eleven percent in major cities. This makes cycling "
            "infrastructure one of the most cost-effective climate interventions."
        ),
        "word_count": 620,
        "questions": [
            {"id": 1, "text": "Cycling is now considered a serious form of urban transport.",
             "type": "TRUE_FALSE_NOT_GIVEN", "correct_answer": "True",
             "options": ["True", "False", "Not Given"]},
            {"id": 2, "text": "Cycling was always popular as a transport option in cities.",
             "type": "TRUE_FALSE_NOT_GIVEN", "correct_answer": "False",
             "options": ["True", "False", "Not Given"]},
            {"id": 3, "text": "Urban cyclists save approximately three thousand dollars per year.",
             "type": "TRUE_FALSE_NOT_GIVEN", "correct_answer": "True",
             "options": ["True", "False", "Not Given"]},
            {"id": 4, "text": "London's bike-sharing scheme is the largest in Europe.",
             "type": "TRUE_FALSE_NOT_GIVEN", "correct_answer": "Not Given",
             "options": ["True", "False", "Not Given"]},
            {"id": 5, "text": "The main barrier to cycling is:", "type": "MULTIPLE_CHOICE",
             "correct_answer": "B",
             "options": ["A. Actual danger", "B. Perceived danger",
                        "C. Cost of bicycles", "D. Lack of fitness"]},
            {"id": 6, "text": "Separated bike lanes reduce injuries by up to ___ percent.",
             "type": "FILL_BLANK", "correct_answer": "75", "options": None},
        ],
    },
]

BASELINE_READING_CONTENT_PART2 = [
    {
        "passage_number": 2,
        "title": "The Science of Sleep Architecture",
        "difficulty": "medium",
        "content": (
            "A. Sleep is far from a uniform state of unconsciousness. Research over "
            "the past fifty years has revealed that sleep consists of distinct stages "
            "that cycle throughout the night in a predictable pattern known as sleep "
            "architecture. Understanding this architecture is crucial for addressing "
            "the growing epidemic of sleep disorders.\n\n"
            "B. A typical sleep cycle lasts approximately ninety minutes and consists "
            "of four stages. The first two stages comprise light sleep, during which "
            "the body temperature drops and heart rate slows. Stage three represents "
            "deep sleep, characterised by slow delta waves in the brain. This stage "
            "is essential for physical restoration and immune function.\n\n"
            "C. The fourth stage is REM (Rapid Eye Movement) sleep, during which most "
            "dreaming occurs. The brain becomes highly active — almost as active as "
            "during waking hours — while the body experiences temporary muscle "
            "paralysis. REM sleep plays a critical role in memory consolidation "
            "and emotional processing.\n\n"
            "D. The proportion of time spent in each stage changes across the night. "
            "Early cycles contain more deep sleep, while later cycles have longer "
            "REM periods. This is why waking early can leave you feeling physically "
            "rested but mentally foggy — you've had your deep sleep but missed "
            "crucial later REM periods.\n\n"
            "E. Disruptions to sleep architecture have been linked to cognitive "
            "decline, metabolic disorders, and cardiovascular disease. Chronic sleep "
            "restriction doesn't just reduce total sleep time; it preferentially "
            "eliminates REM sleep and deep sleep, the most restorative stages.\n\n"
            "F. Modern sleep medicine increasingly focuses on sleep quality rather "
            "than mere duration. Technologies such as actigraphy and home-based "
            "EEG devices now allow clinicians to assess sleep architecture outside "
            "the laboratory, making personalised sleep interventions more accessible."
        ),
        "word_count": 810,
        "questions": [
            {"id": 7, "text": "Which paragraph describes the stages of a sleep cycle?",
             "type": "MATCHING_HEADINGS", "correct_answer": "B",
             "options": ["A", "B", "C", "D", "E", "F"]},
            {"id": 8, "text": "Which paragraph discusses the clinical implications of poor sleep?",
             "type": "MATCHING_HEADINGS", "correct_answer": "E",
             "options": ["A", "B", "C", "D", "E", "F"]},
            {"id": 9, "text": "A typical sleep cycle lasts about ___ minutes.",
             "type": "FILL_BLANK", "correct_answer": "90", "options": None},
            {"id": 10, "text": "During REM sleep, the body experiences temporary muscle ___.",
             "type": "SENTENCE_COMPLETION", "correct_answer": "paralysis", "options": None},
            {"id": 11, "text": "Early sleep cycles contain more:", "type": "MULTIPLE_CHOICE",
             "correct_answer": "A",
             "options": ["A. Deep sleep", "B. REM sleep", "C. Light sleep", "D. Dreaming"]},
            {"id": 12, "text": "Chronic sleep restriction preferentially eliminates REM and deep sleep.",
             "type": "TRUE_FALSE_NOT_GIVEN", "correct_answer": "True",
             "options": ["True", "False", "Not Given"]},
            {"id": 13, "text": "All adults need exactly eight hours of sleep.",
             "type": "TRUE_FALSE_NOT_GIVEN", "correct_answer": "Not Given",
             "options": ["True", "False", "Not Given"]},
        ],
    },
]

BASELINE_READING_CONTENT_PART3 = [
    {
        "passage_number": 3,
        "title": "The Epistemology of Artificial Intelligence",
        "difficulty": "hard",
        "content": (
            "A. The rapid advancement of artificial intelligence has precipitated "
            "a philosophical crisis concerning the nature of knowledge itself. "
            "When a neural network arrives at a conclusion through millions of "
            "weighted connections, can we meaningfully say it 'knows' something? "
            "This question, far from being merely academic, has profound implications "
            "for how we deploy AI in consequential domains such as medicine, law, "
            "and criminal justice.\n\n"
            "B. Traditional epistemology defines knowledge as justified true belief — "
            "a formulation dating back to Plato's Theaetetus. Under this framework, "
            "knowing requires not merely holding a correct belief, but having adequate "
            "justification for that belief. The challenge with contemporary AI systems, "
            "particularly deep learning networks, is that their 'justifications' are "
            "opaque even to their creators.\n\n"
            "C. This opacity has been termed the 'black box problem.' While we can "
            "observe that a trained model achieves ninety-seven percent accuracy in "
            "diagnosing certain cancers from medical images, we cannot fully articulate "
            "the reasoning process by which it arrives at individual diagnoses. This "
            "creates an asymmetry between predictive power and explanatory insight "
            "that challenges our conventional epistemic frameworks.\n\n"
            "D. Some philosophers argue that AI systems possess what might be called "
            "'procedural knowledge' — they know how to perform tasks without possessing "
            "propositional knowledge about why their methods work. This distinction, "
            "originally articulated by Gilbert Ryle in his 1949 work 'The Concept of "
            "Mind,' acquires new significance in the context of machine learning.\n\n"
            "E. The implications for trust and accountability are substantial. If a "
            "medical AI recommends a treatment that proves harmful, the question of "
            "epistemic responsibility becomes deeply problematic. The developer may "
            "not understand why the model made its recommendation; the clinician who "
            "followed it relied on statistical authority rather than mechanistic "
            "understanding. We face a distributed epistemology in which no single "
            "agent possesses complete justification for the decision.\n\n"
            "F. Emerging approaches such as Explainable AI (XAI) attempt to bridge "
            "this gap by generating post-hoc rationalisations of model decisions. "
            "However, critics note that these explanations may be reconstructions "
            "rather than genuine reflections of the model's internal processes — "
            "akin to confabulation in human psychology. The explanations satisfy our "
            "narrative desire for reasons without necessarily capturing the actual "
            "computational pathways.\n\n"
            "G. Ultimately, the epistemological challenges posed by AI may require "
            "us to develop new frameworks for knowledge that accommodate non-human "
            "cognitive architectures. Just as quantum mechanics demanded new "
            "mathematical formalisms beyond classical physics, machine intelligence "
            "may demand new epistemological categories beyond justified true belief."
        ),
        "word_count": 1020,
        "questions": [
            {"id": 14, "text": "AI knowledge challenges have only theoretical importance.",
             "type": "TRUE_FALSE_NOT_GIVEN", "correct_answer": "False",
             "options": ["True", "False", "Not Given"]},
            {"id": 15, "text": "Traditional epistemology defines knowledge as:",
             "type": "MULTIPLE_CHOICE", "correct_answer": "C",
             "options": ["A. True belief", "B. Correct information",
                        "C. Justified true belief", "D. Empirical observation"]},
            {"id": 16, "text": "The 'black box problem' refers to AI systems' ___.",
             "type": "SENTENCE_COMPLETION", "correct_answer": "opacity", "options": None},
            {"id": 17, "text": "Gilbert Ryle published 'The Concept of Mind' in ___.",
             "type": "FILL_BLANK", "correct_answer": "1949", "options": None},
            {"id": 18, "text": "XAI explanations may be reconstructions rather than genuine reflections.",
             "type": "TRUE_FALSE_NOT_GIVEN", "correct_answer": "True",
             "options": ["True", "False", "Not Given"]},
            {"id": 19, "text": "Most AI researchers reject the black box problem.",
             "type": "TRUE_FALSE_NOT_GIVEN", "correct_answer": "Not Given",
             "options": ["True", "False", "Not Given"]},
            {"id": 20, "text": "The author compares AI epistemology challenges to:",
             "type": "MULTIPLE_CHOICE", "correct_answer": "D",
             "options": ["A. Classical philosophy", "B. Human psychology",
                        "C. Computer science", "D. Quantum mechanics"]},
        ],
    },
]


# ═══════════════════════════════════════════════════════════════════════════════
# BASELINE WRITING CONTENT
# ═══════════════════════════════════════════════════════════════════════════════

BASELINE_WRITING_CONTENT = [
    {
        "task_number": 1,
        "task_type": "task_1",
        "prompt": (
            "The bar chart below shows the percentage of households with internet "
            "access in five different countries in 2005 and 2015.\n\n"
            "Summarise the information by selecting and reporting the main features, "
            "and make comparisons where relevant.\n\n"
            "Write at least 150 words."
        ),
        "chart_data": {
            "type": "bar",
            "title": "Household Internet Access (%)",
            "categories": ["USA", "UK", "Japan", "Brazil", "India"],
            "series": [
                {"name": "2005", "data": [62, 55, 64, 13, 2]},
                {"name": "2015", "data": [84, 86, 91, 51, 26]},
            ],
        },
        "min_words": 150,
    },
    {
        "task_number": 2,
        "task_type": "task_2",
        "prompt": (
            "Some people believe that university education should be free for all "
            "students, while others argue that students should pay their own fees.\n\n"
            "Discuss both views and give your own opinion.\n\n"
            "Give reasons for your answer and include any relevant examples from "
            "your own knowledge or experience.\n\n"
            "Write at least 250 words."
        ),
        "chart_data": None,
        "min_words": 250,
    },
]

# ═══════════════════════════════════════════════════════════════════════════════
# BASELINE SPEAKING CONTENT
# ═══════════════════════════════════════════════════════════════════════════════

BASELINE_SPEAKING_CONTENT = [
    {
        "part_number": 1,
        "title": "Introduction and General Questions",
        "questions": [
            "Can you tell me your full name, please?",
            "Where are you from? Can you describe your hometown?",
            "Do you work or are you a student?",
            "What do you enjoy doing in your free time?",
            "How often do you use public transport?",
        ],
    },
    {
        "part_number": 2,
        "title": "Individual Long Turn",
        "cue_card": (
            "Describe a book that you have read recently that made a strong "
            "impression on you.\n\n"
            "You should say:\n"
            "- what the book was about\n"
            "- why you decided to read it\n"
            "- what you learned from it\n"
            "- and explain why it made such a strong impression on you."
        ),
        "follow_up": "Do you often read books?",
    },
    {
        "part_number": 3,
        "title": "Two-way Discussion",
        "topic": "Reading and Education",
        "questions": [
            "Do you think reading is becoming less popular among young people? Why or why not?",
            "How has technology changed the way people read?",
            "Some people argue that schools should focus more on digital literacy than traditional reading. Do you agree?",
            "In what ways can reading contribute to personal development?",
        ],
    },
]


# ═══════════════════════════════════════════════════════════════════════════════
# HELPER: Build full baseline test content dict
# ═══════════════════════════════════════════════════════════════════════════════

def get_baseline_section_content():
    """Return the full baseline test content organized by section."""
    return {
        "listening": {
            "sections": BASELINE_LISTENING_CONTENT + BASELINE_LISTENING_CONTENT_PART2,
            "difficulty_config": LISTENING_DIFFICULTY,
            "total_questions": 20,
        },
        "reading": {
            "passages": (
                BASELINE_READING_CONTENT
                + BASELINE_READING_CONTENT_PART2
                + BASELINE_READING_CONTENT_PART3
            ),
            "difficulty_config": READING_DIFFICULTY,
            "total_questions": 20,
        },
        "writing": {
            "tasks": BASELINE_WRITING_CONTENT,
            "difficulty_config": WRITING_DIFFICULTY,
        },
        "speaking": {
            "parts": BASELINE_SPEAKING_CONTENT,
            "difficulty_config": SPEAKING_DIFFICULTY,
        },
    }
