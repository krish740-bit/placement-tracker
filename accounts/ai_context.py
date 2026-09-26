from .models import Subject, Topic, Question, Note, Goal


def build_user_context(user):
    subjects = Subject.objects.filter(user=user)

    context = []

    total_questions = 0
    total_solved = 0
    total_revision = 0

    for subject in subjects:
        context.append(f"\nSubject: {subject.name}")

        topics = Topic.objects.filter(subject=subject)

        for topic in topics:
            questions = Question.objects.filter(topic=topic)

            total = questions.count()
            solved = questions.filter(solved=True).count()
            revision = questions.filter(needs_revision=True).count()

            total_questions += total
            total_solved += solved
            total_revision += revision

            context.append(
                f"  Topic: {topic.name} | "
                f"Questions: {total} | "
                f"Solved: {solved} | "
                f"Marked for Revision: {revision}"
            )

    context.insert(
        0,
        f"""OVERALL PROGRESS:
Total questions: {total_questions}
Total solved: {total_solved}
Questions marked for revision: {total_revision}
""",
    )

    notes = Note.objects.filter(user=user)

    if notes.exists():
        context.append("\nNOTES:")

        for note in notes:
            context.append(f"  {note.title}: {note.content[:500]}")

    goals = Goal.objects.filter(user=user)

    if goals.exists():
        context.append("\nGOALS:")

        for goal in goals:

            if goal.topic:
                questions = Question.objects.filter(
                    topic=goal.topic, topic__subject__user=user
                )

                scope = f"Topic: {goal.topic.name}"

            elif goal.subject:
                questions = Question.objects.filter(
                    topic__subject=goal.subject, topic__subject__user=user
                )

                scope = f"Subject: {goal.subject.name}"

            else:
                questions = Question.objects.filter(topic__subject__user=user)

                scope = "All tracked subjects"

            completed = questions.filter(solved=True).count()

            context.append(
                f"  Goal: {goal.title} | "
                f"Scope: {scope} | "
                f"Completed: {completed} | "
                f"Target: {goal.target}"
            )

    return "\n".join(context)
