"""Regression checks for source dates and explicit, empty-field-only backfills."""
import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1] / 'minmin-collect-create/scripts'
sys.path.insert(0, str(SCRIPTS))
import notehelper_client as client
import record_plan
from record_plan import topic_fields


class SourceMetadataTests(unittest.TestCase):
    def setUp(self):
        self.article = {'id': 'note-one', 'title': 'Source title',
                        'savedAt': '2026-10-30T12:00:00+08:00',
                        'publishedAt': '2026-10-24T17:45:30+08:00'}

    def test_official_published_date_survives_metadata_and_body_reads(self):
        node = dict(self.article, content='selected body')
        with patch.object(client, 'request', return_value={'edges': [{'node': node}]}):
            for content in (False, True):
                result = client.search('test', '', 1, 0, content, 'note-one')
                self.assertEqual(result['articles'][0].get('publishedAt'), self.article['publishedAt'])
                self.assertEqual('content' in result['articles'][0], content)

    def test_new_topic_uses_source_publication_instead_of_save_time(self):
        fields = topic_fields(self.article, 'doc')
        self.assertEqual(fields.get('发布时间'), self.article['publishedAt'])
        self.assertNotEqual(fields['发布时间'], self.article['savedAt'])
        self.assertNotIn('点赞', fields)

    def test_missing_or_invalid_date_never_falls_back_to_save_time(self):
        for value in (None, '', 'unknown', True, 123):
            with self.subTest(value=value):
                fields = topic_fields(dict(self.article, publishedAt=value), 'doc')
                self.assertNotIn('发布时间', fields)

    def test_verified_facts_keep_priority_and_zero_is_real_data(self):
        fields = topic_fields(self.article, 'doc', facts={'发布时间': '2026-10-23', '点赞': 0})
        self.assertEqual(fields['发布时间'], '2026-10-23')
        self.assertEqual(fields['点赞'], 0)

    def test_normal_repeated_pull_still_writes_nothing(self):
        self.assertEqual(topic_fields(self.article, 'doc', existing={'选题状态': ['已拍摄']}), {})

    def test_explicit_backfill_only_updates_missing_source_fields(self):
        existing = {'备注': 'NoteHelper ID:note-one', '发布时间': None, '点赞': 0,
                    '收藏': '', '评论': 7, '转发': [], '选题状态': ['已拍摄'],
                    '标题': 'Edited title', '笔记文档': 'existing-doc'}
        original = dict(existing)
        fields = topic_fields(self.article, 'other-doc',
                              facts={'点赞': 200, '收藏': 3, '评论': 100, '转发': 2},
                              existing=existing, fill_missing_source=True)
        self.assertEqual(fields, {'发布时间': self.article['publishedAt'], '收藏': 3, '转发': 2,
                                  '数据获取说明': '参考数据已获取。'})
        self.assertEqual(existing, original)

    def test_backfill_requires_a_matching_existing_source_id(self):
        for existing in (None, {}, {'备注': 'NoteHelper ID:note-one-other'}):
            with self.subTest(existing=existing), self.assertRaises(client.ClientError):
                topic_fields(self.article, 'doc', existing=existing, fill_missing_source=True)

    def test_cli_backfill_generates_a_patch_for_the_existing_record(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'article.json').write_text(json.dumps(self.article))
            (root / 'fields.json').write_text(json.dumps({'备注': 'NoteHelper ID:note-one',
                                                        '选题状态': ['已拍摄']}))
            args = ['record_plan', '--article', str(root / 'article.json'), '--doc-url', 'doc',
                    '--existing', str(root / 'fields.json'), '--fill-missing-source',
                    '--output', str(root / 'patch.json')]
            with patch.object(sys, 'argv', args), contextlib.redirect_stdout(io.StringIO()):
                record_plan.main()
            self.assertEqual(json.loads((root / 'patch.json').read_text()),
                             {'发布时间': self.article['publishedAt'],
                              '数据获取说明': '点赞、收藏、评论、转发：本条未获取到。'})

    def test_filled_source_date_is_preserved_even_if_cloud_changes(self):
        existing = {'备注': 'NoteHelper ID:note-one', '发布时间': '2026-10-20'}
        fields = topic_fields(self.article, 'doc', existing=existing, fill_missing_source=True)
        self.assertNotIn('发布时间', fields)
        self.assertEqual(fields, {'数据获取说明': '点赞、收藏、评论、转发：本条未获取到。'})


if __name__ == '__main__':
    unittest.main()
