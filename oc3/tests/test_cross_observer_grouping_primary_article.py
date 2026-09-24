import unittest
from oc3lib.cross_observer_grouping_primary_article_validation import validate_candidate,validate_manifest
class PrimaryArticleTests(unittest.TestCase):
 def test_exact_single_ads_article(self):
  c=validate_candidate(); r=validate_manifest()["resources"][0]; self.assertEqual(r["url"],"https://articles.adsabs.harvard.edu/pdf/2008ApJ...679..301B"); self.assertEqual(c["source_rows_read"],0)
if __name__=="__main__": unittest.main()
