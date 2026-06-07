import pytest

from bot import DRINKS_PATTERN


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
