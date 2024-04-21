#!/usr/bin/env python
"""Create a list of prompts from a context-free grammar and string templates.

Converted from Jupyter notebook to executable.
"""

import argparse
import json
import random
from string import Template

from nltk import CFG
from nltk.parse.generate import generate


def load_json(name):
    """Load prompt parts."""
    with open(f"prompt_parts/{name}.json") as fh:
        return json.load(fh)


def get_identifiers(template):
    """Get identifiers in a string template.

    See # https://github.com/python/cpython/issues/90465
    """
    return list(
        set(
            filter(
                lambda v: v is not None,
                (mo.group('named') or mo.group('braced')
                 for mo in template.pattern.finditer(template.template))
            )
        )
    )


def make_grammar(grammar_tpl_str):
    """Convert template string to CFG."""
    grammar = CFG.fromstring(grammar_tpl_str)
    return grammar


def join_text(tokens):
    r = []
    for t in tokens:
        if r and t and (t[0].isalnum() or t[0] in "$`"):
            r.append(" ")
        t = t.replace('`', '"')
        r.append(t)
    return "".join(r)


def capitalize_sentence(text):
    return text[0].upper() + text[1:]


def random_prompt_from_type(_type, prompts_dict):
    _prompts_subset = prompts_dict[_type]
    prompt_tpl = Template(join_text(random.choice(_prompts_subset)))
    ids = get_identifiers(prompt_tpl)
    id_kws = {}
    for _id in ids:
        id_list = prompts_dict[_id]
        try:
            id_kws[_id] = random.choice(id_list)
        except Exception:
            print(_id, ids)
            raise
    prompt = prompt_tpl.substitute(**id_kws)
    return prompt


def mutate_prompt(prompt, _type, prompts_dict):
    prefix = random.random()
    if prefix < 0.05:
        prompt = "Please " + prompt[0].lower() + prompt[1:]
    elif prefix < 0.06:
        command = random.choice(commands)
        if not prompt.lower().startswith(command):
            prompt = command.capitalize() + ": " + prompt[0].lower() + prompt[1:]

    if _type not in ["other_prompts"]:
        phrase = random.random()

        if phrase < 0.01:
            preserve = random_prompt_from_type("preserve_prompts", prompts_dict)
            prompt = prompt + " " + preserve
        elif phrase < 0.02:
            preserve = random_prompt_from_type("keep_quality_prompts", prompts_dict)
            prompt = prompt + " " + preserve

    stops = [".", "...", "!"]
    s = random.choices(stops, weights=[48, 1, 1])[0]
    prompt = prompt + s

    return prompt


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--sample_size", type=int, default=10000)
    args = parser.parse_args()

    code = load_json("code")
    constrain_words = load_json("constrain_words")
    mostly_fictional = load_json("mostly_fictional")
    other_media = load_json("other_media")
    tone = load_json("tone")
    to_inject = load_json("to_inject")
    to_replace = load_json("to_replace")
    qualities = load_json("qualities")
    things = load_json("things")
    authors = load_json("authors")
    accents = load_json("accents")
    themes = load_json("themes")

    nouns_catchy = load_json("nouns_catchy")
    nouns_mathy = load_json("nouns_mathy")
    nouns_everyday = load_json("nouns_everyday")

    nouns = nouns_catchy + nouns_mathy + nouns_everyday

    rephrase_1 = ["reformulate", "rewrite", "reimagine", "recreate", "rephrase", "paraphrase", "update"]
    commands = rephrase_1.copy()
    text = ["text", "article", "passage", "piece of text"]

    FICTION_TPL = """
    SENTENCE -> CONV
    CONV -> CONVI | CONVA
    CONVI -> CWI TT INTO CONVTEXT
    CONVA -> CWA TT AS CONVTEXT
    AS -> "as" | "in the style of" | "using the tone and structure of" | "as if it were"
    INTO -> "to" | "into"
    TT -> "this $text" | "this" | "it" | "the $text above" | "the $text"
    CWI -> "convert" | "transform" | "make" | "turn" | "remake"
    CWA -> "express" | "present" | "$rephrase_1"
    CONVTEXT -> "$mostly_fictional"
    """

    grammar_fiction = make_grammar(FICTION_TPL)
    fiction_prompts = list(generate(grammar_fiction))

    MEDIUM_TPL = """
    SENTENCE -> CONV
    CONV -> CONVI | CONVA
    CONVI -> CWI TT INTO CONVTEXT
    CONVA -> CWA TT AS CONVTEXT
    AS -> "as" | "in the style of" | "using the tone and structure of" | "as if it were"
    INTO -> "to" | "into"
    TT -> "this $text" | "this" | "it" | "the $text above" | "the $text" | "the above $text"
    CWI -> "convert" | "transform" | "make" | "turn" | "remake"
    CWA -> "express" | "present" | "$rephrase_1"
    CONVTEXT -> "$other_media"
    """

    grammar_new_medium = make_grammar(MEDIUM_TPL)
    new_medium_prompts = list(generate(grammar_new_medium))

    AUTHOR_TPL = """
    SENTENCE -> CONVA | CONVB | CONVC
    
    CONVA -> CWA TT WITH "the" STYLE "of" AUTHOR
    CONVB -> CWA TT AS AUTHOR
    CONVC -> CWA TT AS AUTHOR "'s" STYLE
    
    AS -> "as if it was written by" | "copying" | "in a way that imitates" | "as a tribute to" | "mimicking"
    WITH -> "with" | "borrowing" | "imitating" | "copying" | "in a way inspired by"
    STYLE -> "writing style" | "prose" | "authoring technique" | "writing technique" | "writing"
    TT -> "this $text" | "this" | "it" | "the $text above" | "the $text" | "the above $text"
    CWA -> "$rephrase_1"
    AUTHOR -> "$authors"
    """

    grammar_author = make_grammar(AUTHOR_TPL)
    author_prompts = list(generate(grammar_author))

    TONE_TPL = """
    SENTENCE -> CONV
    CONV -> CONVM | CONVR
    CONVM -> CWM TT ADV
    CONVR -> CWR TT ADV_MANNER
    ADV -> ADV_MAIN TONE
    ADV_SUP -> "a bit" | "slightly" | ""
    ADV_MAIN -> ADV_SUP ADV_DIRECTION
    TONE -> "$tone"
    TT -> "this $text" | "this" | "it" | "the $text above" | "the $text"
    CWM -> "make"
    CWR -> "reformulate" | "rewrite" | "express" | "present" | "recreate" | "articulate" | "re-generate" | "reconstruct" | "rephrase"
    TONE_WORD -> "tone" | "manner" | "style" | "way" | "fashion" | "approach"
    ADV_MANNER -> "in a" TONE TONE_WORD
    """

    grammar_tone = make_grammar(TONE_TPL)
    tone_prompts = list(generate(grammar_tone))

    random.choices(tone_prompts, k=10)

    INJECT_TPL = """
    SENTENCE -> CONVI | CONVR
    CONVI -> CONVINJ | CONVADD
    CONVINJ -> CWI INJECT INTO TT
    CONVADD -> CWA INJECT "to" TT
    CONVR -> CWR TT "with" INJECT ADDED
    
    
    TT -> "this $text" | "this" | "it" | "the $text above" | "the $text" | "the above $text"
    CWI -> "inject" | "incorporate" | "insert" | "instill"
    CWA -> "add" | "append"
    CWR -> "reformulate" | "rewrite" | "present" | "recreate" | "re-generate" | "reconstruct" | "rephrase" | "remake"
    INJECT -> "$to_inject" | THEWORD "`$nouns`" | THETHEME
    THETHEME -> "the theme of $themes" | "$themes" | "themes of $themes"
    THEWORD -> "the word" | "the noun"
    INTO -> "inside" | "in" | "into" | "to"
    ADDED -> "added" | "injected to it" | "inserted" | "attached" | "imbued to it" | "shoehorned into it" | "forced into it" | "taking the center" | "being featured"
    
    """

    grammar_inject = make_grammar(INJECT_TPL)
    inject_prompts = list(generate(grammar_inject))
    random.choices(inject_prompts, k=50)

    REPLACE_TPL = """
    SENTENCE -> CONV | REP
    REP -> CWR EVERY TO_REPLACE "in" TT WITH SOMETHING
    CONV -> CWC EVERY TO_REPLACE "in" TT INTO SOMETHING
    CWR -> "replace" | "substitute" | "swap" | "exchange"
    CWC -> "convert" | "transform"
    EVERY -> "every"
    TO_REPLACE -> "$to_replace"
    SOMETHING -> THING | THEWORD "`$nouns`"
    THEWORD -> "the word" | "the noun"
    THING -> "$things"
    TT -> "this $text" | "this" | "it" | "the $text above" | "the $text" | "the above $text"
    WITH -> with
    INTO -> "into" | "to"
    """

    grammar_replace = make_grammar(REPLACE_TPL)
    replace_prompts = list(generate(grammar_replace))
    random.choices(replace_prompts, k=10)

    SUMMARIZE_TPL = """
    SENTENCE -> SUM
    SUM -> CWS TT
    CWS -> "summarize" | "shorten" | "condense" | "sum up" | MS
    MS -> MAKE "a summary of"
    MAKE -> "make" | "create" | "write" | "generate" | "give me"
    TT -> "this $text" | "this" | "it" | "the $text above" | "the $text" | "the above $text"
    """

    grammar_summary = make_grammar(SUMMARIZE_TPL)
    summary_prompts = list(generate(grammar_summary))
    random.choices(summary_prompts, k=10)

    CODE_TPL = """
    SENTENCE -> TRANS | REF1 | REF2
    TRANS -> CWT TT TO CODE
    REF1 -> CWR TT AS "a" CODE FILE
    REF2 -> CWR TT IN CODE
    CWT -> "transform" | "translate" | "convert"
    CWR -> "rewrite" | "reformat" | "reconstruct" | "re-generate"
    TT -> "this $text" | "this" | "it" | "the $text above" | "the $text" | "the above $text"
    TO -> "to"
    IN -> "in"
    AS -> "as"
    FORM -> "code" | "format" | "file format"
    FILE -> "snippet" | "file"
    CODE -> "$code"
    """

    grammar_code = make_grammar(CODE_TPL)
    code_prompts = list(generate(grammar_code))
    random.choices(code_prompts, k=10)

    QUALITY_TPL = """
    SENTENCE -> CONV | CONV2
    CONV -> CWI TT QUALITY
    CONV2 -> CWI TT QUALITY "and" QUALITY
    INTO -> "to" | "into"
    TT -> "this $text" | "this" | "it" | "the $text above" | "the $text" | "the above $text"
    CWI -> "make"
    QUALITY -> "$qualities"
    """

    grammar_quality = make_grammar(QUALITY_TPL)
    quality_prompts = list(generate(grammar_quality))
    quality_prompts = [p for p in quality_prompts if len(p) < 4 or p[2] != p[4]]
    random.choices(quality_prompts, k=10)

    ACCENT_TPL = """
    SENTENCE -> CONV1
    CONV1 -> CWR TT IN ACCENT_NAME
    IN -> "in"
    TYP -> "typical" | "stereotypical" | "prominent" | "unmistakable" | "pronounced" | "obvious"
    TT -> "this $text" | "this" | "it" | "the $text above" | "the $text" | "the above $text"
    CWR -> "reformulate" | "rewrite" | "express" | "present" | "recreate" | "articulate" | "re-generate" | "reconstruct" | "rephrase" | "translate"
    ACCENT_NAME -> "$accents"
    ACCENT -> "dialect" | "accent"
    """

    grammar_accent = make_grammar(ACCENT_TPL)
    accent_prompts = list(generate(grammar_accent))
    random.choices(accent_prompts, k=10)

    PRESERVE_TPL = """
    PHRASE -> P1 | P2
    P1 -> WHILE PRESERVING "the" CORE "of" "the" ORIG "$text"
    P2 -> WHILE PRESERVING "the" TRUE IDEA BEHIND "the" ORIG "$text"
    WHILE -> "while"
    BEHIND -> "of" | "behind"
    PRESERVING -> "preserving" | "retaining" | "remaining faithful to" | "respecting" | "keeping" |  "upholding" | "staying true to" | "sticking to"
    TRUE -> "raw" | "core" | "original" | "true" | "primary" | "fundamental"
    IDEA -> "idea" | "meaning" | "context" | "message"
    CORE -> "meaning" | "core" | "spirit" | "true meaning" | "authenticity" | "core idea" | "actual content" | "core content" | "essence"
    ORIG -> "original" | "initial" | "actual" | "given" | "transformed"
    """

    grammar_preserve = make_grammar(PRESERVE_TPL)
    preserve_prompts = list(generate(grammar_preserve))
    random.choices(preserve_prompts, k=10)

    KEEP_QUALITY_TPL = """
    PHRASE -> P1
    P1 -> WHILE VERBING QUALITY "of the" ORIG "$text"
    WHILE -> "while" | "meanwhile" | "while at the same time"
    VERBING -> PRESERVING | IMPROVING
    PRESERVING -> "preserving" | "retaining" | "respecting" | "keeping" |  "upholding" | "protecting"
    IMPROVING -> "improving" | "enhancing"
    QUALITY -> "the quality" | "the overall quality" | "the stylistic quality" | "the logic and consistency" | "the coherence" | "the integrity"
    ORIG -> "original" | "initial" | "actual" | "given" | "transformed"
    """

    grammar_keep_quality = make_grammar(KEEP_QUALITY_TPL)
    keep_quality_prompts = list(generate(grammar_keep_quality))
    random.choices(keep_quality_prompts, k=10)

    prompt_weights = {c: 1 for c, v in locals().items() if c.endswith("prompts")}
    prompt_weights.keys()

    prompt_weights = {'tone_prompts': 45,
                      'inject_prompts': 20,
                      'replace_prompts': 20,
                      'summary_prompts': 5,
                      'code_prompts': 5,
                      'quality_prompts': 18,
                      'fiction_prompts': 20,
                      'new_medium_prompts': 80,
                      'author_prompts': 14,
                      'accent_prompts': 15
                      }

    prompts = []
    prompt_types = random.choices(list(prompt_weights.keys()), weights=list(prompt_weights.values()),
                                  k=args.sample_size)
    for _type in prompt_types:
        prompt = random_prompt_from_type(_type, locals())
        prompt = mutate_prompt(prompt, _type, locals())
        prompt = capitalize_sentence(prompt)

        prompts.append(prompt)

    prompts = list(set(prompts))
    with open("prompts_cfg.json", "w") as fh:
        json.dump(prompts, fh, indent=1)
