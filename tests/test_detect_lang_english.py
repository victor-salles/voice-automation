"""Tests for English language detection."""
from detect_lang import detect


def test_detect_returns_en_for_simple_english_sentence():
    assert detect("Hello world") == "en"


def test_detect_returns_en_for_english_phrase_with_the():
    assert detect("The cat is here") == "en"


def test_detect_returns_en_for_english_phrase_with_is():
    assert detect("This is good") == "en"


def test_detect_returns_en_for_english_phrase_with_are():
    assert detect("They are happy") == "en"


def test_detect_returns_en_for_english_phrase_with_was():
    assert detect("It was raining") == "en"


def test_detect_returns_en_for_english_phrase_with_were():
    assert detect("We were there") == "en"


def test_detect_returns_en_for_english_phrase_with_have():
    assert detect("I have a dog") == "en"


def test_detect_returns_en_for_english_phrase_with_has():
    assert detect("He has a car") == "en"


def test_detect_returns_en_for_english_phrase_with_had():
    assert detect("She had gone") == "en"


def test_detect_returns_en_for_english_phrase_with_been():
    assert detect("I have been there") == "en"


def test_detect_returns_en_for_english_phrase_with_will():
    assert detect("I will go soon") == "en"


def test_detect_returns_en_for_english_phrase_with_would():
    assert detect("I would like that") == "en"


def test_detect_returns_en_for_english_phrase_with_could():
    assert detect("You could try") == "en"


def test_detect_returns_en_for_english_phrase_with_should():
    assert detect("You should go") == "en"


def test_detect_returns_en_for_english_phrase_with_can():
    assert detect("I can do it") == "en"


def test_detect_returns_en_for_english_phrase_with_this():
    assert detect("This is mine") == "en"


def test_detect_returns_en_for_english_phrase_with_that():
    assert detect("That looks good") == "en"


def test_detect_returns_en_for_english_phrase_with_these():
    assert detect("These are good") == "en"


def test_detect_returns_en_for_english_phrase_with_those():
    assert detect("Those are far") == "en"


def test_detect_returns_en_for_english_phrase_with_there():
    assert detect("There is a bug") == "en"


def test_detect_returns_en_for_english_phrase_with_their():
    assert detect("Their house is big") == "en"


def test_detect_returns_en_for_english_phrase_with_they():
    assert detect("They went home") == "en"


def test_detect_returns_en_for_english_phrase_with_them():
    assert detect("I saw them") == "en"


def test_detect_returns_en_for_english_phrase_with_with():
    assert detect("Come with me") == "en"


def test_detect_returns_en_for_english_phrase_with_from():
    assert detect("I came from here") == "en"


def test_detect_returns_en_for_english_phrase_with_into():
    assert detect("Go into the room") == "en"


def test_detect_returns_en_for_english_phrase_with_which():
    assert detect("Which one is it") == "en"


def test_detect_returns_en_for_english_phrase_with_when():
    assert detect("When will you come") == "en"


def test_detect_returns_en_for_english_phrase_with_where():
    assert detect("Where are you") == "en"


def test_detect_returns_en_for_english_phrase_with_what():
    assert detect("What is that") == "en"


def test_detect_returns_en_for_english_phrase_with_while():
    assert detect("While you wait") == "en"


def test_detect_returns_en_for_english_phrase_with_because():
    assert detect("Because I said so") == "en"


def test_detect_returns_en_for_english_phrase_with_then():
    assert detect("Then we left") == "en"


def test_detect_returns_en_for_english_phrase_with_than():
    assert detect("Better than before") == "en"


def test_detect_returns_en_for_english_phrase_with_being():
    assert detect("Being here is nice") == "en"


def test_detect_returns_en_for_english_phrase_with_does():
    assert detect("He does it well") == "en"


def test_detect_returns_en_for_english_phrase_with_did():
    assert detect("I did my best") == "en"


def test_detect_returns_en_for_english_phrase_with_not():
    assert detect("I will not go") == "en"


def test_detect_returns_en_for_english_phrase_with_but():
    assert detect("But I disagree") == "en"


def test_detect_returns_en_for_english_phrase_with_and():
    assert detect("You and I") == "en"


def test_detect_returns_en_for_english_phrase_with_for():
    assert detect("This is for you") == "en"


def test_detect_returns_en_for_english_phrase_with_you():
    assert detect("I love you") == "en"


def test_detect_returns_en_for_english_phrase_with_your():
    assert detect("Your book is here") == "en"


def test_detect_returns_en_for_real_english_sentence_1():
    assert detect("Hello, how are you today?") == "en"


def test_detect_returns_en_for_real_english_sentence_2():
    assert detect("I have been working on this project for months.") == "en"


def test_detect_returns_en_for_real_english_sentence_3():
    assert detect("The weather is nice, and I want to go for a walk.") == "en"


def test_detect_returns_en_for_uppercase_english_text():
    assert detect("HELLO WORLD") == "en"


def test_detect_returns_en_for_mixed_case_english_text():
    assert detect("Hello World This Is Good") == "en"


def test_detect_returns_en_for_english_with_numbers():
    assert detect("I have 42 apples") == "en"


def test_detect_returns_en_for_english_with_punctuation():
    assert detect("Hello! How are you? I'm fine.") == "en"
