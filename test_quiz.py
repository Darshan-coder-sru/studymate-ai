import asyncio
from memory import generate_quiz

async def main():
    quiz = await generate_quiz(dataset_name="Physics", num_questions=3)
    print(quiz)

asyncio.run(main())