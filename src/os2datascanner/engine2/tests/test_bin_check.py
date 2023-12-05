import unittest

from os2datascanner.engine2.rules.cpr import CPRRule

content = """
101080-0001 er personnummeret for [FORNAVN] [EFTERNAVN],
og bør opfanges af CPRRule med og uden bin_check
Nu følger der en masse cpr-lignende tal, med nogle rigtige nogen ind imellem.
Den med bin_check bør ignorere dem, siden de står mellem en masse andre tal,
og derfor nok er varenumre eller lignende.
660487-6475
291417-7763
011524-4939
398259-7919
    010180-0008
341672-1106
945807-3021
917400-2975
526018-1590
356230-1238
795422-0587
906790-3774
787789-3287
    070780-0003
748526-0574
442323-2218
198344-4174
308023-0025
577463-7064
864542-8410
217533-7727
081836-5849
241592-0661
266473-7828
230972-1513
410946-6852
692323-2124
603470-4049
    020280-0009
336980-2709
744311-4854
128923-2763
815994-1856
849093-4066
071620-2183
132437-0015
923478-8298
859030-6516
852524-6490
500410-8234
    060680-0002
919805-7817
661157-5092
346033-6904
798034-3254
653269-4846
104332-1819
042751-7979
688126-3403
467414-5017
160993-8298
516879-5486
852884-8362
    030380-0018
156158-8004
745375-1853
388233-8468
408756-0226
937878-5700
278477-6375
132412-4157
807848-6315
059903-8574
933303-7654
317024-0907
449243-7750
728354-5075
921374-5282
774471-6113
    040480-0019
719680-3432
644837-7878
146374-4817
116764-9679
781993-6745
012195-5867
147725-1293
589042-3413
192589-5492
418792-7491
981514-2351
796708-7515
576340-6344
    050580-0001
453331-4789
314460-2637
275923-3721
468655-8650
875886-7022
278422-4206
771260-0332
407085-3778
391533-7593
085018-4618
238145-8515
635208-0572
194251-2653
Her i enden af filen skrives der så endnu et cpr-nummer som bin_check finder,
fordi det står efter denne her blok tekst, og derfor står for langt væk fra den
lange liste af tal.
Denne test er lang, og dette er fordi, bin_check kun filtere noget væk for lang input.
For at se, at bin_check ikke fjerne korrekte positiver, se tests under test_cprrule.py
Personnummeret for [FORNAVN] [EFTERNAVN] er 111080-0009
"""  # noqa: E501


class RuleTests(unittest.TestCase):
    def test_cpr_bin_check(self):
        with_bin_check = CPRRule(modulus_11=True, examine_context=True)
        without_bin_check = CPRRule(modulus_11=True, examine_context=False)

        with_expected = ['1010XXXXXX', '1110XXXXXX']
        without_expected = ['1010XXXXXX', '0101XXXXXX', '0707XXXXXX', '0202XXXXXX', '0606XXXXXX',
                            '0303XXXXXX', '0404XXXXXX', '0505XXXXXX', '1110XXXXXX']

        with_actual = list(with_bin_check.match(content))
        without_actual = list(without_bin_check.match(content))

        self.assertEqual(len(with_actual), len(with_expected))
        for i, m in enumerate(with_actual):
            self.assertEqual(m["match"], with_expected[i])

        self.assertEqual(len(without_actual), len(without_expected))
        for i, m in enumerate(without_actual):
            self.assertEqual(m["match"], without_expected[i])
