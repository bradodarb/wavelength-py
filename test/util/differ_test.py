
import unittest
from wavelength_py.util.dict_differ import DictDiffer


class TestDiffer(unittest.TestCase):

    def test_diff(self):
        differ = DictDiffer({'new_key1': 'new_value1', 'changed_key1':
                             'change_value', 'same_key1': 'same_value1'},
                            {'removed_key1': 'removed_value1', 'changed_key1':
                             'change_value1', 'same_key1': 'same_value1'})
        self.assertEqual(differ.added(), {'new_key1'})
        self.assertEqual(differ.changed(), {'changed_key1'})
        self.assertEqual(differ.removed(), {'removed_key1'})
        self.assertEqual(differ.unchanged(), {'same_key1'})


if __name__ == "__main__":
    unittest.main()
