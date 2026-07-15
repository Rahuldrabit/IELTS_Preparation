"""Seed data for the IELTS Tutor database.

Uses synchronous psycopg2 to avoid asyncpg auth issues with Python 3.14.
Run with: python -m shared.seed
"""
from datetime import date, datetime, timedelta

from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import Session

from shared.database import Base
from shared.models import (
    User,
    ReadingPassage,
    ReadingQuestion,
    ListeningSection,
    ListeningQuestion,
    WritingTask,
    Vocabulary,
    GrammarSkill,
    GrammarMistake,
    Milestone,
    DailyTask,
)
from shared.config import settings


def get_sync_engine():
    """Create a synchronous database engine using psycopg2."""
    sync_url = settings.database_url_sync
    return create_engine(sync_url, echo=False, future=True)


def create_tables(engine):
    """Create all tables synchronously."""
    Base.metadata.create_all(engine)


def seed_data(session: Session):
    """Seed all the initial data."""
    # Check if data already exists
    result = session.execute(select(User).limit(1)).scalar_one_or_none()
    if result:
        print("Database already seeded. Skipping...")
        return

    # ============ Default User ============
    user = User(
        id=1,
        name="Alex",
        email="alex@example.com",
        current_band=6.5,
        target_band=8.0,
        exam_date=date.today() + timedelta(days=60),
        daily_goal=5,
        tasks_completed=3,
        streak=12,
    )
    session.add(user)
    session.flush()

    # ============ Reading Passages ============
    passage1 = ReadingPassage(
        id=1,
        title="The Impact of Technology on Education",
        content="""Technology has revolutionized the way we approach education in the 21st century. From interactive whiteboards to online learning platforms, technological advancements have transformed traditional classroom settings into dynamic, interactive learning environments.

One of the most significant changes has been the emergence of online learning platforms. These platforms provide students with access to high-quality educational resources from anywhere in the world. Whether it's a student in a remote village or a professional seeking to upgrade their skills, online education has democratized learning in unprecedented ways.

The role of teachers has also evolved significantly. Rather than simply delivering information, educators now act as facilitators of learning, guiding students through personalized learning paths. Technology enables teachers to identify each student's strengths and weaknesses, allowing for targeted interventions and customized support.

However, the integration of technology in education is not without challenges. Concerns about screen time, digital divide, and the loss of human connection in learning are valid considerations that educators and policymakers must address. Studies have shown that while technology can enhance learning outcomes, it should complement rather than replace traditional teaching methods.

Looking ahead, the future of education will likely involve even greater integration of emerging technologies such as artificial intelligence, virtual reality, and augmented reality. These technologies have the potential to create immersive learning experiences that were previously unimaginable.

In conclusion, while technology has undoubtedly transformed education, the key to successful integration lies in finding the right balance between technological innovation and proven pedagogical approaches. The goal should always be to enhance student learning outcomes and prepare learners for the challenges of the future.""",
        word_count=287,
        difficulty="medium",
        source="IELTS Practice",
    )
    session.add(passage1)

    passage2 = ReadingPassage(
        id=2,
        title="Sustainable Urban Planning",
        content="""As urban populations continue to grow, cities face unprecedented challenges in managing resources, reducing environmental impact, and maintaining quality of life for their residents. Sustainable urban planning has emerged as a critical approach to address these complex issues.

At its core, sustainable urban planning involves designing cities that meet the needs of the present without compromising the ability of future generations to meet their own needs. This approach considers environmental, social, and economic factors in urban development decisions.

One key aspect of sustainable cities is efficient public transportation systems. By reducing reliance on private vehicles, cities can significantly decrease air pollution and greenhouse gas emissions. Amsterdam, Copenhagen, and Singapore are often cited as examples of cities that have successfully implemented comprehensive public transportation networks.

Green spaces play another crucial role in sustainable urban development. Parks, community gardens, and urban forests provide numerous benefits, including improved air quality, reduced urban heat island effect, and enhanced mental health for residents. Research has consistently shown that access to green spaces correlates with better health outcomes.

Energy-efficient building design is also gaining prominence in sustainable cities. Green buildings incorporate features such as solar panels, rainwater harvesting systems, and natural ventilation to reduce energy consumption. Many cities now mandate green building standards for new constructions.

The concept of the "15-minute city" has gained traction in recent years. This urban planning concept aims to ensure that essential services and amenities are accessible within a 15-minute walk or bike ride from any point in the city. This approach reduces the need for long commutes and fosters more community-oriented neighborhoods.

However, implementing sustainable urban planning practices faces numerous obstacles. Financial constraints, political will, and resistance to change from various stakeholders can hinder progress. Despite these challenges, the transition towards sustainable cities is essential for addressing climate change and creating livable urban environments for future generations.""",
        word_count=312,
        difficulty="hard",
        source="IELTS Practice",
    )
    session.add(passage2)
    session.flush()

    # ============ Reading Questions – Passage 1 ============
    for q in [
        ReadingQuestion(
            passage_id=1,
            question_text="Online learning platforms have made education accessible to people in remote areas.",
            question_type="true-false",
            correct_answer="true",
            explanation="The passage states that online platforms provide access to educational resources from anywhere in the world, including students in remote villages.",
        ),
        ReadingQuestion(
            passage_id=1,
            question_text="The passage suggests that technology should completely replace traditional teaching methods.",
            question_type="true-false",
            correct_answer="false",
            explanation="The passage states that technology should complement rather than replace traditional teaching methods.",
        ),
        ReadingQuestion(
            passage_id=1,
            question_text="According to the passage, what role do teachers play in the modern classroom?",
            question_type="multiple-choice",
            options=["Information deliverers", "Facilitators of learning", "Exam graders", "Textbook authors"],
            correct_answer="Facilitators of learning",
            explanation="The passage states that educators now act as facilitators of learning.",
        ),
        ReadingQuestion(
            passage_id=1,
            question_text="The future of education may involve greater integration of AI, virtual reality, and ______ reality.",
            question_type="fill-blank",
            correct_answer="augmented",
            explanation="The passage mentions these three emerging technologies as future possibilities.",
        ),
        ReadingQuestion(
            passage_id=1,
            question_text="The passage discusses concerns about screen time and digital divide.",
            question_type="true-false",
            correct_answer="true",
            explanation="The passage explicitly mentions concerns about screen time, digital divide, and loss of human connection.",
        ),
    ]:
        session.add(q)

    # ============ Reading Questions – Passage 2 ============
    for q in [
        ReadingQuestion(
            passage_id=2,
            question_text="What is the main focus of sustainable urban planning?",
            question_type="multiple-choice",
            options=[
                "Building more skyscrapers",
                "Meeting present needs without compromising future generations",
                "Increasing private vehicle usage",
                "Prioritizing economic growth over environmental concerns",
            ],
            correct_answer="Meeting present needs without compromising future generations",
            explanation="The passage defines sustainable urban planning as meeting present needs without compromising future generations.",
        ),
        ReadingQuestion(
            passage_id=2,
            question_text="The '15-minute city' concept aims to make essential services accessible within a short walk or bike ride.",
            question_type="true-false",
            correct_answer="true",
            explanation="The passage explicitly describes this concept.",
        ),
    ]:
        session.add(q)

    # ============ Listening Section ============
    listening1 = ListeningSection(
        id=1,
        title="Academic Lecture: Climate Change and Ocean Currents",
        audio_url="/audio/sample-listening.mp3",
        duration=420,
        transcript="""Good morning, everyone. Today I'd like to talk about the relationship between climate change and ocean currents.

As you may know, ocean currents play a crucial role in regulating Earth's climate. They transport heat from the equator towards the poles, helping to distribute warmth around our planet.

However, recent studies have shown that climate change is significantly impacting these ocean currents. Rising sea temperatures are causing changes in water density, which in turn affects how currents flow.

One particularly concerning phenomenon is the slowing of the Atlantic Meridional Overturning Circulation, often called AMOC. This circulation system helps transport warm water from the tropics to the North Atlantic.

Scientists have observed that the AMOC is at its weakest point in over a thousand years. This could have severe consequences for weather patterns in Europe and North America.

But it's not all bad news. Research is ongoing to better understand these complex systems, and some proposed solutions include reducing greenhouse gas emissions and protecting marine ecosystems.

In conclusion, understanding the relationship between climate change and ocean currents is essential for predicting and mitigating future environmental changes. Thank you.""",
        difficulty="medium",
    )
    session.add(listening1)
    session.flush()

    for q in [
        ListeningQuestion(
            section_id=1,
            question_text="According to the lecture, what role do ocean currents play in Earth's climate?",
            question_type="multiple-choice",
            options=[
                "They trap heat in the atmosphere",
                "They transport heat from equator to poles",
                "They cause climate change",
                "They prevent rainfall",
            ],
            correct_answer="They transport heat from equator to poles",
            explanation="The lecturer states that ocean currents transport heat from the equator towards the poles.",
        ),
        ListeningQuestion(
            section_id=1,
            question_text="The slowing of the ______ circulation is a particular concern for scientists.",
            question_type="fill-blank",
            correct_answer="AMOC",
            explanation="The lecture specifically mentions the Atlantic Meridional Overturning Circulation (AMOC).",
        ),
        ListeningQuestion(
            section_id=1,
            question_text="The lecturer suggests that the AMOC is currently stronger than it has been in recent history.",
            question_type="true-false",
            correct_answer="false",
            explanation="The lecture states that the AMOC is at its weakest point in over a thousand years.",
        ),
        ListeningQuestion(
            section_id=1,
            question_text="What solution did the lecturer mention for addressing these issues?",
            question_type="multiple-choice",
            options=[
                "Building more power plants",
                "Reducing greenhouse gas emissions",
                "Increasing ocean shipping",
                "Mining the ocean floor",
            ],
            correct_answer="Reducing greenhouse gas emissions",
            explanation="The lecturer mentions reducing greenhouse gas emissions as one of the proposed solutions.",
        ),
    ]:
        session.add(q)

    # ============ Writing Task ============
    session.add(WritingTask(
        id=1,
        task_type="task_2",
        prompt="Some people believe that unpaid community service should be a compulsory part of high school programs. To what extent do you agree or disagree?",
        description="Write an essay discussing the advantages and disadvantages of making community service mandatory for high school students.",
        min_words=250,
        band_descriptor="Band 7-8: presents a clear position; develops ideas with relevant examples; uses cohesion effectively",
    ))

    # ============ Vocabulary ============
    for v in [
        Vocabulary(
            user_id=1, word="ubiquitous", pronunciation="/juːˈbɪkwɪtəs/",
            meaning="present, appearing, or found everywhere",
            definition="existing or being everywhere at the same time",
            examples=["Smartphones have become ubiquitous in modern society.", "The ubiquitous coffee shop chain can be found on every corner."],
            synonyms=["omnipresent", "pervasive", "universal", "widespread"],
            antonyms=["rare", "scarce", "uncommon"],
            collocations=["ubiquitous presence", "ubiquitous technology"],
            word_family=["ubiquitously", "ubiquity"],
            cefr="C2", ielts_frequency=8, mastery="learning",
            next_review=date.today() + timedelta(days=2),
        ),
        Vocabulary(
            user_id=1, word="mitigate", pronunciation="/ˈmɪtɪɡeɪt/",
            meaning="make less severe, serious, or painful",
            definition="to make less severe, harmful, or unpleasant",
            examples=["Measures to mitigate climate change effects are crucial.", "The government introduced policies to mitigate economic downturn."],
            synonyms=["alleviate", "reduce", "lessen", "diminish"],
            antonyms=["aggravate", "exacerbate", "worsen"],
            collocations=["mitigate effects", "mitigate damage", "mitigate risks"],
            word_family=["mitigation", "mitigating"],
            cefr="C2", ielts_frequency=7, mastery="new",
            next_review=date.today() + timedelta(days=1),
        ),
        Vocabulary(
            user_id=1, word="scrutinize", pronunciation="/ˈskruːtɪnaɪz/",
            meaning="examine or inspect closely and thoroughly",
            definition="to examine or inspect closely and thoroughly",
            examples=["The auditors will scrutinize the company's financial records.", "Scientists scrutinize the data for any anomalies."],
            synonyms=["examine", "inspect", "investigate", "analyze"],
            antonyms=["glance", "skim", "overlook"],
            collocations=["closely scrutinize", "undergo scrutiny"],
            word_family=["scrutiny", "scrutinizing"],
            cefr="C1", ielts_frequency=6, mastery="mastered",
        ),
        Vocabulary(
            user_id=1, word="eloquent", pronunciation="/ˈeləkwənt/",
            meaning="fluent or persuasive in speaking or writing",
            definition="fluent or persuasive in speaking or writing",
            examples=["She gave an eloquent speech at the conference.", "The article was an eloquent plea for environmental protection."],
            synonyms=["articulate", "expressive", "fluent", "persuasive"],
            antonyms=["inarticulate", "tongue-tied"],
            collocations=["eloquent speaker", "eloquent speech"],
            word_family=["eloquently", "eloquence"],
            cefr="B2", ielts_frequency=5, mastery="learning",
            next_review=date.today() + timedelta(days=3),
        ),
        Vocabulary(
            user_id=1, word="paradigm", pronunciation="/ˈpærədaɪm/",
            meaning="a typical example or pattern of something",
            definition="a typical example or pattern of something; a model",
            examples=["This discovery represents a paradigm shift in scientific thinking.", "The company's success created a new business paradigm."],
            synonyms=["model", "pattern", "example", "standard"],
            antonyms=["exception", "anomaly"],
            collocations=["paradigm shift", "new paradigm"],
            word_family=["paradigmatic"],
            cefr="C1", ielts_frequency=7, mastery="new",
        ),
        Vocabulary(
            user_id=1, word="pragmatic", pronunciation="/præɡˈmætɪk/",
            meaning="dealing with things sensibly and realistically",
            definition="dealing with things in a practical way rather than based on theories",
            examples=["We need a pragmatic approach to solve this problem.", "The pragmatic solution saved both time and money."],
            synonyms=["practical", "realistic", "sensible"],
            antonyms=["idealistic", "impractical"],
            collocations=["pragmatic approach", "pragmatic solution"],
            word_family=["pragmatically", "pragmatism"],
            cefr="B2", ielts_frequency=6, mastery="learning",
            next_review=date.today() + timedelta(days=4),
        ),
    ]:
        session.add(v)

    # ============ Grammar Skills ============
    grammar_skills_data = [
        ("Articles", "Definite, indefinite, and zero articles", 75, 8),
        ("Tenses", "Present, past, and future tenses", 65, 15),
        ("Passive Voice", "Forming and using passive constructions", 60, 12),
        ("Conditionals", "Zero, first, second, third, and mixed conditionals", 55, 18),
        ("Relative Clauses", "Defining and non-defining relative clauses", 70, 10),
        ("Modal Verbs", "Ability, possibility, permission, obligation", 80, 5),
        ("Comparison", "Comparatives, superlatives, and equality", 68, 11),
        ("Linking Words", "Conjunctions and discourse markers", 72, 9),
    ]

    grammar_skills = []
    for name, desc, mastery_pct, mistakes in grammar_skills_data:
        skill = GrammarSkill(
            user_id=1,
            skill_name=name,
            description=desc,
            mastery=mastery_pct,
            mistake_count=mistakes,
            last_practiced=datetime.utcnow() - timedelta(days=2),
        )
        session.add(skill)
        grammar_skills.append(skill)
    session.flush()

    # Grammar Mistakes
    mistakes_data = [
        (0, "I went to school yesterday.", "I went to school yesterday.", "Certain institutions don't need articles when referring to general purpose.", "reading"),
        (1, "I have seen that movie yesterday.", "I saw that movie yesterday.", "Use simple past for completed actions at specific past times.", "listening"),
        (2, "The letter was sent yesterday by John.", "The letter was sent by John yesterday.", "Place time expressions at the end of the sentence.", "writing"),
        (3, "If I would have money, I would buy a car.", "If I had money, I would buy a car.", "Use past simple (not would) in the if-clause for second conditional.", "writing"),
        (4, "The book which I told you, is very interesting.", "The book I told you about is very interesting.", "Use 'which/that' only when the relative clause is essential.", "reading"),
        (6, "She is more intelligent than any student in the class.", "She is more intelligent than any other student in the class.", "Use 'any other' when comparing within the same group.", "writing"),
    ]
    for idx, incorrect, correct, explanation, source in mistakes_data:
        session.add(GrammarMistake(
            skill_id=grammar_skills[idx].id,
            incorrect_sentence=incorrect,
            correct_sentence=correct,
            explanation=explanation,
            source=source,
        ))

    # ============ Milestones ============
    for band, title, desc, status in [
        (6.5, "Intermediate Plus", "You can communicate and understand complex ideas with some fluency.", "current"),
        (7.0, "Advanced", "You can handle complex topics and maintain coherence.", "locked"),
        (7.5, "Advanced Plus", "You can use advanced vocabulary and complex structures accurately.", "locked"),
        (8.0, "Expert", "You can communicate with complete fluency and accuracy.", "locked"),
    ]:
        session.add(Milestone(
            user_id=1, band=band, title=title, description=desc, status=status,
            skills={
                "grammar": round(70 + (band - 6.5) * 10),
                "vocabulary": round(65 + (band - 6.5) * 10),
                "reading": round(75 + (band - 6.5) * 10),
                "listening": round(70 + (band - 6.5) * 10),
                "speaking": round(60 + (band - 6.5) * 10),
                "writing": round(65 + (band - 6.5) * 10),
            },
        ))

    # ============ Daily Tasks ============
    for title, skill, completed in [
        ("Complete 2 reading passages", "reading", True),
        ("Practice 10 vocabulary words", "vocabulary", True),
        ("Listen to a podcast and take notes", "listening", True),
        ("Record a 2-minute speaking response", "speaking", False),
        ("Write an essay and get AI feedback", "writing", False),
    ]:
        session.add(DailyTask(
            user_id=1, title=title, skill=skill,
            completed=completed, date=date.today(),
        ))

    session.commit()
    print("Database seeded successfully!")


def main():
    """Main entry point (synchronous)."""
    print("Creating tables...")
    engine = get_sync_engine()
    create_tables(engine)
    print("Seeding data...")
    with Session(engine) as session:
        seed_data(session)


if __name__ == "__main__":
    main()
