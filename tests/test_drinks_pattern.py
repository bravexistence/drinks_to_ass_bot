import pytest

from bot import DRINKS_PATTERN, is_drinks_mention


@pytest.mark.parametrize(
    "text",
    [
        "напиток",
        "Напиток",
        "НАПИТОК",
        "напитка",
        "напитку",
        "напитком",
        "напитке",
        "напитки",
        "Напитки",
        "напитков",
        "напиткам",
        "напитками",
        "напитках",
        "напиточек",
        "напиточки",
        "напиточка",
        "Хочу напитки!",
        "а у нас есть какие-нибудь напитки?",
        "Принёс напитков на всех",
        "в этом напитке слишком много сахара",
        "купил два напиточка",
    ],
)
def test_pattern_matches(text: str) -> None:
    assert DRINKS_PATTERN.search(text), f"должно матчиться: {text!r}"


@pytest.mark.parametrize(
    "text",
    [
        "",
        "привет",
        "напитанный кровью",
        "напитать землю влагой",
        "напильник лежит в гараже",
        "drink some water",
        "Питон лучший язык",
    ],
)
def test_pattern_does_not_match(text: str) -> None:
    assert not DRINKS_PATTERN.search(text), f"не должно матчиться: {text!r}"


@pytest.mark.parametrize(
    "text",
    [
        # Polный транслит
        "Napitki",
        "napitki",
        "NAPITKI",
        "napitok",
        "Napitkov na vseh",
        "kupil napitochek",
        # Визуальные подмены (буква-омоглиф)
        "нaпитки",  # Latin a
        "Hапитки",  # Latin H
        "Нaпитки",  # Latin a в середине
        "напитkи",  # Latin k
        "напиtки",  # Latin t
        "напитки и закуски",  # норм случай тоже должен пройти
        # Смесь
        "HAПИТКИ",  # H Latin, остальное кириллица
        "Кто-нибудь принесёт Napitki?",  # транслит внутри русского предложения
    ],
)
def test_is_drinks_mention_handles_obfuscation(text: str) -> None:
    assert is_drinks_mention(text), f"должно матчиться: {text!r}"


@pytest.mark.parametrize(
    "text",
    [
        "",
        "Hi everyone",  # фонетически → 'хи евер...' но без напит
        "drink water please",
        "I like python",
        "напильник",
        "Каждый имеет своё мнение",
    ],
)
def test_is_drinks_mention_no_false_positives(text: str) -> None:
    assert not is_drinks_mention(text), f"не должно матчиться: {text!r}"
