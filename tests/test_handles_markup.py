import unittest

from socialkit import handles, markup


class HandleTests(unittest.TestCase):
    def test_normalize_strips_at_sign_and_case(self):
        self.assertEqual(handles.normalize("  @Marisol_V "), "marisol_v")
        self.assertEqual(handles.normalize(None), "")

    def test_validate_accepts_good_handles(self):
        for raw in ("abc", "@Tobias_K", "a" + "b" * 19):
            self.assertTrue(handles.is_valid(raw), raw)

    def test_validate_rejects_bad_handles(self):
        for raw in ("", "ab", "1abc", "has space", "a" * 21, "dash-ed", "admin", "@Root"):
            self.assertFalse(handles.is_valid(raw), raw)

    def test_validate_reports_reserved_names(self):
        with self.assertRaisesRegex(ValueError, "reserved"):
            handles.validate("support")

    def test_suggest_from_display_name(self):
        self.assertEqual(handles.suggest("Marisol Vega"), "marisol_vega")
        self.assertEqual(handles.suggest("  Zoë!! "), "zo_")

    def test_suggest_avoids_taken_and_reserved(self):
        self.assertEqual(handles.suggest("Tobias Kern", taken={"tobias_kern"}), "tobias_kern2")
        self.assertEqual(handles.suggest("Admin", taken={"admin2"}), "admin3")

    def test_suggest_handles_numeric_and_short_names(self):
        self.assertTrue(handles.suggest("42").startswith("user_"))
        self.assertTrue(handles.is_valid(handles.suggest("Al")))


class MarkupTests(unittest.TestCase):
    def test_mentions_are_unique_and_ordered(self):
        self.assertEqual(markup.mentions("@bob_x hi @amy_y and @bob_x again"), ["bob_x", "amy_y"])

    def test_mentions_ignore_emails_and_short_handles(self):
        self.assertEqual(markup.mentions("mail me at ann@example.invalid or @ab"), [])

    def test_hashtags_are_lower_cased_and_unique(self):
        self.assertEqual(markup.hashtags("#Lakeside day, #lakeside night #Run5k"), ["lakeside", "run5k"])

    def test_hashtags_ignore_numbers_and_entities(self):
        self.assertEqual(markup.hashtags("issue #42 and &#x27; quote"), [])

    def test_links(self):
        self.assertEqual(markup.links("see https://a.example/x and http://b.example"), ["https://a.example/x", "http://b.example"])

    def test_to_html_escapes_and_links(self):
        out = markup.to_html("<i>hi</i> @bob_x #Fun & more")
        self.assertEqual(
            out,
            '&lt;i&gt;hi&lt;/i&gt; <a class="mention" href="/profiles/bob_x/">@bob_x</a> '
            '<a class="hashtag" href="/feed/tags/fun/">#Fun</a> &amp; more',
        )

    def test_to_html_leaves_unknown_handles_plain_when_a_set_is_given(self):
        out = markup.to_html("@bob_x and @ghost_y", known_handles={"bob_x"})
        self.assertIn('href="/profiles/bob_x/"', out)
        self.assertNotIn("ghost_y/", out)
        self.assertTrue(out.endswith("@ghost_y"))
