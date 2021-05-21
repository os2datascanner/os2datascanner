import unittest

from os2datascanner.engine2.rules.cpr import CPRRule


content = """
@ Godtages fordi det er et valid cpr der opfylder Modulus 11 tjek.
Anders And 060521-4002
@ godtages fordi der indgår cpr i linjen
Anders And, cpr: [060521-4010
@ godtages fordi parenteser er balanceret
Anders And, [060521-4029], Paradisæblevej 111
@ godtages fordi der tillades ekstra ord ved parenteser.
Anders (060521-4037 And), Andeby
@ godtages ikke fordi foranstående ord er et tal, der IKKE opfylder kriterium for cpr
Anders And 113 060521-4045
@ godtages fordi bagvedstående/foranstående ord opfylder kriterium for cpr
Anders And 060521-4053 060521-4061

@ godtages ikke fordi foranstående ord er et mix af store og små bogstaver
"HOST/ABCD.intra.corp"], "uSNChanged": [060521-4088], "uSNCreated": [123456], "userAccountControl":
@ godtages ikke pga. omkringstående tal OG fordi kun to ord medtages, vil paranteser være ubalanceret.
712000 0 0 WET} {060521-4096 3600 1 WEST} [0605214118 0 0 WET]
@ godtages ikke pga foranstående er unær operatør(dvs. fortegns-minus. På eng: unary) eller specialsymbol
16768 0 LMT} {-060521-4126} {+060521-4134} (#060521-4142)

Følgende kriterier undersøges
- Kontekst består af de `n_words=2` foranstående/bagvedstående ord incl. tegn.
Ord med bindesteg(-), punktum(.) eller skråstreg(/) splittes ikke.
- Konteksten bruges til at estimere en sandsynlighed for at et 10-cifret nummer
der opfylder modulus 11, rent faktisk er et cpr-nummber.

Følgende heuristik benyttes
- indgår p-nr eller variant deraf noget sted i teksten
- Er der unær operator før eller efter, fx -060521-4150 eller 060521-4169+
- Er der ubalanceret symboler eller parenteser omkring, fx [060521-4177. Men [060521-4185] vil være ok.
- Kommer der et tal der ikke ligner et cpr før eller efter, fx 113 060521-4193
- Er ord før eller efter ikke ’alle små’-, ’stort begyndelsesbogstav’ eller ’alle caps’, fx uSNChanged 060521-4207
resulterer alle i sandsynlighed=0.

- indeholder ord før cpr, fx Anders cpr-nr [060521-4215]
resulterer i  sandsynlighed=1

Følgende symboler undersøges
- unær operatører "+", "-"
- parenteser "(", "[", "{", "<", "<?", "<%", "/*"
- symboler "!", "#", "%"
"""

# all possible matches
ALL_MATCHES = [
    {'offset': 79,
     'match': '0605XXXXXX',
     'context': 'alid cpr der opfylder Modulus 11 tjek.\nAnders And XXXXXX-XXXX\n@ godtages fordi der indgår cpr i linjen\nAnders A',
     'context_offset': 0,
     'sensitivity': None,
     'probability': 1.0},
    {'offset': 150,
     'match': '0605XXXXXX',
     'context': 's fordi der indgår cpr i linjen\nAnders And, cpr: [XXXXXX-XXXX\n@ godtages fordi parenteser er balanceret\nAnders ',
     'context_offset': 0,
     'sensitivity': None,
     'probability': 1.0},
    {'offset': 217,
     'match': '0605XXXXXX',
     'context': 'tages fordi parenteser er balanceret\nAnders And, [XXXXXX-XXXX], Paradisæblevej 111\n@ godtages fordi der tillade',
     'context_offset': 0,
     'sensitivity': None,
     'probability': 1.0},
    {'offset': 315,
     'match': '0605XXXXXX',
     'context': 'i der tillades ekstra ord ved parenteser.\nAnders (XXXXXX-XXXX And), Andeby\n@ godtages ikke fordi foranstående o',
     'context_offset': 0,
     'sensitivity': None,
     'probability': 1.0},
    {'offset': 441,
     'match': '0605XXXXXX',
     'context': 'er IKKE opfylder kriterium for cpr\nAnders And 113 XXXXXX-XXXX\n@ godtages fordi bagvedstående/foranstående ord o',
     'context_offset': 0,
     'sensitivity': None,
     'probability': 1.0},
    {'offset': 539,
     'match': '0605XXXXXX',
     'context': 'stående ord opfylder kriterium for cpr\nAnders And XXXXXX-XXXX XXXXXX-XXXX\n\n@ godtages ikke fordi foranstående o',
     'context_offset': 0,
     'sensitivity': None,
     'probability': 1.0},
    {'offset': 551,
     'match': '0605XXXXXX',
     'context': 'opfylder kriterium for cpr\nAnders And XXXXXX-XXXX XXXXXX-XXXX\n\n@ godtages ikke fordi foranstående ord er et mix',
     'context_offset': 0,
     'sensitivity': None,
     'probability': 1.0},
    {'offset': 679,
     'match': '0605XXXXXX',
     'context': 'bogstaver\n"HOST/ABCD.intra.corp"], "uSNChanged": [XXXXXX-XXXX], "uSNCreated": [123456], "userAccountControl":\n@',
     'context_offset': 0,
     'sensitivity': None,
     'probability': 1.0},
    {'offset': 859,
     'match': '0605XXXXXX',
     'context': 'vil paranteser være ubalanceret.\n712000 0 0 WET} {XXXXXX-XXXX 3600 1 WEST} [XXXXXX-XXXX 0 0 WET]\n@ godtages ikke',
     'context_offset': 0,
     'sensitivity': None,
     'probability': 1.0},
    {'offset': 885,
     'match': '0605XXXXXX',
     'context': 'ceret.\n712000 0 0 WET} {XXXXXX-XXXX 3600 1 WEST} [XXXXXX-XXXX 0 0 WET]\n@ godtages ikke pga foranstående er unær',
     'context_offset': 0,
     'sensitivity': None,
     'probability': 1.0},
    {'offset': 1026,
     'match': '0605XXXXXX',
     'context': 'På eng: unary) eller specialsymbol\n16768 0 LMT} {-XXXXXX-XXXX} {+XXXXXX-XXXX} (#XXXXXX-XXXX)\n\nFølgende kriterie',
     'context_offset': 0,
     'sensitivity': None,
     'probability': 1.0},
    {'offset': 1041,
     'match': '0605XXXXXX',
     'context': 'eller specialsymbol\n16768 0 LMT} {-XXXXXX-XXXX} {+XXXXXX-XXXX} (#XXXXXX-XXXX)\n\nFølgende kriterier undersøges\n- ',
     'context_offset': 0,
     'sensitivity': None,
     'probability': 1.0},
    {'offset': 1056,
     'match': '0605XXXXXX',
     'context': 'mbol\n16768 0 LMT} {-XXXXXX-XXXX} {+XXXXXX-XXXX} (#XXXXXX-XXXX)\n\nFølgende kriterier undersøges\n- Kontekst består',
     'context_offset': 0,
     'sensitivity': None,
     'probability': 1.0},
    {'offset': 1511,
     'match': '0605XXXXXX',
     'context': 'ksten\n- Er der unær operator før eller efter, fx -XXXXXX-XXXX eller XXXXXX-XXXX+\n- Er der ubalanceret symboler ',
     'context_offset': 0,
     'sensitivity': None,
     'probability': 1.0},
    {'offset': 1529,
     'match': '0605XXXXXX',
     'context': 'r operator før eller efter, fx -XXXXXX-XXXX eller XXXXXX-XXXX+\n- Er der ubalanceret symboler eller parenteser o',
     'context_offset': 0,
     'sensitivity': None,
     'probability': 1.0},
    {'offset': 1602,
     'match': '0605XXXXXX',
     'context': 'balanceret symboler eller parenteser omkring, fx [XXXXXX-XXXX. Men [XXXXXX-XXXX] vil være ok.\n- Kommer der et t',
     'context_offset': 0,
     'sensitivity': None,
     'probability': 1.0},
    {'offset': 1620,
     'match': '0605XXXXXX',
     'context': 'r eller parenteser omkring, fx [XXXXXX-XXXX. Men [XXXXXX-XXXX] vil være ok.\n- Kommer der et tal der ikke ligner',
     'context_offset': 0,
     'sensitivity': None,
     'probability': 1.0},
    {'offset': 1713,
     'match': '0605XXXXXX',
     'context': 'al der ikke ligner et cpr før eller efter, fx 113 XXXXXX-XXXX\n- Er ord før eller efter ikke ’alle små’-, ’stort',
     'context_offset': 0,
     'sensitivity': None,
     'probability': 1.0},
    {'offset': 1828,
     'match': '0605XXXXXX',
     'context': 'yndelsesbogstav’ eller ’alle caps’, fx uSNChanged XXXXXX-XXXX\nresulterer alle i sandsynlighed=0.\n\n- indeholder ',
     'context_offset': 0,
     'sensitivity': None,
     'probability': 1.0},
    {'offset': 1920,
     'match': '0605XXXXXX',
     'context': 'd=0.\n\n- indeholder ord før cpr, fx Anders cpr-nr [XXXXXX-XXXX]\nresulterer i  sandsynlighed=1\n\nFølgende symboler',
     'context_offset': 0,
     'sensitivity': None,
     'probability': 1.0}
]


class RuleTests(unittest.TestCase):
    def test_cpr_context(self):
        rules = [
            (
                CPRRule(modulus_11=True, ignore_irrelevant=False, examine_context=False,
                        blacklist=False),
                ALL_MATCHES,
                "match all"
            ),
            (
                CPRRule(modulus_11=True, ignore_irrelevant=False, examine_context=True,
                        blacklist=False),
                [ALL_MATCHES[i] for i in [0,1,2,3,5,6,19]],
                "match using context rules"
            ),
            (
                CPRRule(modulus_11=True, ignore_irrelevant=False, examine_context=True,
                        blacklist=False, whitelist=False),
                [ALL_MATCHES[i] for i in [0,2,3,5,6,19]],
                "match setting `whitelist=False`"
            ),
            (
                CPRRule(modulus_11=True, ignore_irrelevant=False, examine_context=True,
                        blacklist=True),
                [ALL_MATCHES[i] for i in []],
                "match setting `blacklist=True`"
            ),
            (
                CPRRule(modulus_11=True, ignore_irrelevant=False, examine_context=True,
                        blacklist=False, whitelist=["anders", "and"]),
                [ALL_MATCHES[i] for i in [0,1,2,3,4,5,6,19]],
                "match setting `whitelist=['anders', 'and']`"
            ),
        ]

        for rule, expected, description in rules:
            print(description)
            with self.subTest(rule):
                matches = rule.match(content)
                if expected:
                    self.assertCountEqual([match for match in matches],
                                          expected,
                                          "")
                else:
                    self.assertFalse(list(matches))
