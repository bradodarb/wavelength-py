import logging
import unittest

from wavelength_py.dal.pynamo_models.attributes.tag_attribute import (serialize_tag_str, serialize_tag_list, TagAttribute,
                                                                            serialize_tag)

logging.basicConfig()
log = logging.getLogger('logger')
log.setLevel(logging.DEBUG)


class TestAttributeTags(unittest.TestCase):

    def setUp(self):
        log.info("==================================================")
        log.info("======   Test: %s, SetUp", self.id())
        log.info("==================================================")

    def tearDown(self):
        log.info("--------------------------------------------------")
        log.info("------   Test: %s, TearDown", self.id())
        log.info("--------------------------------------------------")

    def test_serialize_tag(self):
        self.assertIsNone(serialize_tag({'test_dict': 123}))
        self.assertIsInstance(serialize_tag('testerino'), str)

        items = ['tag1', 'tag2', 'tag3']
        self.assertEqual(serialize_tag(items), '::tag1::tag2::tag3::')
        self.assertIsNone(serialize_tag([]))

    def test_serialize_tag_str(self):
        result = serialize_tag_str('tag-1')
        self.assertTrue(result, '::tag-1')

    def test_serialize_tag_list(self):
        result = serialize_tag_str('tag-1')
        self.assertTrue(result, '::tag-1')

    def test_TagAttribute_serialize_list(self):
        result = serialize_tag_list(['tag-1', 'tag-2', 'tag-3'])
        self.assertTrue(result, '::tag-1::tag-2::tag-3::')

    def test_TagAttribute_serialize_string(self):
        tag_attribute = TagAttribute()
        result = tag_attribute.serialize('tag-1')
        self.assertTrue(result, '::tag-1')

    def test_TagAttribute_serialize_returns_None_when_list_or_str_not_in_param(self):
        tag_attribute = TagAttribute()
        result = tag_attribute.serialize(True)
        self.assertEqual(result, None)

    def test_TagAttribute_deserialize_serialized_string(self):
        tag_attribute = TagAttribute()
        result = tag_attribute.deserialize('::tag-1::tag-2::tag-3::')
        self.assertTrue(result, ['tag-1', 'tag-2', 'tag-3'])

    def test_TagAttribute_deserialize_regular_string(self):
        tag_attribute = TagAttribute()
        result = tag_attribute.deserialize('tag-1')
        self.assertTrue(result, 'tag-1')

    def test_TagAttribute_deserialize_returns_empty_string(self):
        tag_attribute = TagAttribute()
        result = tag_attribute.deserialize('')
        self.assertEqual(result, '')


if __name__ == '__main__':
    unittest.main()
