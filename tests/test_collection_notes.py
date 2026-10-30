"""Customer-facing explanations must match the data actually present."""
import json
import sys
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / 'notebook-feishu-onboarding/scripts'
sys.path.insert(0, str(SCRIPTS))
from notehelper_client import ClientError
from record_plan import topic_fields


class CollectionNoteTests(unittest.TestCase):
    def setUp(self):
        self.article = {'id': 'source-one', 'title': 'Example',
                        'publishedAt': '2026-10-24T17:45:30+08:00'}

    def test_unknown_missing_metrics_have_an_explanation_and_no_fake_zero(self):
        fields = topic_fields(self.article, 'doc')
        self.assertEqual(fields.get('数据获取说明'), '点赞、收藏、评论、转发：本条未获取到。')
        for name in ['点赞', '收藏', '评论', '转发']:
            self.assertNotIn(name, fields)

    def test_only_confirmed_unsupported_fields_are_labelled_unsupported(self):
        fields = topic_fields(self.article, 'doc', facts={
            '点赞': 5, '未获取原因': {'收藏': '暂不支持自动获取', '评论': '暂不支持自动获取'}})
        self.assertEqual(fields.get('数据获取说明'),
                         '收藏、评论：暂不支持自动获取；转发：本条未获取到。')

    def test_retry_failure_is_distinct_from_unknown_and_unsupported(self):
        fields = topic_fields(self.article, 'doc', facts={
            '点赞': 0, '收藏': 2, '转发': 3, '未获取原因': {'评论': '获取失败，待重试'}})
        self.assertEqual(fields.get('数据获取说明'), '评论：获取失败，待重试。')
        self.assertEqual(fields['点赞'], 0)

    def test_missing_publication_date_is_explained(self):
        fields = topic_fields(dict(self.article, publishedAt=None), 'doc', facts={
            '点赞': 0, '收藏': 0, '评论': 0, '转发': 0})
        self.assertEqual(fields.get('数据获取说明'), '发布时间：本条未获取到。')

    def test_real_zero_values_count_as_obtained_data(self):
        facts = {name: 0 for name in ['点赞', '收藏', '评论', '转发']}
        fields = topic_fields(self.article, 'doc', facts=facts)
        self.assertEqual(fields.get('数据获取说明'), '参考数据已获取。')

    def test_backfill_explanation_uses_existing_values_and_refreshes_old_status(self):
        existing = {'备注': 'NoteHelper ID:source-one', '发布时间': '2026-10-20',
                    '点赞': 0, '收藏': 1, '评论': 2, '转发': None,
                    '数据获取说明': '转发：获取失败，待重试。', '选题状态': ['已拍摄']}
        original = dict(existing)
        fields = topic_fields(self.article, 'other-doc', facts={'转发': 3},
                              existing=existing, fill_missing_source=True)
        self.assertEqual(fields, {'转发': 3, '数据获取说明': '参考数据已获取。'})
        self.assertEqual(existing, original)

    def test_same_explanation_does_not_cause_redundant_updates(self):
        existing = {'备注': 'NoteHelper ID:source-one', '发布时间': self.article['publishedAt'],
                    '数据获取说明': '点赞、收藏、评论、转发：本条未获取到。'}
        fields = topic_fields(self.article, 'doc', existing=existing, fill_missing_source=True)
        self.assertEqual(fields, {})

    def test_invalid_reason_cannot_be_published_as_a_confirmed_status(self):
        for reason in ({'点赞': '平台永远没有数据'}, ['network-error']):
            with self.subTest(reason=reason), self.assertRaises(ClientError):
                topic_fields(self.article, 'doc', facts={'未获取原因': reason})

    def test_template_exposes_a_text_explanation_next_to_the_metrics(self):
        template = json.loads((SCRIPTS.parent / 'assets/feishu-template.json').read_text())
        table = template['tables']['选题池']
        fields = [field for field in table['fields'] if field['name'] == '数据获取说明']
        self.assertEqual(len(fields), 1)
        self.assertEqual(fields[0]['type'], 'text')
        visible = table['views'][0]['visible']['visible_fields']
        self.assertEqual(visible[visible.index('转发') + 1], '数据获取说明')


if __name__ == '__main__':
    unittest.main()
