from django.test import SimpleTestCase

from apps.feed.services.ranking import (
    AFFINITY_MULTIPLIER,
    compute_score,
    engagement_from_counts,
)


class EngagementTests(SimpleTestCase):
    def test_weights_likes_reposts_and_replies(self):
        self.assertEqual(engagement_from_counts(1, 0, 0), 1)
        self.assertEqual(engagement_from_counts(0, 1, 0), 2)
        self.assertEqual(engagement_from_counts(0, 0, 1), 1)
        self.assertEqual(engagement_from_counts(3, 2, 1), 8)

    def test_zero_engagement(self):
        self.assertEqual(engagement_from_counts(0, 0, 0), 0)


class ScoreTests(SimpleTestCase):
    def test_zero_engagement_is_zero(self):
        self.assertEqual(
            compute_score(0, age_hours_value=1, has_affinity=False),
            0,
        )
        self.assertEqual(
            compute_score(0, age_hours_value=1, has_affinity=True),
            0,
        )

    def test_older_posts_score_lower(self):
        recent = compute_score(10, age_hours_value=1, has_affinity=False)
        older = compute_score(10, age_hours_value=24, has_affinity=False)
        self.assertGreater(recent, older)

    def test_affinity_multiplies_score(self):
        base = compute_score(10, age_hours_value=1, has_affinity=False)
        boosted = compute_score(10, age_hours_value=1, has_affinity=True)
        self.assertAlmostEqual(boosted, base * AFFINITY_MULTIPLIER)

    def test_matches_time_decay_formula(self):
        engagement = 10
        age_hours_value = 2
        expected = engagement / ((age_hours_value + 2) ** 1.5)
        self.assertAlmostEqual(
            compute_score(engagement, age_hours_value, has_affinity=False),
            expected,
        )
