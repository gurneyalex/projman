from logilab.common import testlib

from projman import format_monetary, extract_extension

class Test(testlib.TestCase):

    def test_format_monetary(self):
        self.assertRaises(TypeError, format_monetary, self)
        data = [(121212.01, u"121\xA0212,01"),
                (121000, u"121\xA0000,00"),
                ("121212.01", u"121\xA0212,01"),
                ("1000200.00", u"1\xA0000\xA0200,00"),
                (u"1200.00", u"1\xA0200,00"),
                (u"1200", u"1\xA0200,00"),
                (u"12", u"12,00"),
                (7.9999999999999991, u"8,00"),
                ]
        for input, expected in data:
            self.assertEqual(format_monetary(input), expected)

    def test_format(self):
        self.assertEqual(u"1\xA0200,0", format_monetary("1200.00", nb_decimal=1))
        self.assertEqual(u"1\xA0200,0", format_monetary(1200.00, nb_decimal=1))
        self.assertEqual(u"1\xA0200", format_monetary(u"1200.00", nb_decimal=0))
        self.assertEqual(u"1\xA0200", format_monetary(1200.00, nb_decimal=0))
        self.assertEqual(u"12", format_monetary(u"12", nb_decimal=0))
        self.assertEqual(u"1200,0", format_monetary("1200", nb_decimal=1, space_gap=0))
        self.assertEqual(u"1\xA02\xA00\xA00,00", format_monetary(u"1200", space_gap=1))

    def test_extract_extension(self):
        self.assertEqual(("foo", ""), extract_extension("foo"))
        self.assertEqual(("foo", "txt"), extract_extension("foo.txt"))
        self.assertEqual(("foo", "txt.old"), extract_extension("foo.txt.old"))

if __name__ == "__main__":
    testlib.unittest_main()
