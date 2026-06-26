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


def test_openalex_english_fields():
    c = Classifier.default()
    assert c.classify("Arts and Humanities") is Field.HUMANITIES
    assert c.classify("Social Sciences") is Field.SOCIAL
    assert c.classify("Economics, Econometrics and Finance") is Field.SOCIAL
    assert c.classify("Medicine") is Field.LIFE
    assert c.classify("Neuroscience") is Field.LIFE
    assert c.classify("Physics and Astronomy") is Field.PHYS
    assert c.classify("Chemistry") is Field.PHYS
    assert c.classify("Engineering") is Field.ENG
    assert c.classify("Computer Science") is Field.ENG
    assert c.classify("Materials Science") is Field.ENG
