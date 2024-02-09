
# -*- coding: utf-8 -*-
import os
from openai import OpenAI
import threading
import time

api_key = "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"
assistant_id = "asst_8jlgzAibxBL0m6RS71GQenk8"

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

        last_message_str = str(response_messages.data[0].content[0].text)  # Преобразование объекта Text в строку
        last_message = last_message_str.replace('\n', '')
        is_accepted = "принята" if 'is_accepted=1' in last_message else "не принята" if 'is_accepted=0' in last_message else None

        with open('results.txt', 'a') as file:
            file.write(f'Домашка с ID {homework_id} {is_accepted} \n' )
    except Exception as e:
        print(f"error from task =   {homework_id}: {e}")

def main() -> None:
    threads = []

    with open('homeworks.txt', 'r') as file:
        homeworks_content = file.read()

    for homework_block in homeworks_content.split('---'):
        if homework_block.strip() != "":
            homework_parts = homework_block.strip().split('\n', 1)
            homework_id = homework_parts[0]
            homework_text = homework_parts[1] if len(homework_parts) > 1 else ""

            thread = threading.Thread(target=process_homework, args=(homework_id, homework_text.strip()))
            threads.append(thread)
            thread.start()

    for thread in threads:
        thread.join()

if __name__ == '__main__':
    main()
