"""
Imported IELTS Mock Tests — real exam-style content from document files.
These serve as pre-built tests available for all users.
"""

from services.mocktest.baseline_data import SECTION_TIMING, SECTION_ORDER

# ═══════════════════════════════════════════════════════════════════════════════
# MOCK TEST 1 — "The Development of Writing Systems" + "Urban Heat Islands"
# ═══════════════════════════════════════════════════════════════════════════════

MOCK_TEST_1 = {
    "id": "imported_1",
    "title": "IELTS Academic Mock Test — Version 1",
    "description": "General academic topics: Writing Systems, Urban Heat Islands",
    "listening": None,  # No listening in these imported tests
    "reading": {
        "passages": [
            {
                "passage_number": 1,
                "title": "The Development of Writing Systems",
                "difficulty": "medium",
                "content": (
"A  Writing ranks among the most transformative inventions in human history, "
"allowing knowledge to be stored, transmitted across generations, and accumulated "
"far beyond the limits of memory. Remarkably, fully-fledged writing systems appear "
"to have emerged independently in several parts of the ancient world, including "
"Mesopotamia, Egypt, China and Mesoamerica, each following a distinct path of development.\n\n"
"B  The earliest known script, cuneiform, was developed by the Sumerians in "
"Mesopotamia around 3400 BCE. It began not as a means of recording language but "
"as an accounting device: small clay tokens representing quantities of goods such "
"as grain or livestock. Over several centuries, these tokens gave way to wedge-shaped "
"marks pressed into clay tablets with a reed stylus, and the symbols gradually shifted "
"from simple pictures of objects to more abstract signs capable of representing sounds "
"as well as ideas.\n\n"
"C  Egyptian hieroglyphs emerged at roughly the same period. Unlike cuneiform, "
"hieroglyphic script retained its elaborate, pictorial character for millennia and "
"was reserved largely for formal and religious inscriptions on temple walls and "
"monuments. Alongside it, the Egyptians used two more cursive scripts, hieratic and "
"later demotic, for everyday administrative and literary purposes. Hieroglyphs "
"remained undeciphered by modern scholars until 1822, when the French linguist "
"Jean-Francois Champollion used the trilingual Rosetta Stone to unlock their meaning.\n\n"
"D  In China, the earliest surviving examples of writing are the oracle bone "
"inscriptions of the Shang dynasty, dating to around 1200 BCE. These logographic "
"characters, in which each symbol represents a word or morpheme rather than a sound, "
"show striking continuity with modern Chinese characters. This durability has allowed "
"the script to unify readers across a vast area whose spoken dialects are often "
"mutually unintelligible.\n\n"
"E  A quite different, and much later, case is found in Mesoamerica, where the Maya "
"developed a sophisticated script combining logographic and syllabic elements. Because "
"it arose entirely independently of Old World civilisations, with no plausible route "
"of contact, it is regarded by scholars as one of the clearest instances of writing "
"being invented from scratch. The script proved extraordinarily difficult to interpret, "
"and it was only in the final decades of the twentieth century, through the combined "
"efforts of epigraphers and linguists, that the majority of Maya glyphs were "
"successfully read.\n\n"
"F  Perhaps the single most consequential breakthrough in the history of writing was "
"the invention of the alphabet. The Phoenicians, a seafaring trading people, developed "
"a consonantal script around 1050 BCE in which each symbol stood for a single sound "
"rather than a whole word or syllable. This dramatically reduced the number of signs "
"a writer needed to learn, from many hundreds to around twenty-two. The Greeks later "
"adapted the Phoenician system, adding symbols for vowels, and this Greek alphabet "
"became the ancestor of the Latin, Cyrillic and, indirectly, many other alphabets "
"used across the world today.\n\n"
"G  Scholars have long debated whether writing was invented only once, in Mesopotamia, "
"and then diffused to other regions through cultural contact, or whether it arose "
"independently in different places. While the question of diffusion between Mesopotamia "
"and Egypt remains open, the Mesoamerican case provides strong evidence that writing "
"was invented independently at least three or four times in human history, since no "
"contact between the Old and New Worlds has ever been demonstrated for this period."
                ),
                "word_count": 680,
                "questions": [
                    {"id": 1, "text": "Paragraph B", "type": "MATCHING_HEADINGS",
                     "correct_answer": "iv",
                     "options": ["i. A shift from meaning-based symbols to sound-based symbols",
                                 "ii. A script cracked only after decades of modern scholarly work",
                                 "iii. Evidence that writing was invented more than once",
                                 "iv. A system that grew out of a record-keeping need",
                                 "v. A writing tradition that changed remarkably little over time",
                                 "vi. Separate scripts used for different social purposes",
                                 "vii. A script deciphered with the help of a famous inscription"]},
                    {"id": 2, "text": "Paragraph C", "type": "MATCHING_HEADINGS",
                     "correct_answer": "vi", "options": None},
                    {"id": 3, "text": "Paragraph D", "type": "MATCHING_HEADINGS",
                     "correct_answer": "v", "options": None},
                    {"id": 4, "text": "Paragraph E", "type": "MATCHING_HEADINGS",
                     "correct_answer": "ii", "options": None},
                    {"id": 5, "text": "Paragraph F", "type": "MATCHING_HEADINGS",
                     "correct_answer": "i", "options": None},
                    {"id": 6, "text": "The Sumerian writing system began purely as a way of recording spoken language.",
                     "type": "TRUE_FALSE_NOT_GIVEN", "correct_answer": "False",
                     "options": ["True", "False", "Not Given"]},
                    {"id": 7, "text": "Champollion was the first scholar to attempt to decipher Egyptian hieroglyphs.",
                     "type": "TRUE_FALSE_NOT_GIVEN", "correct_answer": "Not Given",
                     "options": ["True", "False", "Not Given"]},
                    {"id": 8, "text": "Chinese characters have remained largely stable in form for roughly three thousand years.",
                     "type": "TRUE_FALSE_NOT_GIVEN", "correct_answer": "True",
                     "options": ["True", "False", "Not Given"]},
                    {"id": 9, "text": "The Maya writing system was influenced by contact with Old World civilisations.",
                     "type": "TRUE_FALSE_NOT_GIVEN", "correct_answer": "False",
                     "options": ["True", "False", "Not Given"]},
                    {"id": 10, "text": "Most scholars now agree that writing was invented only once and then spread through contact.",
                     "type": "TRUE_FALSE_NOT_GIVEN", "correct_answer": "False",
                     "options": ["True", "False", "Not Given"]},
                ],
            },
            {
                "passage_number": 2,
                "title": "Urban Heat Islands: Causes and Solutions",
                "difficulty": "hard",
                "content": (
"A  Anyone who has walked from a leafy suburb into a city centre on a summer "
"afternoon may have noticed that the air feels distinctly warmer downtown. This is "
"not merely a subjective impression: cities are, on average, measurably hotter than "
"the rural areas that surround them, sometimes by as much as several degrees Celsius. "
"Climatologists refer to this phenomenon as the urban heat island, or UHI, effect.\n\n"
"B  Several factors combine to produce this effect. Dark surfaces such as asphalt "
"roads and conventional roofing absorb far more solar radiation than natural vegetation "
"does, and they release this stored heat slowly after sunset. The removal of trees and "
"grass for construction reduces evapotranspiration, a natural cooling process by which "
"plants release water vapour into the air. Waste heat from vehicles, air conditioning "
"units and industrial processes adds further warmth, while the dense arrangement of "
"tall buildings — sometimes called the urban canyon effect — traps heat and restricts "
"the natural airflow that would otherwise disperse it.\n\n"
"C  The consequences extend well beyond mere discomfort. Elevated urban temperatures "
"increase demand for air conditioning, which in turn raises energy consumption and "
"associated greenhouse gas emissions, creating a feedback loop. Heat-related illness "
"and mortality rise during heatwaves, disproportionately affecting the elderly and "
"those without access to cooling. Higher temperatures also accelerate the chemical "
"reactions that produce ground-level ozone, worsening air quality in already polluted "
"cities.\n\n"
"D  A striking illustration of the social dimension of this problem comes from research "
"conducted in several United States cities. Researchers found that neighbourhoods "
"subjected decades ago to 'redlining' — a discriminatory practice in which lenders "
"refused mortgages to residents of certain, often predominantly minority, districts — "
"tend to be significantly hotter today than wealthier neighbourhoods nearby. Chronic "
"underinvestment in these areas left them with fewer trees and less green "
"infrastructure, meaning that a historical policy continues to shape residents' "
"exposure to heat today.\n\n"
"E  Fortunately, a range of mitigation strategies has been developed. Reflective, or "
"'cool', roofing and paving materials reflect more sunlight than conventional dark "
"surfaces, reducing heat absorption. Expanding the urban tree canopy provides shade "
"and restores evapotranspiration, while permeable paving allows rainwater to filter "
"through rather than run off, cooling the surface as it evaporates. Urban planners can "
"also design street layouts that preserve corridors for airflow. Singapore is frequently "
"cited for its extensive use of vertical greenery — plants grown on the facades of "
"buildings — as part of a broader cooling strategy.\n\n"
"F  Green roofs, a layer of vegetation planted on a building's rooftop, deserve "
"particular attention. Besides cooling the immediate area, they provide insulation that "
"can reduce a building's heating and cooling costs, and they absorb rainwater, easing "
"pressure on urban drainage systems during storms. Their main drawback is cost: the "
"structural reinforcement and irrigation systems required for installation carry a "
"higher upfront price than conventional roofing, which has limited their adoption. "
"Some municipal governments now offer subsidies or tax incentives to encourage building "
"owners to install them.\n\n"
"G  Looking ahead, researchers warn that climate change is likely to intensify the "
"urban heat island effect, as heatwaves are projected to become both more frequent and "
"more severe in many regions. Studies consistently find that combining several "
"strategies — increased tree cover, reflective materials and heat-conscious planning — "
"produces far better outcomes than relying on any single intervention. In response, a "
"growing number of cities have begun drafting dedicated 'heat action plans' to "
"coordinate these efforts."
                ),
                "word_count": 750,
                "questions": [
                    {"id": 11, "text": "According to the passage, urban heat islands are primarily caused by:",
                     "type": "MULTIPLE_CHOICE", "correct_answer": "B",
                     "options": ["A. increased rainfall in cities",
                                 "B. surfaces and human activity that retain and generate heat",
                                 "C. the higher altitude of city centres",
                                 "D. ocean currents near coastal cities"]},
                    {"id": 12, "text": "The case study of redlining mentioned in the passage relates historic lending discrimination to:",
                     "type": "MULTIPLE_CHOICE", "correct_answer": "C",
                     "options": ["A. higher property values today",
                                 "B. greater tree cover in wealthy neighbourhoods only",
                                 "C. present-day temperature differences within cities",
                                 "D. reduced traffic congestion"]},
                    {"id": 13, "text": "Which of the following is NOT mentioned in the passage as a mitigation strategy?",
                     "type": "MULTIPLE_CHOICE", "correct_answer": "C",
                     "options": ["A. reflective roofing", "B. green roofs",
                                 "C. desalination plants", "D. permeable pavements"]},
                    {"id": 14, "text": "What does the passage identify as the main factor limiting wider adoption of green roofs?",
                     "type": "MULTIPLE_CHOICE", "correct_answer": "B",
                     "options": ["A. lack of technical knowledge",
                                 "B. the initial installation cost",
                                 "C. legal restrictions in most cities",
                                 "D. insufficient rainfall"]},
                    {"id": 15, "text": "The measurable temperature difference between cities and surrounding rural areas is known as the ___.",
                     "type": "FILL_BLANK", "correct_answer": "urban heat island", "options": None},
                    {"id": 16, "text": "Reduced vegetation lowers a natural cooling process called ___.",
                     "type": "FILL_BLANK", "correct_answer": "evapotranspiration", "options": None},
                    {"id": 17, "text": "The dense arrangement of tall buildings that traps heat is known as the ___.",
                     "type": "FILL_BLANK", "correct_answer": "urban canyon", "options": None},
                    {"id": 18, "text": "Singapore is known for using ___ on buildings as part of its cooling strategy.",
                     "type": "FILL_BLANK", "correct_answer": "vertical greenery", "options": None},
                    {"id": 19, "text": "Researchers believe that a single mitigation strategy is generally sufficient to address urban heat islands.",
                     "type": "TRUE_FALSE_NOT_GIVEN", "correct_answer": "No",
                     "options": ["Yes", "No", "Not Given"]},
                    {"id": 20, "text": "Heatwaves are expected to become less frequent as a result of climate change.",
                     "type": "TRUE_FALSE_NOT_GIVEN", "correct_answer": "No",
                     "options": ["Yes", "No", "Not Given"]},
                ],
            },
        ],
        "difficulty_config": [
            {"passage_number": 1, "difficulty": "medium", "vocabulary_level": "academic", "grammar_complexity": "medium"},
            {"passage_number": 2, "difficulty": "hard", "vocabulary_level": "c1", "grammar_complexity": "complex"},
        ],
        "total_questions": 20,
    },
    "writing": {
        "tasks": [
            {
                "task_number": 1,
                "task_type": "task_1",
                "prompt": (
                    "The chart below shows average household spending on entertainment "
                    "in four countries in 2023.\n\n"
                    "Summarise the information by selecting and reporting the main features, "
                    "and make comparisons where relevant.\n\n"
                    "Write at least 150 words."
                ),
                "chart_data": {
                    "type": "bar",
                    "title": "Average Household Spending on Entertainment (2023)",
                    "categories": ["USA", "UK", "Australia", "Japan"],
                    "series": [
                        {"name": "Streaming", "data": [45, 38, 42, 30]},
                        {"name": "Cinema", "data": [25, 20, 22, 18]},
                        {"name": "Live Events", "data": [35, 30, 28, 15]},
                        {"name": "Gaming", "data": [40, 32, 35, 50]},
                    ],
                },
                "min_words": 150,
            },
            {
                "task_number": 2,
                "task_type": "task_2",
                "prompt": (
                    "Some people believe that unpaid community service should be a "
                    "compulsory part of high school education. To what extent do you "
                    "agree or disagree?\n\n"
                    "Give reasons for your answer and include any relevant examples "
                    "from your own knowledge or experience.\n\n"
                    "Write at least 250 words."
                ),
                "chart_data": None,
                "min_words": 250,
            },
        ],
        "difficulty_config": [
            {"task_number": 1, "difficulty": "medium", "min_words": 150, "suggested_time_minutes": 20},
            {"task_number": 2, "difficulty": "hard", "min_words": 250, "suggested_time_minutes": 40},
        ],
    },
    "speaking": {
        "parts": [
            {
                "part_number": 1,
                "title": "Introduction and Interview",
                "questions": [
                    "Let's talk about your hometown. Where is it, and what do you like about living there?",
                    "Are you currently working or studying?",
                    "What do you usually do in your free time?",
                    "Do you prefer sunny weather or rainy weather? Why?",
                ],
            },
            {
                "part_number": 2,
                "title": "Individual Long Turn",
                "cue_card": (
                    "Describe a time when you helped a stranger.\n\n"
                    "You should say:\n"
                    "- who the stranger was\n"
                    "- what happened\n"
                    "- how you helped them\n"
                    "- and explain how you felt about the experience."
                ),
                "follow_up": "Do you often help people you don't know?",
            },
            {
                "part_number": 3,
                "title": "Two-way Discussion",
                "topic": "Helping Others and Community",
                "questions": [
                    "Why do you think some people today are reluctant to help strangers?",
                    "Do you think communities are becoming less close-knit than they used to be? Why or why not?",
                    "What role should schools play in teaching children to help others?",
                    "Should looking after vulnerable people be mainly the government's responsibility, or should individuals take more initiative?",
                ],
            },
        ],
        "difficulty_config": [
            {"part_number": 1, "difficulty": "easy", "duration_minutes": 4},
            {"part_number": 2, "difficulty": "medium", "duration_minutes": 4},
            {"part_number": 3, "difficulty": "hard", "duration_minutes": 5},
        ],
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# MOCK TEST 2 — "The Science of Sleep" + "Renewable Energy in Island Nations"
# ═══════════════════════════════════════════════════════════════════════════════

MOCK_TEST_2 = {
    "id": "imported_2",
    "title": "IELTS Academic Mock Test — Version 2",
    "description": "General academic topics: Sleep Science, Renewable Energy",
    "listening": None,
    "reading": {
        "passages": [
            {
                "passage_number": 1,
                "title": "The Science of Sleep",
                "difficulty": "medium",
                "content": (
"A  For much of the twentieth century, sleep was widely regarded as a passive state "
"in which the brain effectively switched off. Modern neuroscience has overturned this "
"view entirely: sleep is now understood to be an active and highly organised biological "
"process, essential to physical health, emotional regulation and cognitive performance. "
"Most adults require between seven and nine hours of sleep per night to function "
"optimally, though individual needs vary.\n\n"
"B  A night's sleep is not uniform but consists of distinct stages that cycle roughly "
"every ninety minutes. Non-REM sleep progresses from light sleep into deep sleep, "
"during which the body repairs tissue, builds bone and muscle, and strengthens the "
"immune system. REM (rapid eye movement) sleep, by contrast, is the stage most closely "
"associated with vivid dreaming and appears to play a crucial role in processing "
"emotional experiences.\n\n"
"C  Underlying these nightly cycles is the circadian rhythm, an internal clock of "
"roughly twenty-four hours governed by a cluster of neurons in the brain called the "
"suprachiasmatic nucleus. This internal clock is strongly influenced by exposure to "
"light: as darkness falls, the brain releases the hormone melatonin, signalling to "
"the body that it is time to prepare for sleep.\n\n"
"D  Chronic sleep deprivation carries serious consequences. In the short term it "
"impairs concentration, memory and decision-making, and it weakens the immune system's "
"ability to fight infection. Over the longer term, insufficient sleep has been linked "
"to an increased risk of cardiovascular disease, mood disorders, obesity and type 2 "
"diabetes, making adequate sleep a matter of long-term public health as much as "
"day-to-day wellbeing.\n\n"
"E  Modern life presents numerous obstacles to healthy sleep. Artificial light, and "
"blue light from smartphone and computer screens in particular, suppresses the "
"production of melatonin and can delay the onset of sleep. Shift work forces the "
"body's internal clock out of alignment with the natural day-night cycle, while "
"caffeine consumed even several hours before bedtime can measurably delay sleep onset "
"and reduce sleep quality.\n\n"
"F  One of the more striking discoveries in recent decades concerns the relationship "
"between sleep and memory. During sleep, the brain appears to reorganise and "
"consolidate information acquired during the preceding day, strengthening connections "
"between neurons that encode newly learned material. In controlled studies, "
"participants who slept after learning a new task consistently performed better on "
"subsequent recall tests than those who remained awake for an equivalent period, "
"underscoring sleep's active contribution to learning.\n\n"
"G  Given the importance of sleep, researchers increasingly recommend a set of "
"practices known collectively as sleep hygiene: maintaining a consistent sleep "
"schedule, limiting screen use in the hour before bed, keeping the bedroom cool, "
"dark and quiet, and avoiding caffeine and alcohol close to bedtime. Sleep specialists "
"argue that these habits deserve the same level of attention that people typically "
"give to diet and exercise."
                ),
                "word_count": 650,
                "questions": [
                    {"id": 1, "text": "Paragraph B", "type": "MATCHING_HEADINGS",
                     "correct_answer": "iv",
                     "options": ["i. How the body keeps track of time",
                                 "ii. The price paid for insufficient rest",
                                 "iii. Sleep's hidden contribution to learning",
                                 "iv. The different phases of a night's sleep",
                                 "v. Everyday habits that interfere with rest",
                                 "vi. Practical steps toward better rest",
                                 "vii. A shift in scientific understanding"]},
                    {"id": 2, "text": "Paragraph C", "type": "MATCHING_HEADINGS",
                     "correct_answer": "i", "options": None},
                    {"id": 3, "text": "Paragraph D", "type": "MATCHING_HEADINGS",
                     "correct_answer": "ii", "options": None},
                    {"id": 4, "text": "Paragraph E", "type": "MATCHING_HEADINGS",
                     "correct_answer": "v", "options": None},
                    {"id": 5, "text": "Paragraph F", "type": "MATCHING_HEADINGS",
                     "correct_answer": "iii", "options": None},
                    {"id": 6, "text": "Sleep is now regarded by scientists as a largely passive, inactive state.",
                     "type": "TRUE_FALSE_NOT_GIVEN", "correct_answer": "False",
                     "options": ["True", "False", "Not Given"]},
                    {"id": 7, "text": "REM sleep is primarily responsible for repairing muscle tissue.",
                     "type": "TRUE_FALSE_NOT_GIVEN", "correct_answer": "False",
                     "options": ["True", "False", "Not Given"]},
                    {"id": 8, "text": "The suprachiasmatic nucleus helps regulate the body's internal clock.",
                     "type": "TRUE_FALSE_NOT_GIVEN", "correct_answer": "True",
                     "options": ["True", "False", "Not Given"]},
                    {"id": 9, "text": "People who sleep after learning new material tend to perform worse on memory tests than those who stay awake.",
                     "type": "TRUE_FALSE_NOT_GIVEN", "correct_answer": "False",
                     "options": ["True", "False", "Not Given"]},
                    {"id": 10, "text": "The passage recommends treating sleep with the same level of importance as diet and exercise.",
                     "type": "TRUE_FALSE_NOT_GIVEN", "correct_answer": "True",
                     "options": ["True", "False", "Not Given"]},
                ],
            },
            {
                "passage_number": 2,
                "title": "Renewable Energy in Island Nations",
                "difficulty": "hard",
                "content": (
"A  Small island nations, particularly those scattered across the Pacific and the "
"Caribbean, have historically depended almost entirely on imported diesel fuel to "
"generate electricity. Because this fuel must be shipped in, often over long distances, "
"island communities have long faced high energy costs and vulnerability to supply "
"disruptions caused by storms, shipping delays or global price shocks.\n\n"
"B  Paradoxically, many of these same islands possess considerable natural advantages "
"for renewable energy: abundant sunshine, steady trade winds, and in some cases "
"geothermal or wave energy potential. Their relatively small and self-contained "
"electricity grids also make them attractive testbeds for renewable technologies, "
"since changes can be trialled and evaluated more quickly than on the vast "
"interconnected grids of large countries.\n\n"
"C  One Pacific island nation offers an instructive example. Having set a target of "
"generating all of its electricity from renewable sources, the country has installed "
"a combination of solar panel arrays, battery storage systems and wind turbines, "
"steadily displacing diesel generators that previously supplied the majority of its "
"power.\n\n"
"D  The transition is not without difficulty. Infrastructure must be built to withstand "
"tropical storms, which raises construction costs. The intermittent nature of solar "
"and wind power means that reliable battery storage is essential to maintain a stable "
"electricity supply, and such storage remains expensive. In addition, many islands "
"lack a sufficiently large workforce trained in the specialised skills needed to "
"install and maintain renewable systems.\n\n"
"E  Financing these projects is itself a considerable challenge. International climate "
"funds and multilateral development banks have stepped in to provide grants and "
"low-interest loans, recognising the disproportionate exposure of small islands to "
"climate change despite their negligible contribution to global emissions. In some "
"cases, governments have signed power purchase agreements with private renewable "
"energy developers, under which the developer bears the upfront capital cost and the "
"government simply commits to purchasing the electricity generated, thereby limiting "
"its own financial exposure.\n\n"
"F  The benefits of a successful transition extend well beyond the electricity sector. "
"Reduced spending on imported fuel frees up government budgets for other national "
"priorities such as healthcare and education. Greater energy independence also enhances "
"resilience during periods when shipping routes are disrupted, whether by severe "
"weather or global events. The renewable sector itself creates new local jobs in "
"installation, operation and maintenance.\n\n"
"G  Experts caution that a complete transition will likely take many years, given the "
"continuing cost of storage technology and the time required to build up local "
"technical expertise. Nonetheless, many view island nations as valuable proving "
"grounds: the lessons learned about integrating high shares of renewable energy into "
"a small grid, they argue, could usefully inform renewable energy strategies in much "
"larger countries facing similar technical challenges at greater scale."
                ),
                "word_count": 700,
                "questions": [
                    {"id": 11, "text": "Why have island nations historically relied heavily on imported diesel?",
                     "type": "MULTIPLE_CHOICE", "correct_answer": "C",
                     "options": ["A. lack of sufficient sunlight",
                                 "B. a limited local workforce",
                                 "C. an absence of readily available domestic energy sources",
                                 "D. government policy against renewables"]},
                    {"id": 12, "text": "According to the passage, small island electricity grids are attractive for renewable transition mainly because:",
                     "type": "MULTIPLE_CHOICE", "correct_answer": "B",
                     "options": ["A. they require less regulation than larger grids",
                                 "B. their size makes them useful for trialling new technology quickly",
                                 "C. they receive more government funding than large countries",
                                 "D. diesel generators are banned on most islands"]},
                    {"id": 13, "text": "What is identified as a major technical challenge for renewable systems on islands?",
                     "type": "MULTIPLE_CHOICE", "correct_answer": "B",
                     "options": ["A. a lack of sunlight during the day",
                                 "B. storing energy from intermittent sources reliably",
                                 "C. producing too much electricity",
                                 "D. strong opposition from residents"]},
                    {"id": 14, "text": "How do some island governments reduce their financial risk in renewable energy projects?",
                     "type": "MULTIPLE_CHOICE", "correct_answer": "B",
                     "options": ["A. by nationalising energy companies",
                                 "B. through power purchase agreements with private developers",
                                 "C. by raising electricity prices sharply",
                                 "D. by importing more diesel as a backup"]},
                    {"id": 15, "text": "Island nations are turning to renewable energy after decades of dependence on imported ___.",
                     "type": "FILL_BLANK", "correct_answer": "diesel", "options": None},
                    {"id": 16, "text": "Many islands benefit from abundant sunlight and steady ___, making them well suited to solar and wind power.",
                     "type": "FILL_BLANK", "correct_answer": "wind", "options": None},
                    {"id": 17, "text": "Because these sources are intermittent, effective energy ___ systems are essential.",
                     "type": "FILL_BLANK", "correct_answer": "storage", "options": None},
                    {"id": 18, "text": "Reducing reliance on fuel imports can also improve national ___ when shipping routes are disrupted.",
                     "type": "FILL_BLANK", "correct_answer": "resilience", "options": None},
                    {"id": 19, "text": "Experts believe island nations will achieve a full renewable energy transition within the next one or two years.",
                     "type": "TRUE_FALSE_NOT_GIVEN", "correct_answer": "No",
                     "options": ["Yes", "No", "Not Given"]},
                    {"id": 20, "text": "The lessons learned from island renewable projects may be useful for larger countries.",
                     "type": "TRUE_FALSE_NOT_GIVEN", "correct_answer": "Yes",
                     "options": ["Yes", "No", "Not Given"]},
                ],
            },
        ],
        "difficulty_config": [
            {"passage_number": 1, "difficulty": "medium", "vocabulary_level": "academic", "grammar_complexity": "medium"},
            {"passage_number": 2, "difficulty": "hard", "vocabulary_level": "c1", "grammar_complexity": "complex"},
        ],
        "total_questions": 20,
    },
    "writing": {
        "tasks": [
            {
                "task_number": 1,
                "task_type": "task_1",
                "prompt": (
                    "The graph below shows the number of international students in "
                    "three countries between 2005 and 2020.\n\n"
                    "Summarise the information by selecting and reporting the main "
                    "features, and make comparisons where relevant.\n\n"
                    "Write at least 150 words."
                ),
                "chart_data": {
                    "type": "line",
                    "title": "International Students (thousands) 2005-2020",
                    "categories": ["2005", "2008", "2011", "2014", "2017", "2020"],
                    "series": [
                        {"name": "Country A", "data": [180, 220, 280, 350, 420, 390]},
                        {"name": "Country B", "data": [120, 150, 190, 240, 310, 340]},
                        {"name": "Country C", "data": [80, 95, 110, 130, 160, 175]},
                    ],
                },
                "min_words": 150,
            },
            {
                "task_number": 2,
                "task_type": "task_2",
                "prompt": (
                    "In many countries, the gap between the rich and the poor is "
                    "increasing.\n\n"
                    "What problems does this cause, and what measures could be taken "
                    "to reduce it?\n\n"
                    "Write at least 250 words."
                ),
                "chart_data": None,
                "min_words": 250,
            },
        ],
        "difficulty_config": [
            {"task_number": 1, "difficulty": "medium", "min_words": 150, "suggested_time_minutes": 20},
            {"task_number": 2, "difficulty": "hard", "min_words": 250, "suggested_time_minutes": 40},
        ],
    },
    "speaking": {
        "parts": [
            {
                "part_number": 1,
                "title": "Introduction and Interview",
                "questions": [
                    "Do you have any hobbies? How did you first become interested in them?",
                    "What kind of food do you enjoy eating most?",
                    "Do you use technology a lot in your daily life?",
                    "Did you enjoy technology or computer classes when you were at school?",
                ],
            },
            {
                "part_number": 2,
                "title": "Individual Long Turn",
                "cue_card": (
                    "Describe a piece of technology that you find very useful.\n\n"
                    "You should say:\n"
                    "- what it is\n"
                    "- how often you use it\n"
                    "- what you use it for\n"
                    "- and explain why you find it useful."
                ),
                "follow_up": "Is there any technology you would like to learn to use better?",
            },
            {
                "part_number": 3,
                "title": "Two-way Discussion",
                "topic": "Technology and Society",
                "questions": [
                    "How has technology changed the way people communicate with one another?",
                    "Do you think older people find it harder to adapt to new technology? Why might that be?",
                    "What are some of the disadvantages of relying too heavily on technology?",
                    "How do you think technology will change education in the future?",
                ],
            },
        ],
        "difficulty_config": [
            {"part_number": 1, "difficulty": "easy", "duration_minutes": 4},
            {"part_number": 2, "difficulty": "medium", "duration_minutes": 4},
            {"part_number": 3, "difficulty": "hard", "duration_minutes": 5},
        ],
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# ALL IMPORTED TESTS — registry
# ═══════════════════════════════════════════════════════════════════════════════

IMPORTED_TESTS = [MOCK_TEST_1, MOCK_TEST_2]


def get_imported_test(test_id: str) -> dict | None:
    """Get an imported test by its ID."""
    for test in IMPORTED_TESTS:
        if test["id"] == test_id:
            return test
    return None


def get_imported_test_list() -> list[dict]:
    """Get summary list of all imported tests."""
    return [
        {
            "id": t["id"],
            "title": t["title"],
            "description": t["description"],
            "has_listening": t["listening"] is not None,
            "has_reading": t["reading"] is not None,
            "has_writing": t["writing"] is not None,
            "has_speaking": t["speaking"] is not None,
        }
        for t in IMPORTED_TESTS
    ]
