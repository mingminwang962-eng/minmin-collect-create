#!/usr/bin/env python3
"""Produce the initial topic field map; never overwrite creative states on later pulls."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import sys

from notehelper_client import ClientError


INITIAL = {'选题状态': ['待研究'], 'route': ['待定']}
SOURCE_FIELDS = ('发布时间', '点赞', '收藏', '评论', '转发', '平台')
EXPLAINED_FIELDS = ('发布时间', '点赞', '收藏', '评论', '转发')
MISSING_STATUSES = ('暂不支持自动获取', '本条未获取到', '获取失败，待重试')


def is_empty(value):
    return value is None or value == '' or value == []


def data_note(values, facts):
    reasons = facts.get('未获取原因', {})
    if not isinstance(reasons, dict) or any(
            key not in EXPLAINED_FIELDS or status not in MISSING_STATUSES
            for key, status in reasons.items()):
        raise ClientError('未获取原因须按字段填写：暂不支持自动获取、本条未获取到或获取失败，待重试。')
    groups = {}
    for key in EXPLAINED_FIELDS:
        if is_empty(values.get(key)):
            status = reasons.get(key, '本条未获取到')
            groups.setdefault(status, []).append(key)
    return ('；'.join('、'.join(keys) + '：' + status for status, keys in groups.items())
            + '。') if groups else '参考数据已获取。'


def topic_fields(article, doc_url, facts=None, existing=None, fill_missing_source=False):
    facts = facts or {}
    if existing is not None and not fill_missing_source:
        # Repeated pulls never write creative fields, notes, rewrites, or versions.
        return {}
    if not article.get('id') or not article.get('title'):
        raise ClientError('缺少稳定来源 ID 或标题，不能创建索引。')
    source = {key: facts[key] for key in SOURCE_FIELDS if not is_empty(facts.get(key))}
    published = article.get('publishedAt')
    if '发布时间' not in source and isinstance(published, str) and published.strip():
        try:
            datetime.fromisoformat(published.replace('Z', '+00:00'))
        except ValueError:
            pass
        else:
            source['发布时间'] = published
    if fill_missing_source:
        marker = r'(?:^|\s)NoteHelper ID:' + re.escape(article['id']) + r'(?=\s|$)'
        if existing is None or not re.search(marker, str(existing.get('备注') or '')):
            raise ClientError('补全前须读取已有记录字段并核对相同 NoteHelper ID；未生成补丁。')
        fields = {key: value for key, value in source.items() if is_empty(existing.get(key))}
        explanation = data_note(dict(existing, **fields), facts)
        if explanation != existing.get('数据获取说明'):
            fields['数据获取说明'] = explanation
        return fields
    fields = dict(INITIAL, 标题=article['title'], 作者=article.get('author'),
                  原文链接=article.get('url'), 笔记文档=doc_url,
                  抓取时间=datetime.now(timezone.utc).isoformat(),
                  备注='NoteHelper ID:' + article['id'])
    fields.update(source)
    fields['数据获取说明'] = data_note(fields, facts)
    return fields


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--article', type=Path, required=True)
    p.add_argument('--doc-url', required=True)
    p.add_argument('--facts', type=Path)
    p.add_argument('--existing', type=Path, help='已读回的平铺 fields 对象，含备注中的来源 ID')
    p.add_argument('--fill-missing-source', action='store_true', help='仅为 --existing 的空来源字段生成补丁')
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    read = lambda path: json.loads(path.read_text(encoding='utf-8')) if path else None
    result = topic_fields(read(a.article), a.doc_url, read(a.facts), read(a.existing), a.fill_missing_source)
    with a.output.open('x', encoding='utf-8') as handle:
        json.dump(result, handle, ensure_ascii=False, indent=2)
    print(json.dumps({'ok': True, 'field_count': len(result), 'output': str(a.output)}, ensure_ascii=False))


if __name__ == '__main__':
    try: main()
    except (ClientError, OSError, ValueError) as exc:
        print(json.dumps({'ok': False, 'error': str(exc) if isinstance(exc, ClientError) else '索引文件操作失败。'}, ensure_ascii=False))
        sys.exit(1)
