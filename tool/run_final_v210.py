from pathlib import Path

source_path = Path('tool/patch_final_v210.py')
source = source_path.read_text(encoding='utf-8')
source = source.replace("    excel_block,\n    text,", "    lambda _: excel_block,\n    text,")
source = source.replace("flashcards + \"class QuizSetupPage\", text", "lambda _: flashcards + \"class QuizSetupPage\", text")
source = source.replace("word_card + \"void push(BuildContext context\", text", "lambda _: word_card + \"void push(BuildContext context\", text")
exec(compile(source, str(source_path), 'exec'))
