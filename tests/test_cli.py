from app.cli import main


def test_ask_without_a_question_is_rejected() -> None:
    assert main(["ask"]) == 2
