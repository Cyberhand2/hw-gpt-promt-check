import os
import re
from openai import OpenAI
import threading
import time
import pandas as pd

api_key = "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"
assistant_id = "asst_8jlgzAibxBL0m6RS71GQenk8"


def compare_results():
    # Исправление сепаратора и указание корректного обработчика для скобок
    results_df = pd.read_csv('results.txt', sep=" ", names=['ID', 'Status', 'Extra'], header=None, engine='python')
    results_df['Extra'] = results_df['Extra'].str.extract(r'\((.*?)\)', expand=False).fillna('')

    mentors_df = pd.read_csv('mentors-results.txt', sep=" ", names=['ID', 'Status', 'Extra'], header=None,
                             engine='python')
    mentors_df['Extra'] = mentors_df['Extra'].str.extract(r'\((.*?)\)', expand=False).fillna('')

    # Объединение результатов для сравнения
    comparison_df = pd.merge(results_df, mentors_df, on="ID", suffixes=('_Machine', '_Mentor'))

    print(comparison_df)

def process_homework(homework_id, homework_text):
    try:
        client = OpenAI(api_key=api_key)
        thread = client.beta.threads.create()

        message = client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=homework_text
        )

        run = client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=assistant_id
        )

        # Wait for the Run to be completed
        while True:
            run_status = client.beta.threads.runs.retrieve(
                thread_id=thread.id,
                run_id=run.id
            )
            if run_status.status == "completed":
                break
            time.sleep(0.5)  # Wait before checking again

        response_messages = client.beta.threads.messages.list(
            thread_id=thread.id
        )

        # Extract the first message's text content
        last_message_str = str(response_messages.data[0].content[0].text)
        last_message = last_message_str.replace('\n', '')

        # Check if accepted
        is_accepted = "принята" if 'is_accepted=1' in last_message else "не принята" if 'is_accepted=0' in last_message else None

        # Pattern to match "task_is_not_complete(1,2,3)"
        pattern = r"task_is_not_complete\((.*?)\)"
        matches = re.search(pattern, last_message)

        task_incomplete_args = matches.group(1) if matches else ""

        # Write to the results file with conditions matched
        with open('results.txt', 'a') as file:
            file.write(f'{homework_id} {is_accepted} ({task_incomplete_args})\n')
    except Exception as e:
        print(f"error from task =   {homework_id}: {e}")

def main() -> None:
    threads = []

    with open('homeworks.txt', 'r') as file:
        homeworks_content = file.read()

    for homework_block in homeworks_content.split('\n'):
        if homework_block.strip() != "":
            homework_parts = homework_block.strip().split('\t', 1)
            homework_id = homework_parts[0]
            homework_text = homework_parts[1] if len(homework_parts) > 1 else ""

            thread = threading.Thread(target=process_homework, args=(homework_id, homework_text.strip()))
            threads.append(thread)
            thread.start()

    for thread in threads:
        thread.join()

    # After processing all homeworks, compare results with mentor's results
    #    compare_results()



if __name__ == '__main__':
    main()