"""laloo sohbet botu widget'i. Calistir: python3 -m unittest discover -s tests -v"""
import os
import re
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
TAG = '<script src="https://mrspace.online/assets/site-chat.js" data-site="laloo"'


def read(p):
    with open(os.path.join(ROOT, p), encoding="utf-8") as f:
        return f.read()


class SiteChatWidget(unittest.TestCase):
    def test_static_pages_load_widget_once(self):
        for f in ["index.html", "business.html", "join/index.html", "rate/index.html", "stories/index.html"]:
            html = read(f)
            self.assertEqual(html.count("site-chat.js"), 1, f)
            self.assertIn(TAG, html, f)
            self.assertLess(html.index(TAG), html.rindex("</body>"), f)

    def test_private_pages_have_no_widget(self):
        for f in ["admin.html", "account.html"]:
            self.assertNotIn("site-chat", read(f), f)

    def test_map_page_keeps_button_above_mobile_sheet(self):
        self.assertIn('data-mobile-bottom="calc(34dvh + 12px)"', read("index.html"))

    def test_generated_city_and_story_pages_get_widget(self):
        import pages
        html = pages.page("en", "T", "D", "https://laloo.org/x/", [("en", "https://laloo.org/x/")], "<p>x</p>", lambda l: "x")
        self.assertEqual(html.count(TAG), 1)
        self.assertLess(html.index(TAG), html.rindex("</body>"))
        src = read("pages.py")
        self.assertEqual(src.count("{CHAT_JS}\n</body>"), 2, "sehir ve hikaye sablonlari")

    def test_about_template_has_widget(self):
        src = read("about_page.py")
        self.assertEqual(src.count(TAG), 1)
        self.assertLess(src.index(TAG), src.index("</body>"))

    def test_widget_does_not_break_service_worker_rules(self):
        sw = read("sw.js")
        # sw yalniz GET navigasyonu ve kendi kabugunu yonetir; capraz kaynakli script'e dokunmaz
        self.assertIn('if (r.method !== "GET") return;', sw)
        self.assertNotIn("mrspace.online", sw)

    def test_data_files_untouched_by_widget(self):
        self.assertTrue(os.path.exists(os.path.join(ROOT, "toilets.json")))
        self.assertIsNone(re.search(r"site-chat", read("toilets.json")[:2000]))


if __name__ == "__main__":
    unittest.main()
