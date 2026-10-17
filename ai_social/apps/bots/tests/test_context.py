from datetime import timedelta

from django.test import SimpleTestCase, TestCase
from django.utils import timezone

from apps.bots.services.context.context import format_age, render_situation
from apps.bots.tests.helpers import create_bot
from apps.feed.tests.helpers import (
    create_post,
    create_space,
    create_user,
    follow,
    like_post,
    set_created_at,
)

EXPECTED_SITUATION = '''\
World: Shonen Academy. Anime high school

What they did recently:
- 40m ago: liked a post by @mika_s
- 2h ago: posted "KENDO FINALS NEXT WEEK. NOBODY IS READY."

New notifications:
- @ren_t replied to their post: "you said that last year too"
- @yui_h followed them

Their timeline right now (newest first):
1. @ren_t: "beat my personal best at practice today"
2. @mika_s: "festival committee needs volunteers!! anyone??"
3. @daichi: "cafeteria curry is a war crime"

The post in question (marked with >>>):
@kenji: KENDO FINALS NEXT WEEK. NOBODY IS READY.
>>> @ren_t: you said that last year too'''


def minutes_ago(minutes, now):
    return now - timedelta(minutes=minutes)


class RenderSituationTests(TestCase):
    def setUp(self):
        self.now = timezone.now()
        self.bot = create_bot('kenji', last_action_at=minutes_ago(40, self.now))
        self.ren, self.mika, self.daichi, self.yui = (
            create_user(name) for name in ('ren_t', 'mika_s', 'daichi', 'yui_h')
        )
        self.space = create_space(self.ren, name='Shonen Academy', slug='shonen')
        self.space.description = 'Anime high school'
        self.space.save()

    def test_renders_full_situation(self):
        reply = self._build_scenario()
        self.assertEqual(render_situation(self.bot, reply, now=self.now), EXPECTED_SITUATION)

    def test_omits_world_and_shows_empty_sections_outside_space(self):
        post = create_post(self.ren, text='hi kenji')
        situation = render_situation(self.bot, post, now=self.now)
        self.assertNotIn('World:', situation)
        self.assertIn('What they did recently:\n- nothing yet', situation)
        self.assertIn('New notifications:\n- nothing new', situation)
        self.assertIn('Their timeline right now (newest first):\n- empty', situation)

    def _build_scenario(self):
        for user in (self.ren, self.mika, self.daichi):
            follow(self.bot.user, user)
        own = self._post(self.bot.user, 'KENDO FINALS NEXT WEEK. NOBODY IS READY.', 120)
        festival = self._post(self.mika, 'festival committee needs volunteers!! anyone??', 60)
        like_post(self.bot.user, festival, created_at=minutes_ago(40, self.now))
        self._post(self.daichi, 'cafeteria curry is a war crime', 180)
        self._post(self.ren, 'beat my personal best at practice today', 10)
        set_created_at(follow(self.yui, self.bot.user), minutes_ago(10, self.now))
        return create_post(self.ren, text='you said that last year too', parent=own,
                           space=self.space, created_at=minutes_ago(5, self.now))

    def _post(self, author, text, age_minutes):
        return create_post(author, text=text, space=self.space,
                           created_at=minutes_ago(age_minutes, self.now))


class FormatAgeTests(SimpleTestCase):
    def test_formats_by_largest_unit(self):
        now = timezone.now()
        cases = {0: 'just now', 40: '40m ago', 125: '2h ago', 60 * 24 * 3: '3d ago'}
        for minutes, expected in cases.items():
            with self.subTest(minutes=minutes):
                self.assertEqual(format_age(minutes_ago(minutes, now), now), expected)
