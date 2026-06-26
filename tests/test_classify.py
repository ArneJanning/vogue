from vogue.model import Field
from vogue.disciplines.classify import Classifier


def test_default_humanities_and_stem():
    c = Classifier.default()
    assert c.classify("Literaturwissenschaft") is Field.HUMANITIES
    assert c.classify("Allgemeine und Vergleichende Sprachwissenschaft") is Field.HUMANITIES
    assert c.classify("Molekülchemie") is Field.PHYS
    assert c.classify("Grundlagen der Biologie und Medizin") is Field.LIFE


def test_unknown_when_no_rule_matches():
    c = Classifier.default()
    assert c.classify("") is Field.UNKNOWN
    assert c.classify("Völlig Unbekanntes Fach") is Field.UNKNOWN


def test_overrides_take_precedence():
    c = Classifier.default().with_overrides([{"match": "Psychologie", "field": "social"}])
    assert c.classify("Psychologie") is Field.SOCIAL
