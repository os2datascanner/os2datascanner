import unittest

from os2datascanner.engine2.rules.cpr import CPRRule


content = """
@ Godtages fordi det er et valid cpr der opfylder Modulus 11 tjek.
Anders And 010180-0008
@ godtages fordi der indgår cpr i linjen
Anders And, cpr: [020280-0009
@ godtages fordi parenteser er balanceret
Anders And, [030380-0018], Paradisæblevej 111
@ godtages fordi der tillades ekstra ord ved parenteser.
Anders (040480-0019 And), Andeby
@ godtages ikke fordi foranstående ord er et tal, der IKKE opfylder kriterium for cpr
Anders And 113 050580-0001
@ godtages fordi bagvedstående/foranstående ord opfylder kriterium for cpr
Anders And 060680-0002 070680-0018

@ godtages ikke fordi foranstående ord er et mix af store og små bogstaver
  "HOST/ABCD.intra.corp"], "uSNChanged": [070780-0003],
  "uSNCreated": [123456], "userAccountControl":
@ godtages ikke pga. omkringstående tal OG fordi kun to ord medtages,
  vil paranteser være ubalanceret.
  712000 0 0 WET} {080880-0004 3600 1 WEST} [090880-0001 0 0 WET]
@ godtages ikke pga foranstående er unær operatør(dvs. fortegns-minus. På eng: unary)
  eller specialsymbol
16768 0 LMT} {090980-0005-} {+100980-0006} (#110980-0003)

Følgende kriterier undersøges
- Kontekst består af de `n_words=2` foranstående/bagvedstående ord incl. tegn.
Ord med bindesteg(-), punktum(.) eller skråstreg(/) splittes ikke.
- Konteksten bruges til at estimere en sandsynlighed for at et 10-cifret nummer
der opfylder modulus 11, rent faktisk er et cpr-nummber.

Følgende heuristik benyttes
- indgår p-nr eller variant deraf noget sted i teksten
- Er der unær operator før eller efter, fx -101080-0001 eller 111080-0009+
- Er der ubalanceret symboler eller parenteser omkring, fx [111180-0002.
  Men [121180-0018] vil være ok.
- Kommer der et tal der ikke ligner et cpr før eller efter, fx 113 121280-0003
- Er ord før eller efter ikke ’alle små’-, ’stort begyndelsesbogstav’ eller ’alle caps’,
  fx uSNChanged 131280-0019
resulterer alle i sandsynlighed=0.

- indeholder ord før cpr, fx Anders cpr-nr [141280-0008]
resulterer i  sandsynlighed=1

Følgende symboler undersøges
- unær operatører "+", "-"
- parenteser "(", "[", "{", "<", "<?", "<%", "/*"
- symboler "!", "#", "%"
"""


# all possible matches
ALL_MATCHES = [
    {'context': 'alid cpr der opfylder Modulus 11 tjek. Anders And XXXXXX-XXXX @ '
     'godtages fordi der indgår cpr i linjen Anders A',
     'context_offset': 0,
     'match': '0101XXXXXX',
     'offset': 79,
     'probability': 1.0,
     'sensitivity': None},
    {'context': 's fordi der indgår cpr i linjen Anders And, cpr: [XXXXXX-XXXX @ '
     'godtages fordi parenteser er balanceret Anders',
     'context_offset': 0,
     'match': '0202XXXXXX',
     'offset': 150,
     'probability': 1.0,
     'sensitivity': None},
    {'context': 'tages fordi parenteser er balanceret Anders And, [XXXXXX-XXXX], '
     'Paradisæblevej 111 @ godtages fordi der tillade',
     'context_offset': 0,
     'match': '0303XXXXXX',
     'offset': 217,
     'probability': 1.0,
     'sensitivity': None},
    {'context': 'i der tillades ekstra ord ved parenteser. Anders (XXXXXX-XXXX '
     'And), Andeby @ godtages ikke fordi foranstående o',
     'context_offset': 0,
     'match': '0404XXXXXX',
     'offset': 315,
     'probability': 1.0,
     'sensitivity': None},
    {'context': 'er IKKE opfylder kriterium for cpr Anders And 113 XXXXXX-XXXX @ '
     'godtages fordi bagvedstående/foranstående ord o',
     'context_offset': 0,
     'match': '0505XXXXXX',
     'offset': 441,
     'probability': 1.0,
     'sensitivity': None},
    {'context': 'stående ord opfylder kriterium for cpr Anders And XXXXXX-XXXX '
     'XXXXXX-XXXX @ godtages ikke fordi foranstående o',
     'context_offset': 0,
     'match': '0606XXXXXX',
     'offset': 539,
     'probability': 1.0,
     'sensitivity': None},
    {'context': 'opfylder kriterium for cpr Anders And XXXXXX-XXXX XXXXXX-XXXX @ '
     'godtages ikke fordi foranstående ord er et mix',
     'context_offset': 0,
     'match': '0706XXXXXX',
     'offset': 551,
     'probability': 1.0,
     'sensitivity': None},
    {'context': 'bogstaver "HOST/ABCD.intra.corp"], "uSNChanged": [XXXXXX-XXXX], '
     '"uSNCreated": [123456], "userAccountControl": @',
     'context_offset': 0,
     'match': '0707XXXXXX',
     'offset': 679,
     'probability': 1.0,
     'sensitivity': None},
    {'context': 'vil paranteser være ubalanceret. 712000 0 0 WET} {XXXXXX-XXXX '
     '3600 1 WEST} [XXXXXX-XXXX 0 0 WET] @ godtages ikk',
     'context_offset': 0,
     'match': '0808XXXXXX',
     'offset': 859,
     'probability': 1.0,
     'sensitivity': None},
    {'context': 'ceret. 712000 0 0 WET} {XXXXXX-XXXX 3600 1 WEST} [XXXXXX-XXXX 0 '
     '0 WET] @ godtages ikke pga foranstående er unær',
     'context_offset': 0,
     'match': '0908XXXXXX',
     'offset': 885,
     'probability': 1.0,
     'sensitivity': None},
    {'context': 'På eng: unary) eller specialsymbol 16768 0 LMT} {XXXXXX-XXXX-} '
     '{+XXXXXX-XXXX} (#XXXXXX-XXXX) Følgende kriteri',
     'context_offset': 0,
     'match': '0909XXXXXX',
     'offset': 1026,
     'probability': 1.0,
     'sensitivity': None},
    {'context': 'eller specialsymbol 16768 0 LMT} {XXXXXX-XXXX-} {+XXXXXX-XXXX} '
     '(#XXXXXX-XXXX) Følgende kriterier undersøges -',
     'context_offset': 0,
     'match': '1009XXXXXX',
     'offset': 1042,
     'probability': 1.0,
     'sensitivity': None},
    {'context': 'mbol 16768 0 LMT} {XXXXXX-XXXX-} {+XXXXXX-XXXX} (#XXXXXX-XXXX) '
     'Følgende kriterier undersøges - Kontekst består',
     'context_offset': 0,
     'match': '1109XXXXXX',
     'offset': 1057,
     'probability': 1.0,
     'sensitivity': None},
    {'context': 'ksten - Er der unær operator før eller efter, fx -XXXXXX-XXXX '
     'eller XXXXXX-XXXX+ - Er der ubalanceret symboler',
     'context_offset': 0,
     'match': '1010XXXXXX',
     'offset': 1512,
     'probability': 1.0,
     'sensitivity': None},
    {'context': 'r operator før eller efter, fx -XXXXXX-XXXX eller XXXXXX-XXXX+ - '
     'Er der ubalanceret symboler eller parenteser o',
     'context_offset': 0,
     'match': '1110XXXXXX',
     'offset': 1530,
     'probability': 1.0,
     'sensitivity': None},
    {'context': 'balanceret symboler eller parenteser omkring, fx [XXXXXX-XXXX. '
     'Men [XXXXXX-XXXX] vil være ok. - Kommer der et t',
     'context_offset': 0,
     'match': '1111XXXXXX',
     'offset': 1603,
     'probability': 1.0,
     'sensitivity': None},
    {'context': 'r eller parenteser omkring, fx [XXXXXX-XXXX. Men [XXXXXX-XXXX] '
     'vil være ok. - Kommer der et tal der ikke ligner',
     'context_offset': 0,
     'match': '1211XXXXXX',
     'offset': 1621,
     'probability': 1.0,
     'sensitivity': None},
    {'context': 'al der ikke ligner et cpr før eller efter, fx 113 XXXXXX-XXXX - '
     'Er ord før eller efter ikke ’alle små’-, ’stort',
     'context_offset': 0,
     'match': '1212XXXXXX',
     'offset': 1714,
     'probability': 1.0,
     'sensitivity': None},
    {'context': 'yndelsesbogstav’ eller ’alle caps’, fx uSNChanged XXXXXX-XXXX '
     'resulterer alle i sandsynlighed=0. - indeholder',
     'context_offset': 0,
     'match': '1312XXXXXX',
     'offset': 1829,
     'probability': 1.0,
     'sensitivity': None},
    {'context': 'd=0. - indeholder ord før cpr, fx Anders cpr-nr [XXXXXX-XXXX] '
     'resulterer i sandsynlighed=1 Følgende symboler',
     'context_offset': 0,
     'match': '1412XXXXXX',
     'offset': 1921,
     'probability': 1.0,
     'sensitivity': None}
]


class RuleTests(unittest.TestCase):
    def test_cpr_context(self):
        rules = [
            (
                CPRRule(modulus_11=True, ignore_irrelevant=False, examine_context=False,
                        blacklist=[]),
                ALL_MATCHES,
                "match all"
            ),
            (
                CPRRule(modulus_11=True, ignore_irrelevant=False, examine_context=True,
                        blacklist=[]),
                [ALL_MATCHES[i] for i in [0, 1, 2, 3, 5, 6, 19]],
                "match using context rules"
            ),
            (
                CPRRule(modulus_11=True, ignore_irrelevant=False, examine_context=True,
                        blacklist=[], whitelist=[]),
                [ALL_MATCHES[i] for i in [0, 2, 3, 5, 6, 19]],
                "match setting `whitelist=[]`"
            ),
            (
                CPRRule(modulus_11=True, ignore_irrelevant=False, examine_context=True),
                [ALL_MATCHES[i] for i in []],
                "match with blacklist"
            ),
            (
                CPRRule(modulus_11=True, ignore_irrelevant=False, examine_context=True,
                        blacklist=[], whitelist=["anders", "and"]),
                [ALL_MATCHES[i] for i in [0, 1, 2, 3, 4, 5, 6, 19]],
                "match setting `whitelist=['anders', 'and']`"
            ),
        ]

        for rule, expected, description in rules:
            print(f"testing {description}")
            with self.subTest(rule):
                matches = rule.match(content)
                if expected:
                    self.assertCountEqual([match for match in matches],
                                          expected,
                                          f"test of {description} failed")
                else:
                    self.assertFalse(list(matches))
